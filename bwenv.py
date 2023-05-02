from __future__ import annotations

import argparse
import collections
import json
import os
import subprocess

from typing import NoReturn

BWENV_PREFIX = 'bwenv://'


def _parse_env_file(filename: str) -> dict[str, str]:
    # TODO: Parse ENV files
    # format: 'bwenv://<UUID>/fields/<name value>'
    ...


def _is_bw_unlocked(session: str) -> bool:
    bw_res = subprocess.run(
        ['bw', 'status', '--session', f'{session}'],
        capture_output=True
    )
    bw_status = json.loads(bw_res.stdout)
    return bw_status['status'] == 'unlocked'


def _run(session: str, cmd: list[str], filename: str = '.env') -> NoReturn:
    env_file = _parse_env_file(filename)

    # BW ID -> list of BW Fields
    bw_fields_by_bw_id: dict[str, set[str]] = collections.defaultdict(set)

    # (BW ID, BW Field) -> list of ENV Fields
    # it is possible that multiple ENV Fields have the same value
    bw_field_to_env_fields: dict[tuple[str, str],
                                 set[str]] = collections.defaultdict(set)

    for k, v in env_file.items():
        if v.startswith(BWENV_PREFIX):
            bw_id, bw_field = v[len(BWENV_PREFIX):].split('/fields/')
            bw_fields_by_bw_id[bw_id].add(bw_field)
            bw_field_to_env_fields[(bw_id, bw_field)].add(k)

    # (BW ID, BW Field) -> ENV Value
    bw_item_secrets: dict[tuple[str, str], str] = {}
    for id, fields in bw_fields_by_bw_id.items():
        bw_res = subprocess.run(
            ['bw', 'get', 'item', f'{id}', '--session', f'{session}'],
            capture_output=True,
        )
        bw_item = json.loads(bw_res.stdout)
        bw_item_fields_parsed = {
            secret['name']: secret['value']
            for secret in bw_item['fields']
        }

        for k, v in bw_item_fields_parsed.items():
            if k in fields:
                bw_item_secrets[(id, k)] = v

    new_env = os.environ.copy()
    for bw_key, env_fields in bw_field_to_env_fields.items():
        for field in env_fields:
            new_env[field] = bw_item_secrets[bw_key]

    os.execvpe(cmd[0], cmd, env=new_env)


def main() -> NoReturn:
    parser = argparse.ArgumentParser()
    parser.add_argument('command', nargs='*')
    parser.add_argument('--session', help='Bitwarden Session Token')
    parser.add_argument('-f', '--env-file', default='.env')
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
        msg = ('Invalid Bitwarden Session Token. Run `bw unlock` to generate'
               'a new session token.')
        raise RuntimeError(msg)

    _run(session, args.command, args.env_file)


if __name__ == '__main__':
    raise SystemExit(main())
