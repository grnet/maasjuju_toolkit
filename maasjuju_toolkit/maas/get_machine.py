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
        exit_with_error('[{}] [ERROR] {}'.format(system_id, e))

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
