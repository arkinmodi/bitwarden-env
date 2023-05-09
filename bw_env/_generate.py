from __future__ import annotations

import json
import subprocess

from bw_env._utils import BWENV_PREFIX


def generate(
        session: str,
        bw_name: list[str],
        filename: str = '.env',
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
        msg = (
            '"fields" property missing from Bitwarden CLI response. '
            f'Matched item with ID "{bw_id}" does not have any environment '
            f'variables configured. Run `bw get item {bw_id}` to view the '
            'Bitwarden CLI response.'
        )
        raise RuntimeError(msg)

    with open(filename, 'a') as f:
        for secret in bw_item['fields']:
            # format: bwenv://<uuid>/fields/<name>
            bwenv_str = f'{BWENV_PREFIX}{bw_id}/fields/{secret["name"]}'
            f.write(f'{secret["name"]}="{bwenv_str}"\n')

    print(f'Added environment variables to {filename}')
