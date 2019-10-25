"""
Author: Aggelos Kolaitis <akolaitis@admin.grnet.gr>
Last Update: 2019/04/25
Description: Gets machine info directly from MaaS

# Usage:
$ mjt_get_machine [system_id]

# Notes
* This script talks directly to the MaaS API, ignoring the local db
"""

import json
import argparse

from maasjuju_toolkit.util import session, exit_with_error, MaaSError


def get_machine(system_id):
    """asks MaaS for information and print it out"""

    try:
        m = session().Machine.read(system_id=system_id)
    except MaaSError as e:
        exit_with_error(f'[{system_id}] [ERROR] {e}')

    print(json.dumps({
        'system_id': system_id,
        'ip_addresses': ','.join(m['ip_addresses']),
        'tags': ','.join(m['tag_names']),
        'hostname': m['hostname'],
        'domain': m['domain']['name'],
        'fqdn': m['fqdn'],
        'status': m['status_name']
    }, indent=2))


def main():
    """calls get_machine()"""
    parser = argparse.ArgumentParser(
        description='Get machine details directly from MaaS'
    )
    parser.add_argument(
        'system_id',
        type=str,
    )

    args = parser.parse_args()
    get_machine(args.system_id)


if __name__ == '__main__':
    main()
