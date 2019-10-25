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
