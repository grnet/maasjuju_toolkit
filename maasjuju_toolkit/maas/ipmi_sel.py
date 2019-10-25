# Copyright (C) 2019  GRNET S.A.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
        exit_with_error('[INFO] No matching machines found.')

    # update machines, one by one
    for r in results:
        print('## [{}] [{}]'.format(r.system_id, r.hostname))

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
