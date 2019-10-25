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
Last Update: 2019/05/15
Description: Updates info for CPU cores and RAM of MaaS machines

# Usage:
$ mjt_update_hardware_info [machine] [machine]
                           [--new-cpus cpus] [--new-ram ram]

# Notes:
* Machines can be matched using system id, hostname, domain name or tags.
  See `utils.py:query_machines()` for details.
* CPUS is number of CPU cores
* RAM is available RAM (given in GB)
* You cannot update hardware info for Deployed or Locked machines.
"""

import argparse

from maasjuju_toolkit.util import (
    query_machines, exit_with_error, session, MaaSError)


def update_hardware_info(machine, new_cpus, new_ram):
    """updates cpus and ram of machines"""

    results = query_machines(machine)
    if not results:
        exit_with_error('[INFO] No matching machines found.')

    # update machines, one by one
    for r in results:
        try:
            update = {}
            if new_cpus is not None:
                update['cpu_count'] = new_cpus

            if new_ram is not None:
                update['memory'] = new_ram * 1024

            session().Machine.update(system_id=r.system_id, **update)
            print('[{}] [{}] [OK] Updated Hardware Info: {}'.format(
                r.system_id, r.hostname, update))

        except MaaSError as e:
            exit_with_error('[{}] [{}] [ERROR] MaaS: {}'.format(
                r.system_id, r.hostname, e))

    print('Done. Refresh machine list with "jmt_refresh".')


def main():
    """parses arguments and does work"""

    parser = argparse.ArgumentParser(
        description='Updates hardware information for many MaaS machines'
    )
    parser.add_argument(
        'machine',
        type=str,
        nargs='*',
        help='Hostname, system id, domain, tags'
    )
    parser.add_argument(
        '--new-cpus',
        type=int,
        required=False,
        default=None,
        help='New value for cpu cores'
    )
    parser.add_argument(
        '--new-ram',
        type=int,
        required=False,
        default=None,
        help='New value for machine RAM (in GB)'
    )

    args = parser.parse_args()
    update_hardware_info(args.machine, args.new_cpus, args.new_ram)


if __name__ == '__main__':
    main()
