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
        exit_with_error(f'[INFO] No matching machines found.')

    # update machines, one by one
    for r in results:
        try:
            update = {}
            if new_cpus is not None:
                update['cpu_count'] = new_cpus

            if new_ram is not None:
                update['memory'] = new_ram * 1024

            session().Machine.update(system_id=r.system_id, **update)
            print(f'[{r.system_id}] [{r.hostname}]'
                  f' [OK] Updated hardware information: {update}')

        except MaaSError as e:
            exit_with_error(
                f'[{r.system_id}] [{r.hostname}] [ERROR] MaaS: {e}')

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
