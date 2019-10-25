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
Last Update: 2019/05/02
Description: Nagios plugin that checks results of Commissioning
             and Hardware Tests on MaaS

# Usage:
$ mjt_check_script_results machine [machine]

# Notes:
* Machines can be matched using system id, hostname, domain name or tags.
  See `utils.py:query_machines()` for details.

# Output:
OK == all machines are ok
WARNING == there are aborted, timed out, skipped, etc tests
CRITICAL == there are failed tests
"""

import argparse
from collections import defaultdict
import json

from maasjuju_toolkit.maas.script_results import get_script_results
from maasjuju_toolkit.util import print_nagios


def check_script_results(machines):
    """checks script results and print proper nagios output"""

    output = {
        'ok': [], 'warning': [], 'critical': []
    }

    # will exit with "UNKNOWN" on error
    results = get_script_results(machines, skip=set())
    total_suppressed = 0
    for hostname, host_results in results.items():
        count = defaultdict(lambda: 0)

        for res in host_results.values():
            count[res['status']] += 1
            total_suppressed += res['suppressed']

        # all ok
        if count['Passed'] == len(host_results):
            continue

        # some skipped
        which = 'critical' if count['Failed'] else 'warning'

        output[which].append('{} has {} tests'.format(
            hostname, json.dumps(count)))

    print_nagios(output)


def main():
    """parses arguments and call function"""

    parser = argparse.ArgumentParser(
        description='Nagios plugin that checks results of commissioning and '
                    'Hardware Tests results on MaaS'
    )
    parser.add_argument(
        'machines',
        type=str,
        nargs='+',
        help='MaaS machines to check'
    )

    args = parser.parse_args()
    check_script_results(args.machines)


if __name__ == '__main__':
    main()
