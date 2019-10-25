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
        exit_with_error(f'Could not GET machines: {e}')

    # Updates database info
    new_data = []
    for m in machines:
        try:
            system_id = m.get('system_id', 'UNKNOWN')
            m_power = powers[system_id]

            if is_virtual_machine(m_power):
                print(f'[{system_id}] [{m.get("hostname")}]'
                      f' [INFO] skipping, virtual machine')
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
            print(f'[{system_id}] [ERROR] Missing information: {e}')

    # Adds new data to the database
    print(f'Updating the database: "{Config.sqlite_db}"')
    MaaSCache.insert(new_data).on_conflict_replace().execute()
    db.commit()

    print('Done.')


def main():
    refresh_db()


if __name__ == '__main__':
    main()
