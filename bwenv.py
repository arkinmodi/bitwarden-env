from __future__ import annotations

import argparse
import collections
import json
import os
import subprocess
import sys

from dotenv import dotenv_values
from typing import NamedTuple
from typing import NoReturn


if sys.platform == 'win32':
    def execvpe(_file: str, args: list[str], env: dict[str, str]) -> int:
        return subprocess.run(args, env=env)
else:
    from os import execvpe

BWENV_PREFIX = 'bwenv://'


class BW_Key(NamedTuple):
    id: str
    name: str


def _is_bw_unlocked(session: str) -> bool:
    bw_res = subprocess.run(
        ['bw', 'status', '--session', f'{session}'],
        capture_output=True
    )
    bw_status = json.loads(bw_res.stdout)
    return bw_status['status'] == 'unlocked'


def _run(session: str, cmd: list[str], filename: str = '.env') -> NoReturn:
    env_file = dotenv_values(filename)

    # BW ID -> list of BW Names
    bw_names_by_bw_id: dict[str, set[str]] = collections.defaultdict(set)

    # (BW ID, BW Name) -> list of ENV Fields
    # it is possible that multiple ENV Fields have the same value
    bw_key_to_env_fields: dict[BW_Key, set[str]] = collections.defaultdict(set)

    for k, v in env_file.items():
        if v and v.startswith(BWENV_PREFIX):
            bw_id, bw_name = v[len(BWENV_PREFIX):].split('/fields/')
            bw_names_by_bw_id[bw_id].add(bw_name)
            bw_key_to_env_fields[BW_Key(bw_id, bw_name)].add(k)

    # (BW ID, BW Name) -> ENV Value
    bw_item_secrets: dict[BW_Key, str] = {}
    for id, fields in bw_names_by_bw_id.items():
        bw_res = subprocess.run(
            ['bw', 'get', 'item', f'{id}', '--session', f'{session}'],
            capture_output=True,
        )

        if bw_res.stderr:
            raise RuntimeError(
                f'Bitwarden CLI Error -- {bw_res.stderr.decode()}')

        bw_item = json.loads(bw_res.stdout)
        bw_item_fields_parsed = {
            secret['name']: secret['value']
            for secret in bw_item['fields']
        }

        for k, v in bw_item_fields_parsed.items():
            if k in fields and v:
                bw_item_secrets[BW_Key(id, k)] = v

    new_env = os.environ.copy()
    for bw_key, env_fields in bw_key_to_env_fields.items():
        for field in env_fields:
            new_env[field] = bw_item_secrets[bw_key]

    execvpe(cmd[0], cmd, env=new_env)


def _generate(
        session: str,
        bw_name: list[str],
        filename: str = '.env'
) -> None:
    bw_res = subprocess.run(
        ['bw', 'get', 'item', '--session', f'{session}', *bw_name],
        capture_output=True,
    )

    if bw_res.stderr:
        raise RuntimeError(f'Bitwarden CLI Error -- {bw_res.stderr.decode()}')

    bw_item = json.loads(bw_res.stdout)
    bw_id = bw_item['id']

    if 'fields' not in bw_item:
        msg = ('"fields" property missing from Bitwarden CLI response. '
               f'Matched item with ID "{bw_id}" does not have any environment '
               f'variables configured. Run `bw get item {bw_id}` to view the '
               'Bitwarden CLI response.')
        raise RuntimeError(msg)

    with open(filename, 'a') as f:
        for secret in bw_item['fields']:
            # format: bwenv://<uuid>/fields/<name>
            bwenv_str = f'{BWENV_PREFIX}{bw_id}/fields/{secret["name"]}'
            f.write(f'{secret["name"]}="{bwenv_str}"\n')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', help='Bitwarden Session Token')
    subparser = parser.add_subparsers(dest='subparser_name')

    run_parser = subparser.add_parser('run')
    run_parser.add_argument(
        '-f',
        '--env-file',
        default='.env',
        help='Name of env file. Default: ".env"',
    )
    run_parser.add_argument(
        'command',
        nargs='+',
        help=('The CLI command to run with the environment variables injected '
              'into.'),
    )

    generate_parser = subparser.add_parser('generate')
    generate_parser.add_argument(
        '-f',
        '--env-file',
        default='.env',
        help='Name of env file. Default: ".env"'
    )
    generate_parser.add_argument(
        'name',
        nargs='+',
        help=('Bitwarden CLI search string. This can either be the Bitwarden '
              'ID or a fuzzy search for the Bitwarden Item Name. Run '
              "`bw get item <search string>` to view Bitwarden CLI's "
              'response.'),
    )

    args = parser.parse_args()

    if not args.session and 'BW_SESSION' not in os.environ:
        msg = ('No Bitwarden Session Token was provided. Run `bw unlock` '
               'and provide the generated session token via either the '
               '--session flag or the BW_SESSION environment variable.')
        raise RuntimeError(msg)
    elif args.session:
        session = args.session
    else:
        session = os.environ['BW_SESSION']

    if not _is_bw_unlocked(session):
        msg = ('Invalid Bitwarden Session Token. Run `bw unlock` to generate '
               'a new session token.')
        raise RuntimeError(msg)

    subparser_name = args.subparser_name
    if subparser_name == 'run':
        _run(session, args.command, args.env_file)
    elif subparser_name == 'generate':
        _generate(session, args.name, args.env_file)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
