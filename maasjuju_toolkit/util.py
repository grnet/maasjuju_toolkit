"""
Author: Aggelos Kolaitis <akolaitis@admin.grnet.gr>
Last Update: 2019/10/17
Description: Common utility functions for all scripts
"""

from datetime import datetime
import sys

import peewee
from maas.client.bones import SessionAPI, CallError, helpers

from maasjuju_toolkit.config import Config


##################################################################
# DATABASE

# SQLite database
db = peewee.SqliteDatabase(Config.sqlite_db)


class MaaSCache(peewee.Model):
    """machine and power info"""

    class Meta:
        database = db

    timestamp = peewee.DateTimeField(null=False, default=datetime.now)

    fqdn = peewee.CharField(max_length=100, null=False)
    system_id = peewee.CharField(unique=True, max_length=20, null=False)
    domain = peewee.CharField(max_length=30)
    hostname = peewee.CharField(max_length=20)

    ip_addresses = peewee.CharField(max_length=200)

    power_address = peewee.CharField(max_length=20, default='')
    power_user = peewee.CharField(max_length=20, default='')
    power_pass = peewee.CharField(max_length=20, default='')

    cpus = peewee.IntegerField()
    ram = peewee.IntegerField()
    tags = peewee.CharField(max_length=100)


# auto create table
MaaSCache.create_table()


##################################################################
# HELPER FUNCTIONS

def exit_with_error(msg, code=3):
    """quits with error"""
    print(msg)
    sys.exit(code)


def print_nagios(output):
    """prints results for nagios. @output must be a `{
        'ok': [list of ok message],
        'warning': [list of warning messages],
        'critical': [list of critical messages]
    }`"""

    if not output['warning'] and not output['critical']:
        print('OK')
        sys.exit(0)

    msgs = output['critical'] + output['warning']
    header, exitcode = 'WARNING:', 1
    if output['critical']:
        header, exitcode = 'CRITICAL:', 2

    print(header, ', '.join(msgs))
    sys.exit(exitcode)


# Collection of errors that may happen when using MaaS API
MaaSError = (CallError, helpers.RemoteError)


__session = None


def session():
    """opens a new session to the MaaS server. subsequent calls return the
    same session"""
    global __session
    if __session:
        return __session

    try:
        _, __session = SessionAPI.connect(
            Config.maas_api_url, apikey=Config.maas_api_key)

        return __session

    except MaaSError as e:
        exit_with_error('Could not connect to MaaS: {}'.format(e))


def query_machines(machine_filters):
    """selects a list of maas machines. @machine_filters can
    be a list of strings. All filters are ORed together.

    See examples in EXAMPLES.md"""
    rows = MaaSCache.select().order_by(MaaSCache.fqdn)

    if machine_filters:
        # search fqdn, system id

        filters = (MaaSCache.fqdn.in_(machine_filters)
                   | MaaSCache.system_id.in_(machine_filters)
                   | MaaSCache.ip_addresses.contains(machine_filters)
                   | MaaSCache.domain.in_(machine_filters)
                   | MaaSCache.hostname.in_(machine_filters))

        for name in machine_filters:
            sp = name.split(',')

            tag_filter = MaaSCache.tags.contains(sp[0])
            for tag in sp[1:]:
                tag_filter &= MaaSCache.tags.contains(tag)

            # search with tags. comma separated == AND
            filters |= tag_filter

            # search using regex in hostname
            filters |= MaaSCache.hostname % name

        rows = rows.where(filters)

    return rows
