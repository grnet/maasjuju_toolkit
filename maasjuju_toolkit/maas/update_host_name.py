"""
Author: Aggelos Kolaitis <akolaitis@admin.grnet.gr>
Last Update: 2019/10/17
Description: Updates hostname of a MaaS machine

# Usage:
$ mjt_update_host_name [machine] [--new-hostname new_name]

# Notes:
* Machines can be matched using system id, hostname, domain name or tags.
  See `utils.py:query_machines()` for details. If multiple machines match
  the query, only one of them will be changed.
"""

import argparse

from maasjuju_toolkit.util import (
    query_machines, exit_with_error, session, MaaSError)


def update_host_name(machine, new_hostname):
    """updates host name of machine"""

    results = query_machines([machine])
    if not results:
        exit_with_error(f'[INFO] No matching machines found.')

    # update machines, one by one
    r = results[0]
    try:
        session().Machine.update(system_id=r.system_id, hostname=new_hostname)
        print(f'[{r.system_id}] [{r.hostname}] [OK]'
              f' Updated hostname to {new_hostname}')

    except MaaSError as e:
        exit_with_error(f'[{r.system_id}] [{r.hostname}] [ERROR] MaaS: {e}')

    print('Done. Refresh machine list with "mjt_refresh".')


def main():
    """parses arguments and does work"""

    parser = argparse.ArgumentParser(
        description='Update domain name for many MaaS machines'
    )
    parser.add_argument(
        'machine',
        type=str,
        help='Hostname, system id, domain, tags'
    )
    parser.add_argument(
        '--new-hostname',
        type=str,
        required=True,
        help='New hostname name for machine'
    )

    args = parser.parse_args()
    update_host_name(args.machine, args.new_hostname)


if __name__ == '__main__':
    main()
