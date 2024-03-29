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
Description: Refreshes local database of MaaS machines

# Usage:
$ mjt_refresh

# Notes:
* This process may take 2-3 minutes for big MaaS installations
"""

from maasjuju_toolkit.config import Config
from maasjuju_toolkit.util import (
    session, MaaSError, db, MaaSCache, exit_with_error)


def is_virtual_machine(power_parameters):
    address = power_parameters.get('power_address', None)

    return (address is None
            or any(x in address for x in ['virsh', 'ssh', 'qemu']))


def refresh_db():
    """gets data from server and update cache"""
    print('Getting information from MaaS.')

    # Retrieves list of machines
    try:
        s = session()
        machines = s.Machines.read()
        powers = s.Machines.power_parameters()

    except MaaSError as e:
        exit_with_error('Could not GET machines: {}'.format(e))

    # Updates database info
    new_data = []
    for m in machines:
        try:
            system_id = m.get('system_id', 'UNKNOWN')
            m_power = powers[system_id]

            if is_virtual_machine(m_power):
                print('[{}] [{}] [INFO] Skipping, virtual machine'.format(
                    system_id, m.get('hostname')))
                continue

            new_data.append(dict(
                power_address=m_power.get('power_address', ''),
                power_user=m_power.get('power_user', ''),
                power_pass=m_power.get('power_pass', ''),

                fqdn=m['fqdn'],
                domain=m['domain']['name'],
                hostname=m['hostname'],
                system_id=system_id,
                ip_addresses=', '.join(m['ip_addresses']),
                cpus=m['cpu_count'],
                ram=m['memory'] // 1024,
                tags=','.join(m['tag_names'])
            ))

        except KeyError as e:
            print('[{}] [ERROR] Missing information: {}'.format(system_id, e))

    # Adds new data to the database
    print('Updating the database: "{}"'.format(Config.sqlite_db))
    MaaSCache.insert(new_data).on_conflict_replace().execute()
    db.commit()

    print('Done.')


def main():
    refresh_db()


if __name__ == '__main__':
    main()
