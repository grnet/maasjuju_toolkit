"""
Author: Aggelos Kolaitis <akolaitis@admin.grnet.gr>
Last Update: 2019/10/17
Description: Gets IPMI credentials of MaaS machine

# Usage:
$ mjt_get_ipmi_info [machine]

# Notes:
* Machines can be matched using system id, hostname, domain name or tags.
  See `utils.py:query_machines()` for details.
"""

import argparse
import json

from maasjuju_toolkit.util import query_machines


def get_ipmi_info(machines):
    """returns IPMI credentials for a list of machines"""
    return {
        row.fqdn: {
            'power_address': row.power_address,
            'power_pass': row.power_pass,
            'power_user': row.power_user,
            'system_id': row.system_id
        } for row in query_machines(machines)
    }


def main():
    """parses arguments and does work"""
    parser = argparse.ArgumentParser(
        description='[testing] Get power parameters of a maas machine'
    )
    parser.add_argument(
        'machines',
        type=str,
        nargs='+',
        help='Hostname, system id, domain, tags'
    )

    args = parser.parse_args()
    print(json.dumps(get_ipmi_info(args.machines), indent=4))


if __name__ == '__main__':
    main()
