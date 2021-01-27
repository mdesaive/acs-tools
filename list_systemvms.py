#!/usr/bin/python3

# pylint: disable=invalid-name
""" List CloudStack Configurations. """

import sys
# import pprint
import argparse
import textwrap
from cs import CloudStack, read_config

parser = argparse.ArgumentParser(
    prog='list_systemvms.py',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
    Create CSV list of all systemvms for a CloudStack intance.

    Autor: Melanie Desaive <m.desaive@mailbox.org>
    '''),
    epilog=textwrap.dedent('''\
    Examples:

    List all systemvms:
        python list_systemvms.py --only-virtual-routers

    List only VM-systemvms:
        python list_systemvms.py --only-secondary-storage-vms

    List only volume-systemvms:
        python list_systemvms.py --only-console-proxy-vms

    Send output to file:
        python list_systemvms.py -o some-outputfile.csv

    Additional Infos:

    Uses the "CS" CloudStack API Client. See https://github.com/exoscale/cs.
    To install use "pip install cs".

    Requires configuration file ~/.cloudstack.ini.

    Todo:

    '''))

parser.add_argument('--only-virtual-routers',
                    dest='only_virtual_routers',
                    help='List only virtual routers.',
                    action='store_true',
                    required=False)
parser.add_argument('--only-secondary-storage-vms',
                    dest='only_secondary_storage_vms',
                    help='List only secondary storage vms',
                    action='store_true',
                    required=False)
parser.add_argument('-o', '--outputfile',
                    dest='name_outputfile',
                    help='Write output to file.',
                    required=False)
args = parser.parse_args()


def collect_systemvms(projectid="", projectname=""):
    """ Collects all system VM for one project. """

    tmp_systemvms = []
    if projectid != "":
        systemvms_container = cs.listSystemVms(
            listall=True,
            projectid=projectid)
    else:
        systemvms_container = cs.listSystemVms(listall=True)

    if systemvms_container != {}:
        systemvms = systemvms_container["systemvm"]
        for my_systemvm in systemvms:
            # pprint.pprint(my_systemvm)
            tmp_systemvms = tmp_systemvms + [{
                "project": projectname,
                "type": my_systemvm["systemvmtype"],
                "ipaddress": my_systemvm["publicip"],
                "router_guestnetworkname": 'n.a',
                "router_isredundantrouter": 'n.a.',
                "router_redundantstate": 'n.a.',
                "state": my_systemvm["state"],
                "name": my_systemvm["name"],
                "hostname": my_systemvm["hostname"],
                "linklocalip": my_systemvm["linklocalip"]}, ]
    return tmp_systemvms


def collect_routers(projectid="", projectname=""):
    """ Collects all virtual routers for one project. """
    tmp_routers = []
    if projectid != "":
        routers_container = cs.listRouters(
            listall=True,
            projectid=projectid)
    else:
        routers_container = cs.listRouters(listall=True)

    if routers_container != {}:
        routers = routers_container["router"]
        for router in routers:
            # pprint.pprint(router)
            if router["state"] != "Running":
                router_hostname = "n.a."
                router_linklocalip = "n.a."
                router_guestnetworkname = "n.a."

            else:
                router_hostname = router["hostname"]
                router_linklocalip = router["linklocalip"]
                router_guestnetworkname = router["guestnetworkname"]
            tmp_routers = tmp_routers + [{
                "project": projectname,
                "type": "virtual router",
                "router_guestnetworkname": router_guestnetworkname,
                "state": router["state"],
                "name": router["name"],
                "hostname": router_hostname,
                "linklocalip": router_linklocalip,
                "ipaddress": router["nic"][0]["ipaddress"],
                "router_isredundantrouter": router["isredundantrouter"],
                "router_redundantstate": router["redundantstate"]}]
    return tmp_routers


if args.name_outputfile is not None:
    outputfile = open(args.name_outputfile, 'w')
else:
    outputfile = sys.stdout

# Reads ~/.cloudstack.ini
cs = CloudStack(**read_config())

all_systemvms = collect_routers()
all_systemvms = all_systemvms + collect_systemvms()

projects_container = cs.listProjects(listall=True)
projects = projects_container["project"]

for project in sorted(projects, key=lambda key: key["name"]):
    project_name = project["name"]
    project_id = project["id"]
    all_systemvms = all_systemvms + collect_routers(project_id, project_name)

# pprint.pprint(sorted(all_systemvms, key=lambda i: (
#         i["project"], i["name"])))

outputfile.write(
    'Projekt;System-VM Type;Networkname for VR;Is Redundant for Router;'
    'Redundant State of Router; State;Name;Hostname;'
    'Public IP;Linklocal IP\n')

for systemvm in sorted(all_systemvms, key=lambda i: (
        i["project"], i["type"], i["router_guestnetworkname"])):
    outputfile.write(
        f'{systemvm["project"]};{systemvm["type"]};'
        f'{systemvm["router_guestnetworkname"]};'
        f'{systemvm["router_isredundantrouter"]};'
        f'{systemvm["router_redundantstate"]};'
        f'{systemvm["state"]};'
        f'{systemvm["name"]};{systemvm["hostname"]};'
        # f'{systemvm["ipaddress"]};'
        f'{systemvm["linklocalip"]}\n')
if args.name_outputfile is not None:
    outputfile.close()
