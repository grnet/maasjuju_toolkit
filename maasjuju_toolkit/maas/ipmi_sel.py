"""
Author: Aggelos Kolaitis <akolaitis@admin.grnet.gr>
Last Update: 2019/05/05
Description: Manages IPMI System Event Log using machine info from MaaS

# Usage:
$ mjt_ipmi_sel list [machine] [[machine] ...]
$ mjt_ipmi_sel clear [machine] [[machine] ...]

# Notes:
* Machines can be matched using system id, hostname, domain name or tags.
  See `utils.py:query_machines()` for details.
* "clear" is a destructive operation
"""

import argparse
import subprocess

from maasjuju_toolkit.util import query_machines, exit_with_error


def ipmi_sel(cmd, machines):
    """lists or clear SEL of @machines"""

    results = query_machines(machines)
    if not results:
        exit_with_error(f'[INFO] No matching machines found.')

    # update machines, one by one
    for r in results:
        print(f'## [{r.system_id}] [{r.hostname}]')

        command_line = [
            'ipmi-sel', '-h', r.power_address,
            '-u', r.power_user, '-p', r.power_pass
        ]

        if cmd == 'clear':
            command_line.append('--clear')

        subprocess.run(command_line)


def main():
    """parses arguments and does work"""

    parser = argparse.ArgumentParser(
        description='Manage IPMI SEL of MaaS machines'
    )
    parser.add_argument(
        'command',
        choices=['list', 'clear'],
        help='Action'
    )
    parser.add_argument(
        'machines',
        type=str,
        nargs='*',
        help='Hostname, system id, domain, tags'
    )

    args = parser.parse_args()
    ipmi_sel(args.command, args.machines)


if __name__ == '__main__':
    main()
