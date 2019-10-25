# MaaS Juju Toolkit

A collection of scripts for managing a MaaS/Juju installation.


## Introduction

### Why

The MaaS API is powerful and allows the user to perform any management
task via a simple cli. However, MaaS uses the obscure `system_id` of a
machine instead of its name. This makes it not-too-helpful to use as-is
for bigger MaaS installations, where retrieving the system id of a
single machine is a tedious task.

### How

A local SQLite3 database is created locally. Typically, the
`mjt_refresh` is run, contacts the MaaS server and stores "useful"
machine information (system id, hostname, FQDN, IP addresses, tags).
This means that we can then refer to machines using their proper
user-friendly names.

### What

The scripts perform a number of useful MaaS operations, as well as a
few other system management tasks (e.g. handling the system event logs
of machines using their IPMI interface).

Documentation for the available scripts can be found below, but the
source code contains a lot of helpful comments as well. All scripts are
prefixed with an `mjt_` prefix for clarity. Running
`<script_name> --help` is also useful.


## Setup

### Installation

```
$ sudo apt -y install python3 virtualenv python3-pip freeipmi-tools
$ virtualenv --python=python3.6 venv
$ source venv/bin/activate
$ pip install . -e
```

The scripts will be located at `venv/bin/`.

### Configuration

Edit the file `config.py` and configure MaaS credentials. Afterwards,
run `./venv/bin/mjt_refresh` to fetch data from the MaaS server.


## Scripts

### Selecting machines

As explained above, after running `mjt_refresh` you should be good to
go! Most of the scripts receive machine filters as arguments. You can
either specify a single machine (by system id, hostname, FQDN, or IP
address). You can also specify more than one, using domain name or a
list of MaaS tags. If more than one filter are given, then the results
are unified (logical OR).

The examples below use the script `mjt_get_ipmi_info`. The same logic
applies to all other scripts. As evident, the syntax is kept as simple
as possible.

```
# There is a MaaS machine with FQDN "mymachine.domain.name", hostname "mymachine",
# IP address 10.0.254.10 and system id "sys1d". You can use any of the following:

$ mjt_get_ipmi_info mymachine.domain.name
$ mjt_get_ipmi_info mymachine
$ mjt_get_ipmi_info domain.name
$ mjt_get_ipmi_info 10.0.254.10
$ mjt_get_ipmi_info sys1d
```

```
# Select all machines with tag "broken-nodes"

$ mjt_get_ipmi_info broken-nodes
```

```
# Select all machines that contain both the "broken-nodes" and the "started-repair" tags

$ mjt_get_ipmi_info "broken-nodes,started-repair"
```

```
# Select all machines under a specific domain

$ mjt_get_ipmi_info domain.name
```

```
# Select two machines

$ mjt_get_ipmi_info host1.domain.name host2.domain.name
```

### MaaS

1.  `mjt_refresh`

    **Description:**

    Refreshes local database

1.  `mjt_add_tags TAG MACHINE (MACHINE ...)`

    **Description:**

    Adds tag `TAG` to all matching machines. Will create the tag `TAG`
    if it does not already exist.

    **Example:**

    ```
    $ mjt_add_tags broken-nodes GRE4132
    ```

1.  `mjt_get_info MACHINE`

    **Description:**

    Retrieves machine information from the local database. Prints
    system id, IP addresses, tags, hostname, FQDN and IPMI information,
    in JSON format.

1.  `mjt_get_machine SYSTEM_ID`

    **Description:**

    Gets complete machine information from MaaS. This is the only
    script that accepts system ids, because it queries MaaS directly.

1.  `mjt_ipmi_sel [list/clear] MACHINE`

    **Description:**

    Lists or clears the IPMI system event log of a machine. Internally,
    it uses `ipmi-sel` and the IPMI credentials known to MaaS.

    **Example:**

    ```
    $ mjt_ipmi_sel list LAR0412
    $ mjt_ipmi_sel clear LAR0412
    ```

1.  `mjt_script_results [list/suppress/unsuppress/delete] MACHINE`

    **Description:**

    Lists (in JSON format), suppresses/unsuppresses or deletes the
    results of Commissioning and Hardware Tests scripts. See
    `mjt_script_results --help`, and
    [the source code](./maasjuju_toolkit/maas/script_results.py) for
    details.

    **Example:**

    ```
    mjt_script_results list 10.0.51.127
    mjt_script_results suppress 10.0.51.127
    ```

1.  `mjt_update_domain_name --new-domain new.domain.name MACHINE`

    **Description:**

    Updates the domain name of a machine.

    **Note:**

    This does not update the local database, you should run
    `mjt_refresh` afterwards to get new info from MaaS.

1.  `mjt_update_host_name --new-hostname newhostname MACHINE`

    **Description:**

    Updates the host name of a machine.

    **Note:**

    This does not update the local database, you should run
    `mjt_refresh` afterwards to get the new info from MaaS.

1.  `mjt_update_hardware_info [--new-cpus X] [--new-ram Y] MACHINE`

    **Description:**

    Updates number of cores and available RAM reported by MaaS. This
    does not work for Deployed/Locked machines.


### Juju

1.  `mjt_juju_nagios_deps --juju juju_status.json --pynag-hosts pynag-hosts.txt --pynag-services pynag-services.txt --outfile dependencies.cfg`

    **Description:**

    Generate Nagios host and service dependencies based on Juju status. Juju
    knows which hosts are containers, and what is the physical host on which
    they reside. We can use this information to create Nagios host and service
    dependencies. These are helpful in order to reduce noise when a physical
    host with many containers fails.

    If there are hosts with running containers that are not being monitored by
    Nagios, then this script will auto create these hosts as well, so that it
    can create the appropriate dependencies. In this case, the IP address that
    is used by Nagios is the one belonging in the subnet specified by the
    `--subnet` parameter.

    **Usage:**
    ```
    # get juju status
    $ juju status --format json > juju_status.json

    # on the Nagios server, retrieve Nagios hosts and services:
    $ pynag list address host_name WHERE object_type=host \
        '--seperator=|' --width=0 --quiet > pynag_hosts.txt
    $ pynag list host_name service_description WHERE object_type=service \
        '--seperator=|' --width=0 --quiet > pynag_services.txt

    # build dependencies. use the information retrieved above.
    # if any Juju hosts are missing from Nagios, they will be automatically
    # added. Nagios will use the host's IP address that belongs in the
    # 10.0.0.0/16 network.
    $ mjt_juju_nagios_deps --juju juju_status.json --subnet 10.0.0.0/16 \
        --pynag-hosts pynag_hosts.txt --pynag-services pynag_services.txt \
        --outfile dependencies.cfg

    # examine file
    $ less dependencies.cfg

    # install on Nagios server and restart Nagios
    $ sudo cp dependencies.cfg /etc/nagios3/conf.d/
    $ sudo systemctl restart nagios3
    ```

### Nagios

1.  `mjt_check_script_results MACHINE`

    Nagios/Icinga plugin that can be used to check that there are no
    failed Commissioning and/or hardware scripts.
