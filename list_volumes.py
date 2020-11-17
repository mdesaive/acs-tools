#!/usr/bin/python3

""" List CloudStack Volumes. """

import sys
# import pprint
import argparse
import textwrap
from cs import CloudStack, read_config


def prepare_arguments():
    """ Parse commandline arguments."""

    parser = argparse.ArgumentParser(
        prog='list_volumes.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
        Create CSV list of all Volumes for a CloudStack intance.

        Autor: Melanie Desaive <m.desaive@mailbox.org>
        '''),
        epilog=textwrap.dedent('''\
        Examples:

        List all volumes in some project:
            ./list_volumes.py --project "Test von Melanie (Mauerpark)"

        List all isos in some storage:
            ./list_volumes.py --storage "Test von Melanie (Mauerpark)"

        List all volumes that are currently not attached to a VM
             ./list_volumes.py --only-detached

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
        '--storage',
        dest='storage',
        help='List only VMs on this storage.',
        required=False)
    parser.add_argument(
        '-o', '--outputfile',
        dest='name_outputfile',
        help='Write output to file.',
        required=False)
    parser.add_argument(
        '--only-detached',
        dest='only_detached',
        action='store_true',
        help='Write output to file.',
        required=False)
    args = parser.parse_args()

    return args


def collect_volumes(cloudstack, projectid=""):
    """ Collects all volumes for one project. """

    if projectid != "":
        volumes_container = cloudstack.listVolumes(
            listall=True,
            projectid=projectid)
    else:
        volumes_container = cloudstack.listVolumes(listall=True)

    if volumes_container != {}:
        volumes = volumes_container["volume"]
        for volume in volumes:
            for key in ["project", "projectid", "diskofferingname", "vmname"]:
                if key not in volume:
                    volume[key] = "n.a."
            if volume["domain"] == "ROOT":
                volume["domain"] = " ROOT"
    else:
        volumes = []

    return volumes


def filter_volumes(all_volumes, args):
    """ Filter set of volumes according to commandline parameters."""
    filtered_volumes = all_volumes.copy()

    if args.project:
        filtered_volumes = filter(
            lambda d: d["project"] == args.project, filtered_volumes)
    if args.storage:
        filtered_volumes = filter(
            lambda d: d["storage"] == args.storage, filtered_volumes)
    if args.only_detached:
        filtered_volumes = filter(
            lambda d: d["vmname"] == 'n.a.', filtered_volumes)

    return filtered_volumes


def print_volumes(filtered_volumes, outputfile):
    """ Printout list of volumes."""

    filtered_volumes = list(filtered_volumes)

    output_string = (
        'Domain;Project;VM Name;Cluster;Hypervisor;Storage;Name;' +
        'Size [GB];Diskoffering;Path\n')
    outputfile.write(output_string)

    for volumes in sorted(filtered_volumes, key=lambda i: (
            i["domain"],
            i["project"],
            i["name"])):
        output_string = (
            f'{volumes["domain"]};{volumes["project"]};'
            f'{volumes["vmname"]};{volumes["clustername"]};'
            f'{volumes["hypervisor"]};'
            f'{volumes["storage"]};{volumes["name"]};'
            f'{int(volumes["size"]/1024**3)};{volumes["diskofferingname"]};'
            f'{volumes["path"]}')
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

    all_volumes = collect_volumes(cloudstack)

    projects_container = cloudstack.listProjects(listall=True)
    projects = projects_container["project"]

    for project in sorted(projects, key=lambda key: key["name"]):
        project_id = project["id"]
        all_volumes = all_volumes + collect_volumes(
            cloudstack, project_id)

    # pprint.pprint(all_volumes)

    filtered_volumes = filter_volumes(all_volumes, args)

    print_volumes(filtered_volumes, outputfile)

    if args.name_outputfile is not None:
        outputfile.close()


if __name__ == "__main__":
    main()
