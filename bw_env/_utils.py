from __future__ import annotations

import json
import subprocess

BWENV_PREFIX = 'bwenv://'


def is_bw_unlocked(session: str) -> bool:
    bw_res = subprocess.run(
        ['bw', 'status', '--session', f'{session}'],
        capture_output=True,
    )
    bw_status = json.loads(bw_res.stdout)
    return bw_status['status'] == 'unlocked'
