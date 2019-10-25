"""
Author: Aggelos Kolaitis <akolaitis@admin.grnet.gr>
Last Update: 2019/05/02
Description: Updates domain names of MaaS machines

# Usage:
$ mjt_update_domain_name [machine] [machine] [--new-domain new.domain.name]

# Notes:
* Machines can be matched using system id, hostname, domain name or tags.
  See `utils.py:query_machines()` for details.
* Domain will be automatically created if needed.
"""

import argparse

from maasjuju_toolkit.util import (
    query_machines, exit_with_error, session, MaaSError)


def update_domain_name(machines, new_domain):
    """updates domain name of machines"""

    if not machines:
        exit_with_error('[ERROR] You did not specify any machines.')

    results = query_machines(machines)
    if not results:
        exit_with_error(f'[INFO] No matching machines found.')

    try:
        # create domain name if needed
        all_domains = session().Domains.read()
        names = [d['name'] for d in all_domains]

        if new_domain not in names:
            print(f'[INFO] Domain {new_domain} does not exist, creating...')
            session().Domains.create(name=new_domain, authoritative=True)

    except MaaSError as e:
        exit_with_error(f'[ERROR] MaaS: {e}')

    # update machines, one by one
    for r in results:
        try:
            session().Machine.update(system_id=r.system_id, domain=new_domain)
            print(f'[{r.system_id}] [{r.hostname}] [OK] Set to {new_domain}')

        except MaaSError as e:
            exit_with_error(
                f'[{r.system_id}] [{r.hostname}] [ERROR] MaaS: {e}')

    print('Done. Refresh machine list with "mjt_refresh".')


def main():
    """parses arguments and does work"""

    parser = argparse.ArgumentParser(
        description='Update domain name for many MaaS machines'
    )
    parser.add_argument(
        'machines',
        type=str,
        nargs='*',
        help='Hostname, system id, domain, tags'
    )
    parser.add_argument(
        '--new-domain',
        type=str,
        required=True,
        help='New domain name for machines (will be created if needed)'
    )

    args = parser.parse_args()
    update_domain_name(args.machines, args.new_domain)


if __name__ == '__main__':
    main()
