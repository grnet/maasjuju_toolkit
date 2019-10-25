"""
Author: Aggelos Kolaitis <akolaitis@admin.grnet.gr>
Last Update: 2019/05/09
Description: Adds tags to MaaS machines

# Usage:
$ mjt_add_tags [tag] [machine] [machine]

# Notes:
* Machines can be matched using system id, hostname, domain name or tags.
  See `utils.py:query_machines()` for details.
* New tags will be automatically created if needed.
"""

import argparse

from maasjuju_toolkit.util import (
    query_machines, exit_with_error, session, MaaSError)


def add_tags(new_tag, machines):
    """adds tags to machines"""

    if not machines:
        exit_with_error('[ERROR] You did not specify any machines.')

    results = query_machines(machines)
    if not results:
        exit_with_error(f'[INFO] No matching machines found.')

    try:
        # create tag name if needed
        all_tags = session().Tags.read()
        names = [t['name'] for t in all_tags]

        if new_tag not in names:
            print(f'[INFO] Tag {new_tag} does not exist, creating...')
            session().Tags.create(
                name=new_tag,
                description='Helper tag for nagios checks'
            )

    except MaaSError as e:
        exit_with_error(f'[ERROR] MaaS: {e}')

    # updates machines, one by one
    for r in results:
        try:
            session().Tag.update_nodes(name=new_tag, system_id=r.system_id)
            print(f'[{r.system_id}] [{r.hostname}] [OK] Added tag {new_tag}')

        except MaaSError as e:
            exit_with_error(
                f'[{r.system_id}] [{r.hostname}] [ERROR] MaaS: {e}')

    print('Done. Refresh machine list with "mjt_refresh".')


def main():
    """parses arguments and does work"""

    parser = argparse.ArgumentParser(
        description='Αdd tags to many MaaS machines'
    )
    parser.add_argument(
        'tag',
        type=str,
        help='Tag name (will be created if needed)'
    )
    parser.add_argument(
        'machines',
        type=str,
        nargs='+',
        help='Hostname, system id, domain, tags'
    )

    args = parser.parse_args()
    add_tags(args.tag, args.machines)


if __name__ == '__main__':
    main()
