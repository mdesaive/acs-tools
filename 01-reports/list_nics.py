#!/usr/bin/python3

# pylint: disable=invalid-name
""" List CloudStack NICs. """

import sys
# import pprint
import argparse
import textwrap
from cs import CloudStack, read_config


def prepare_arguments():
    """ Parse commandline arguments."""

    parser = argparse.ArgumentParser(
        prog='list_systemvms.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
        Create CSV list of all NICs for a CloudStack intance.

        Autor: Melanie Desaive <m.desaive@mailbox.org>
        '''),
        epilog=textwrap.dedent('''\
        Examples:

        List all NICs.
            ./list_nics.py

        List all NICs in some project:
            ./list_nics.py --project "Test von Melanie (Mauerpark)"

        List all NICs for one Network:
            ./list_nics.py --network "Internes Management-Netz"

        Additional Infos:

        Uses the "CS" CloudStack API Client.
        See https://github.com/exoscale/cs.
        To install use "pip install cs".

        Requires configuration file ~/.cloudstack.ini.

        Todo:

        '''))

    parser.add_argument(
        '-p', '--project',
        dest='project',
        help='List only VMs of this project.',
        required=False)
    parser.add_argument(
        '-n', '--network',
        dest='network',
        help='List only VMs of this network.',
        required=False)
    parser.add_argument(
        '-o', '--outputfile',
        dest='name_outputfile',
        help='Write output to file.',
        required=False)
    args = parser.parse_args()

    return args


def collect_nics(cs, projectid=""):
    """ Collects all VMs for one project. """

    project_nics = []
    if projectid != "":
        vms_container = cs.listVirtualMachines(
            listall=True,
            projectid=projectid)
    else:
        vms_container = cs.listVirtualMachines(listall=True)

    if vms_container != {}:
        vms = vms_container["virtualmachine"]
        for vm in vms:
            for key in [
                    "project",
                    "projectid",
                    "hostname"]:
                if key not in vm:
                    vm[key] = "n.a."
            for nic in vm["nic"]:
                nic["domain"] = vm["domain"]
                nic["project"] = vm["project"]
                nic["vmname"] = vm["name"]
                for key in ["ipaddress", ]:
                    if key not in nic:
                        nic[key] = "n.a."
                project_nics = project_nics + [nic, ]

    return project_nics


def filter_nics(all_nics, args):
    """ Filter set of NICs according to commandline parameters."""
    filtered_nics = all_nics.copy()
    if args.project is not None:
        filtered_nics = filter(
            lambda d: d["project"] == args.project, filtered_nics)
    if args.network is not None:
        filtered_nics = filter(
            lambda d: d["networkname"] == args.network, filtered_nics)

    return list(filtered_nics)


def print_nics(filtered_nics, outputfile):
    """ Printout list of VMs."""

    output_string = (
        'Domain;Project;VM Name;IP Address;MAC Address;Default;' +
        'Networkname')
    outputfile.write(f'{output_string}\n')

    for nic in sorted(filtered_nics, key=lambda i: (
            i["domain"],
            i["project"],
            i["vmname"],
            i["ipaddress"])):
        output_string = (
            f'{nic["domain"]};{nic["project"]};{nic["vmname"]};'
            f'{nic["ipaddress"]};'
            f'{nic["macaddress"]};{nic["isdefault"]};{nic["networkname"]}')
        outputfile.write(f'{output_string}\n')


def main():
    """ main :) """
    args = prepare_arguments()

    if args.name_outputfile is not None:
        outputfile = open(args.name_outputfile, 'w')
    else:
        outputfile = sys.stdout

    # Reads ~/.cloudstack.ini
    cs = CloudStack(**read_config())

    all_nics = collect_nics(cs)

    projects_container = cs.listProjects(listall=True)
    projects = projects_container["project"]

    for project in sorted(projects, key=lambda key: key["name"]):
        project_id = project["id"]
        all_nics = all_nics + collect_nics(
            cs, project_id)

    # pprint.pprint(all_nics)
    filtered_nics = filter_nics(all_nics, args)
    # pprint.pprint(filtered_nics)
    print_nics(filtered_nics, outputfile)

    if args.name_outputfile is not None:
        outputfile.close()


if __name__ == "__main__":
    main()
