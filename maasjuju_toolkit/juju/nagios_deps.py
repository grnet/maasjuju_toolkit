"""
Author: Aggelos Kolaitis <akolaitis@admin.grnet.gr>
Last Update: 2019/10/24
Description: Creates Nagios configuration for host dependencies based on
             dependencies derived from the Juju status output.
Requires: Juju, PyNag

# Usage (mind the beautiful typo on PyNag):
$ juju status --format json > juju_status.json
$ pynag list address host_name WHERE object_type=host \
    '--seperator=|' --width=0 --quiet > pynag_hosts.txt
$ pynag list host_name service_description WHERE object_type=service \
    '--seperator=|' --width=0 --quiet > pynag_services.txt

$ mjt_juju_nagios_deps [--juju juju_status.json] [--subnet CIDR] \
    [--services pynag_services.txt] [--hosts pynag_hosts.txt]

# Notes:
* `juju status` should run on the Juju controller machine
* `pynag` should run on the machine where Nagios is running
* The output is a Nagios configuration file. Add it under /etc/nagios3/conf.d
  and then restart Nagios.

# Output:
The output is a Nagios config file that describes Juju host and service
dependencies.

The logic is that containers depend on the physical machines on which they
reside. Furthermore, all the services of a container depend upon a well-known
service of the physical machine (by default: the SSH service), so as to avoid
mass notification messages in case a physical machine fails.

If any physical hosts listed under Juju are not present in Nagios, then they
are created as well. If there are multiple IP addresses, the one belonging in
the subnet CIDR is chosen.
"""

import argparse
import json
from collections import defaultdict

from netaddr import IPNetwork, IPAddress

from maasjuju_toolkit.util import exit_with_error

# Container services will depend on this service of the physical machine
WELL_KNOWN_SERVICE = 'SSH'

HOST_TEMPLATE = '''

##########################################################################

# {COMMENT}
define host {
    use                 generic-host
    host_name           {DISPLAY_NAME}
    address             {IP_ADDRESS}
    alias               {DISPLAY_NAME}
}

define service {
    check_command       check_ssh
    service_description SSH
    use                 generic-service
    host_name           {DISPLAY_NAME}
}

'''

HOST_DEPENDENCY_TEMPLATE = '''

##########################################################################

# {COMMENT}
define hostdependency {
        host_name                           {PARENT}
        dependent_host_name                 {CHILD}
        notification_failure_criteria       d,u
}

'''

SERVICE_DEPENDENCY_TEMPLATE = '''

# {COMMENT}
define servicedependency {
        host_name                               {PARENT_HOST}
        service_description                     {PARENT_SERVICE}
        dependent_host_name                     {DEPENDENT_HOST}
        dependent_service_description           {DEPENDENT_SERVICE}
        execution_failure_criteria              c,w,u
        notification_failure_criteria           c,w,u
}

'''


def get_juju_status(f_name):
    """parses Juju status JSON and returns as dict"""
    try:
        with open(f_name, 'r') as fin:
            return json.load(fin)

    except json.JSONDecodeError as e:
        exit_with_error('[EXCEPTION] Invalid input file: {}'.format(e))


def parse_pynag_hosts(f_name):
    """parses Nagios hosts. Returns them as a {'ip_address': 'host_name'}
    dict"""

    with open(f_name, 'r') as fin:
        pynag = fin.read()

    result = {}
    try:
        for line in pynag.split('\n'):
            if not line:
                continue

            address, hostname = line.split('|')
            result[address] = hostname

    except (TypeError, ValueError) as e:
        exit_with_error(
            '[EXCEPTION] Invalid Nagios hosts format: {}'.format(e))

    return result


def parse_pynag_services(f_name):
    """parses Nagios hosts. Returns them as a {'ip_address': 'host_name'}
    dict"""

    with open(f_name, 'r') as fin:
        pynag = fin.read()

    result = defaultdict(lambda: [])
    try:
        for line in pynag.split('\n'):
            if not line:
                continue

            hostname, service = line.split('|')
            result[hostname].append(service)

    except (TypeError, ValueError) as e:
        exit_with_error(
            '[EXCEPTION] Invalid Nagios hosts format: {}'.format(e))

    return result


def nagios_juju_deps(juju_status, pynag_hosts, pynag_services, subnet,
                     outfile):
    """generates Nagios host and service dependencies and writes to outfile"""
    hosts = parse_pynag_hosts(pynag_hosts)
    services = parse_pynag_services(pynag_services)
    juju = get_juju_status(juju_status)

    output = ''
    try:
        # p_address, p_host:  IP address and hostname of parent host
        # d_address, d_host:  IP address and hostname of dependent host

        for machine in juju['machines'].values():

            p_host = None
            for p_address in machine['ip-addresses']:
                p_host = hosts.get(p_address)
                if p_host is not None:
                    break

            if p_host is None:
                print('[WARN] [{}] Unknown Nagios host: ({})'.format(
                    machine['display-name'], machine['ip-addresses']))

                cons = machine.get('containers')
                if cons:
                    print(
                        '[WARN] [{}] Has {} containers. Will create'.format(
                            machine['display-name'], len(cons)))

                    ip_address = None
                    for ip in machine['ip-addresses']:
                        if IPAddress(ip_address) in IPNetwork(subnet):
                            ip_address = ip
                            print('Will use IP address', ip_address)
                            break

                    if not ip_address:
                        print('[WARN] [{}] No IPs in {}'.format(
                            machine['display-name'], subnet))
                        print('Choose which IP address to use:')

                        while ip_address not in machine['ip-addresses']:
                            ip_address = input('> ')

                    output += (
                        HOST_TEMPLATE
                        .replace('{COMMENT}',
                                 'Auto created by mjt_juju_nagios_deps')
                        .replace('{DISPLAY_NAME}', machine['display-name'])
                        .replace('{IP_ADDRESS}', ip_address)
                    )

                    p_host = machine['display-name']
                else:
                    print('[WARN] [{}] has no containers, skipping'.format(
                        machine['display-name']))

            if WELL_KNOWN_SERVICE not in services.get(p_host, []):
                print('[WARN] [{}] Service {} does not exist'.format(
                    p_host, WELL_KNOWN_SERVICE))

            try:
                containers = machine['containers']
            except KeyError:
                continue

            for name, container in containers.items():
                d_host = None
                for d_address in container['ip-addresses']:
                    d_host = hosts.get(d_address)
                    if d_host is not None:
                        break

                if d_host is None:
                    print('[WARN] [{}] Unknown Nagios host ({})'.format(
                        container['instance-id'], container['ip-addresses']))
                    continue

                # adds host dependencies
                output += (
                    HOST_DEPENDENCY_TEMPLATE
                    .replace('{COMMENT}', '({}) => ({})'.format(
                        container['instance-id'], machine['display-name']))
                    .replace('{PARENT}', p_host)
                    .replace('{CHILD}', d_host)
                )

                for service in services.get(d_host, []):
                    output += (
                        SERVICE_DEPENDENCY_TEMPLATE
                        .replace(
                            '{COMMENT}', '({}/{}) => ({}/{})'.format(
                                container['instance-id'], service,
                                machine['display-name'], WELL_KNOWN_SERVICE))
                        .replace('{PARENT_HOST}', p_host)
                        .replace('{PARENT_SERVICE}', WELL_KNOWN_SERVICE)
                        .replace('{DEPENDENT_HOST}', d_host)
                        .replace('{DEPENDENT_SERVICE}', service)
                    )

    except KeyError as e:
        exit_with_error(
            '[EXCEPTION] Invalid Juju status format: {}'.format(e))

    try:
        with open(outfile, 'w') as f_out:
            f_out.write(output)

        print('[SUCCESS] Configuration was written to', outfile)
    except OSError as e:
        print('[EXCEPTION] Writing to {} failed: {}'.format(outfile, e))


def main():
    """parses arguments and does work"""
    parser = argparse.ArgumentParser(
        description='Parses Juju status and generates dependencies'
                    ' for Nagios'
    )

    parser.add_argument(
        '--juju', type=str,
        help='Juju status (as json file)',
        required=True, default=None
    )
    parser.add_argument(
        '--pynag-hosts', type=str,
        help='file where PyNag has written list of Nagios hosts',
        required=True, default=None
    )
    parser.add_argument(
        '--pynag-services', type=str,
        help='file where PyNag has written list of Nagios services',
        required=True, default=None
    )
    parser.add_argument(
        '--outfile', type=str,
        help='file where configuration will be written',
        required=True, default=None
    )
    parser.add_argument(
        '--subnet', type=str,
        help='subnet to choose for new hosts with multiple IP addresses',
        required=False, default='0.0.0.0/0'
    )

    args = parser.parse_args()
    nagios_juju_deps(
        args.juju, args.pynag_hosts, args.pynag_services,
        args.subnet, args.outfile)


if __name__ == '__main__':
    main()
