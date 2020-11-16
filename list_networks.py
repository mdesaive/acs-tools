#!/usr/bin/python3

""" List CloudStack networks. """

import sys
# import pprint
import argparse
import textwrap
from cs import CloudStack, read_config


def prepare_arguments():
    """ Parse commandline arguments."""

    parser = argparse.ArgumentParser(
        prog='list_networks.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
        Create CSV list of all networks for a CloudStack intance.

        Autor: Melanie Desaive <m.desaive@mailbox.org>
        '''),
        epilog=textwrap.dedent('''\
        Examples:

        List all networks in some project:
            ./list_networks.py --project "Test von Melanie (Mauerpark)"

        List only isolated networks:
            ./list_networks.py --only-isolated-nets

        List only shared networks:
            ./list_networks.py --only-shared-nets

        List only redundant networks:
            ./list_networks.py --only-redundant-vr

        List only not-redundant networks:
            ./list_networks.py --only-not-redundant-vr

        Additional Infos:

        Uses the "CS" CloudStack API Client.
        See https://github.com/exoscale/cs.
        To install use "pip install cs".

        Requires configuration file ~/.cloudstack.ini.

        Todo:

        '''))

    parser.add_argument(
        '--only-isolated-nets',
        dest='only_isolated_nets',
        help='List only isolated networks.',
        action='store_true',
        required=False)
    parser.add_argument(
        '--only-shared-nets',
        dest='only_shared_nets',
        help='List only shared nets.',
        action='store_true',
        required=False)
    parser.add_argument(
        '--only-redundant-vr',
        dest='only_redundant_vr',
        help='List only networks with redundant VR.',
        action='store_true',
        required=False)
    parser.add_argument(
        '--only-not-redundant-vr',
        dest='only_not_redundant_vr',
        help='List only networks with not redundant VR.',
        action='store_true',
        required=False)
    parser.add_argument(
        '-p', '--project',
        dest='project',
        help='List only VMs of this project.',
        required=False)
    parser.add_argument(
        '-o', '--outputfile',
        dest='name_outputfile',
        help='Write output to file.',
        required=False)
    args = parser.parse_args()

    return args


def collect_nets(cloudstack, projectid=""):
    """ Collects all networks for one project. """

    project_nets = []
    if projectid != "":
        nets_container = cloudstack.listNetworks(
            listall=True,
            projectid=projectid)
    else:
        nets_container = cloudstack.listNetworks(listall=True)

    if nets_container != {}:
        project_nets = nets_container["network"]
        for my_nets in project_nets:
            for key in ["project", "projectid", "vlan"]:
                if key not in my_nets:
                    my_nets[key] = "n.a."
            if my_nets["domain"] == "ROOT":
                my_nets["domain"] = " ROOT"

    return project_nets


def remove_duplicates(all_nets):
    """ Remove duplicate entries."""

    nets_condensed = []
    last_id = ''
    for loop_net in sorted(all_nets, key=lambda i: (
            i["id"])):
        if loop_net["id"] != last_id:
            nets_condensed = nets_condensed + [loop_net.copy(), ]
        last_id = loop_net["id"]

    return nets_condensed


def filter_nets(all_nets, args):
    """ Filter set of nets according to commandline parameters."""
    filtered_nets = all_nets.copy()

    if args.only_isolated_nets:
        filtered_nets = filter(
            lambda d: d["type"] == "Isolated", filtered_nets)
    if args.only_shared_nets:
        filtered_nets = filter(
            lambda d: d["type"] == "Shared", filtered_nets)
    if args.only_redundant_vr:
        filtered_nets = filter(
            lambda d: d["redundantrouter"], filtered_nets)
    if args.only_not_redundant_vr:
        filtered_nets = filter(
            lambda d: not d["redundantrouter"], filtered_nets)
    if args.project:
        filtered_nets = filter(
            lambda d: d["project"] == args.project, filtered_nets)
    # pprint.pprint(args.host)

    return filtered_nets


def print_nets(filtered_nets, outputfile):
    """ Printout list of nets."""

    filtered_nets = list(filtered_nets)

    output_string = (
        'Domain;Project;Name;Type;State;Restart Required;CIDR;' +
        'VLAN;Is Redundant')

    for nets in sorted(filtered_nets, key=lambda i: (
            i["domain"],
            i["project"],
            i["name"])):
        output_string = (
            f'{nets["domain"]};{nets["project"]};'
            f'{nets["name"]};{nets["type"]};'
            f'{nets["state"]};{nets["restartrequired"]};'
            f'{nets["cidr"]};{nets["vlan"]};{nets["redundantrouter"]}')
        outputfile.write(f'{output_string}\n')


def main():
    """ main :) """
    args = prepare_arguments()

    if args.name_outputfile is not None:
        outputfile = open(args.name_outputfile, 'w')
    else:
        outputfile = sys.stdout

    # Reads ~/.cloudstack.ini
    cloudstack = CloudStack(**read_config())

    all_nets = collect_nets(cloudstack)

    projects_container = cloudstack.listProjects(listall=True)
    projects = projects_container["project"]

    for project in sorted(projects, key=lambda key: key["name"]):
        project_id = project["id"]
        all_nets = all_nets + collect_nets(
            cloudstack, project_id)

    # pprint.pprint(all_nets)
    # filtered_nets = filter_nets(all_nets, args)
    condensed_nets = remove_duplicates(all_nets)
    filtered_nets = filter_nets(condensed_nets, args)

    print_nets(filtered_nets, outputfile)

    if args.name_outputfile is not None:
        outputfile.close()


if __name__ == "__main__":
    main()
