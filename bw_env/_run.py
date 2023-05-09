from __future__ import annotations

import collections
import json
import os
import subprocess
import sys
from typing import NamedTuple
from typing import NoReturn

from dotenv import dotenv_values

from bw_env._utils import BWENV_PREFIX


if sys.platform == 'win32':
    def execvpe(_file: str, args: list[str], env: dict[str, str]) -> int:
        return subprocess.run(args, env=env)
else:
    from os import execvpe


class BW_Key(NamedTuple):
    id: str
    name: str


def run(session: str, cmd: list[str], filename: str = '.env') -> NoReturn:
    env_file = dotenv_values(filename)

    # BW ID -> list of BW Names
    bw_names_by_bw_id: dict[str, set[str]] = collections.defaultdict(set)

    # (BW ID, BW Name) -> list of ENV Fields
    # it is possible that multiple ENV Fields have the same value
    bw_key_to_env_fields: dict[BW_Key, set[str]] = collections.defaultdict(set)

    for k, v in env_file.items():
        if v and v.startswith(BWENV_PREFIX):
            secret_reference_split = v[len(BWENV_PREFIX):].split('/fields/')

            if (
                len(secret_reference_split) != 2 or
                not secret_reference_split[0] or
                secret_reference_split[0].isspace() or
                not secret_reference_split[1] or
                secret_reference_split[1].isspace()
            ):
                print(f'"{k}" has a malformed secret reference.')
                continue

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
                f'Bitwarden CLI Error -- {bw_res.stderr.decode()}',
            )

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
            if bw_key in bw_item_secrets:
                new_env[field] = bw_item_secrets[bw_key]
            else:
                print(
                    f'"{bw_key.name}" not found in item with ID "{bw_key.id}"',
                )

    execvpe(cmd[0], cmd, new_env)
