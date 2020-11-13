#!/usr/bin/python3

""" List CloudStack ISOs. """

import sys
# import pprint
import argparse
import textwrap
from cs import CloudStack, read_config


def prepare_arguments():
    """ Parse commandline arguments."""

    parser = argparse.ArgumentParser(
        prog='list_isos.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
        Create CSV list of all ISOs for a CloudStack intance.

        Autor: Melanie Desaive <m.desaive@mailbox.org>
        '''),
        epilog=textwrap.dedent('''\
        Examples:

        List all isos in some project:
            ./list_isos.py --project "Test von Melanie (Mauerpark)"

        List only isolated isos:
            ./list_isos.py --only-isolated-isos

        List only shared isos:
            ./list_isos.py --only-shared-isos

        List only redundant isos:
            ./list_isos.py --only-redundant-vr

        List only not-redundant isos:
            ./list_isos.py --only-not-redundant-vr

        Additional Infos:

        Uses the "CS" CloudStack API Client.
        See https://github.com/exoscale/cs.
        To install use "pip install cs".

        Requires configuration file ~/.cloudstack.ini.

        Todo:

        '''))

    parser.add_argument(
        '--only-public',
        dest='only_public',
        help='List only public isos.',
        action='store_true',
        required=False)
    parser.add_argument(
        '--only-featured',
        dest='only_featured',
        help='List only featured isos.',
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


def collect_isos(cloudstack, projectid=""):
    """ Collects all isos for one project. """

    project_isos = []
    if projectid != "":
        isos_container = cloudstack.listIsos(
            listall=True,
            projectid=projectid)
    else:
        isos_container = cloudstack.listIsos(listall=True)

    if isos_container != {}:
        project_isos = isos_container["iso"]
        for my_isos in project_isos:
            for key in ["project", "projectid"]:
                if key not in my_isos:
                    my_isos[key] = "n.a."
            if my_isos["domain"] == "ROOT":
                my_isos["domain"] = " ROOT"

    return project_isos


def remove_duplicates(all_isos):
    """ Remove duplicate entries."""

    isos_condensed = []
    last_id = ''
    for loop_iso in sorted(all_isos, key=lambda i: (
            i["id"])):
        if loop_iso["id"] != last_id:
            isos_condensed = isos_condensed + [loop_iso.copy(), ]
        last_id = loop_iso["id"]

    return isos_condensed


def filter_isos(all_isos, args):
    """ Filter set of isos according to commandline parameters."""
    filtered_isos = all_isos.copy()

    if args.only_public:
        filtered_isos = filter(
            lambda d: d["ispublic"], filtered_isos)
    if args.only_featured:
        filtered_isos = filter(
            lambda d: d["isfeatured"], filtered_isos)
    if args.project:
        filtered_isos = filter(
            lambda d: d["project"] == args.project, filtered_isos)

    return filtered_isos


def print_isos(filtered_isos, outputfile):
    """ Printout list of isos."""

    filtered_isos = list(filtered_isos)

    output_string = (
        'Domain;Project;Name;Displaytext;OS Type;Status;Size;' +
        'Bootable;Dynamically Scalable;Extractable;Featured;Public;Ready\n')
    outputfile.write(output_string)

    for isos in sorted(filtered_isos, key=lambda i: (
            i["domain"],
            i["project"],
            i["name"])):
        output_string = (
            f'{isos["domain"]};{isos["project"]};'
            f'{isos["name"]};{isos["displaytext"]};{isos["ostypename"]};'
            f'{isos["status"]};{isos["size"]};'
            f'{isos["bootable"]};{isos["isdynamicallyscalable"]};'
            f'{isos["isextractable"]};{isos["isfeatured"]};{isos["ispublic"]};'
            f'{isos["isready"]};')
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

    all_isos = collect_isos(cloudstack)

    projects_container = cloudstack.listProjects(listall=True)
    projects = projects_container["project"]

    for project in sorted(projects, key=lambda key: key["name"]):
        project_id = project["id"]
        all_isos = all_isos + collect_isos(
            cloudstack, project_id)

    # pprint.pprint(all_isos)

    condensed_isos = remove_duplicates(all_isos)
    filtered_isos = filter_isos(condensed_isos, args)

    print_isos(filtered_isos, outputfile)

    if args.name_outputfile is not None:
        outputfile.close()


if __name__ == "__main__":
    main()
