#!/usr/bin/python3

# pylint: disable=invalid-name
""" List CloudStack Configurations. """

import sys
# import pprint
import argparse
import textwrap
from cs import CloudStack, read_config

PARSER = argparse.ArgumentParser(
    prog='list_configurations.py',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
    Create CSV list of all configuration settings for a CloudStack intance.

    Autor: Melanie Desaive <m.desaive@mailbox.org>
    '''),
    epilog=textwrap.dedent('''\
    Examples:

    Additional Infos:

    Uses the "CS" CloudStack API Client. See https://github.com/exoscale/cs.
    To install use "pip install cs".

    Requires configuration file ~/.cloudstack.ini.

    Todo:
       Add options to list configurations for:
           x account
           x cluster
           x storage

    '''))

PARSER.add_argument('-o', '--outputfile',
                    dest='name_outputfile',
                    help='Write output to file.',
                    required=False)

ARGS = PARSER.parse_args()


def print_global_confs():
    """API call list configurations."""
    configurations_container = cs.listConfigurations()

    if configurations_container != {}:
        configurations = configurations_container["configuration"]
        for configuration in sorted(
                configurations,
                key=lambda key: key["name"]):
            if "value" not in configuration:
                value = "n.a."
            else:
                value = configuration["value"]

            OUTPUTFILE.write(
                f'{configuration["name"]};{value}\n')


if ARGS.name_outputfile is not None:
    OUTPUTFILE = open(ARGS.name_outputfile, 'w')
else:
    OUTPUTFILE = sys.stdout

# Reads ~/.cloudstack.ini
cs = CloudStack(**read_config())

# projects_container = cs.listProjects(listall=True)
# projects = projects_container["project"]
#
# OUTPUTFILE.write(
#     'Projekt;System-VM Type;Networkname for VR;State;Name;Hostname;'
#     'Linklocal IP\n')
# for project in sorted(projects, key=lambda key: key["name"]):
#     project_name = project["name"]
#     project_id = project["id"]
#     print_routers(project_id, project_name)

print_global_confs()

if ARGS.name_outputfile is not None:
    OUTPUTFILE.close()
