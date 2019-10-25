"""
Author: Aggelos Kolaitis <akolaitis@admin.grnet.gr>
Last Update: 2019/10/17
Description: Lists and suppresses/deletes MaaS machine script results from
             Commissioning and Hardware Tests.

# Notes:
* Machines can be matched using system id, hostname, domain name or tags.
  See `utils.py:query_machines()` for details.

-----------------------------------------------------------------------

# Usage:

* Prints information for script results. If no <machine> is passed,
  the script will run for all known machines. (NOTE: this may take
  a very long time):

    $ mjt_script_results list [machine] [machine] [--no-installation]
        [--no-commission] [--no-tests] [--no-aborted] [--no-skipped]
        [--no-passed]

* Suppresses/deletes script results based on category/status. "Passed" scripts
  are always ignored. If no [machine] is given, the script will run for all
  known machines (NOTE: this may take a very long time).

    $ mjt_script_results suppress [machine] [--no-commission]
        [--no-tests] [--no-aborted] [--no-skipped]

    $ mjt_script_results unsuppress [machine] [--no-commission]
        [--no-tests] [--no-aborted] [--no-skipped]

    $ mjt_script_results delete [machine] [--no-commission]
        [--no-tests] [--no-aborted] [--no-skipped]

* Suppresses/deletes individual script ids for a machine.

    $ mjt_script_results suppress_id [machine] [--script-id script_id]
    $ mjt_script_results unsuppress_id [machine] [--script_id script_id]
    $ mjt_script_results delete_id [machine] [--script_id script_id]
"""

import argparse
import json

from maasjuju_toolkit.util import (
    exit_with_error, session, MaaSError, query_machines)

##################################################################


def get_script_results(machine, skip):
    """returns all script group results, along with result status"""

    if isinstance(machine, str):
        query = [machine]
    else:
        query = machine

    machines = query_machines(query)
    if not machines:
        exit_with_error(f'UNKNOWN: No matching machine: {machine}', code=3)

    api = session()

    results = {}
    for m in machines:
        scripts = api.NodeScriptResults.read(system_id=m.system_id)
        for s in scripts:
            if s['type_name'] in skip or s['status_name'] in skip:
                continue

            if m.system_id not in results:
                results[m.system_id] = {}

            suppressed = [r for r in s['results'] if r['suppressed']]
            ids = ','.join([str(r['id']) for r in s['results']])
            results[m.system_id].update({
                s['id']: {
                    'type': s['type_name'],
                    'status': s['status_name'],
                    'total': len(s['results']),
                    'suppressed': len(suppressed),
                    'individual_ids': ids
                }
            })

    return results


##################################################################


def set_suppressed(machines, skip, suppressed):
    """for a list of @machines, updates script results with
    status other than 'Passed' and sets the `suppressed`
    property to @suppressed"""

    # installation and passed script results are always ignored
    skip = skip | {'Passed'}

    # Status name changes to 'Passed' if all errors have been
    # suppressed. In order to "unsuppress", we need to look for
    # status "Passed" as well.
    if not suppressed:
        skip -= {'Passed'}

    all_results = get_script_results(machines, skip)

    for system_id, machine_results in all_results.items():
        for script_id in machine_results:
            set_suppressed_id(system_id, script_id, suppressed)


def set_suppressed_id(system_id, script_id, suppressed):
    """updates @script_id for @system_id and sets `suppressed`
    property to @suppressed. Prints a helpful error message
    if that failed."""

    try:
        session().NodeScriptResult.update(
            system_id=system_id, id=script_id, suppressed=suppressed
        )
        print(
            f'[{system_id}] Set suppressed={suppressed} for script {script_id}'
        )

    except MaaSError as e:
        print(
            f'[{system_id}] Failed to set suppressed={suppressed}'
            f'for script {script_id}: {e.__class__.__name__}: {e}'
        )


def delete_results(machines, skip):
    """for a list of @machines, deletes script results where
    status != 'Passed'"""

    # "installation" and "passed" results are always ignored
    skip = skip | {'Passed'}

    all_results = get_script_results(machines, skip)

    for system_id, machine_results in all_results.items():
        for script_id in machine_results:
            delete_result_id(system_id, script_id)


def delete_result_id(system_id, script_id):
    """deletes results of @script_id for @system_id"""

    try:
        session().NodeScriptResult.delete(
            system_id=system_id, id=script_id
        )
        print(f'[{system_id}] Deleted script {script_id}')

    except MaaSError as e:
        print(
            f'[{system_id}] Failed to delete script {script_id}: '
            f'{e.__class__.__name__}: {e}'
        )

##################################################################


def script_results(command, machine, script_id, skip):
    """calls appropriate command"""
    if command == 'list':
        print(json.dumps(get_script_results(machine, skip), indent=2))

    elif command in ['suppress', 'unsuppress']:
        set_suppressed(machine, skip, bool(command == 'suppress'))

    elif command in ['suppress_id', 'unsuppress_id']:
        if machine == '':
            exit_with_error('ERROR: No machine name')
        if script_id == '':
            exit_with_error('ERROR: No script id')

        set_suppressed_id(machine, script_id, bool(command == 'suppress_id'))

    elif command == 'delete':
        delete_results(machine, skip)

    elif command == 'delete_id':
        delete_result_id(machine, script_id)

    else:
        exit_with_error(f'Unknown command: {command}')


def main():
    """parses arguments and run proper command"""

    parser = argparse.ArgumentParser(
        description='Manage node script results. '
                    'See maasjuju_toolkit/maas/script_results.py for examples'
    )
    parser.add_argument(
        'command',
        choices=['list', 'suppress', 'delete', 'unsuppress',
                 'suppress_id', 'delete_id', 'unsuppress_id'],
        help='What to do'
    )
    parser.add_argument(
        'machines', type=str, default=[], nargs='*'
    )
    parser.add_argument(
        '--script-id', type=str
    )
    for x in ['Installation', 'Passed', 'Commissioning',
              'Testing', 'Skipped', 'Aborted']:
        parser.add_argument(
            f'--no-{x.lower()}',
            const=x,
            action='append_const',
            dest='skip',
            help=f'Ignore {x} script results'
        )

    # set skip categories, always skip running tests
    args = parser.parse_args()
    if args.skip is None:
        skip = {'Running'}
    else:
        skip = {'Running', *args.skip}

    # check if script id is required
    if args.command.endswith('_id') and args.script_id is None:
        exit_with_error('[ERROR] No script id passed')

    script_results(args.command, args.machines, args.script_id, skip)

##################################################################


if __name__ == '__main__':
    main()
