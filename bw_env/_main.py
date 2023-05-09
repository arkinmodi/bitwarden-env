from __future__ import annotations

import argparse
import os

from bw_env._generate import generate
from bw_env._run import run
from bw_env._utils import is_bw_unlocked


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Securely use and share environment variables in your '
        'local development using Bitwarden!',
    )
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
        help=(
            'The CLI command to run with the environment variables injected '
            'into.'
        ),
    )

    generate_parser = subparser.add_parser('generate')
    generate_parser.add_argument(
        '-f',
        '--env-file',
        default='.env',
        help='Name of env file. Default: ".env"',
    )
    generate_parser.add_argument(
        'name',
        nargs='+',
        help=(
            'Bitwarden CLI search string. This can either be the Bitwarden '
            'ID or a fuzzy search for the Bitwarden Item Name. Run '
            "`bw get item <search string>` to view Bitwarden CLI's "
            'response.'
        ),
    )

    args = parser.parse_args()

    if not args.session and 'BW_SESSION' not in os.environ:
        msg = (
            'No Bitwarden Session Token was provided. Run `bw unlock` '
            'and provide the generated session token via either the '
            '--session flag or the BW_SESSION environment variable.'
        )
        raise RuntimeError(msg)
    elif args.session:
        session = args.session
    else:
        session = os.environ['BW_SESSION']

    if not is_bw_unlocked(session):
        msg = (
            'Invalid Bitwarden Session Token. Run `bw unlock` to generate '
            'a new session token.'
        )
        raise RuntimeError(msg)

    subparser_name = args.subparser_name
    if subparser_name == 'run':
        run(session, args.command, args.env_file)
    elif subparser_name == 'generate':
        generate(session, args.name, args.env_file)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
