#!/usr/bin/python3

""" List CloudStack SSH Keypairs. """

import sys
# import pprint
import argparse
import textwrap
from cs import CloudStack, read_config


def prepare_arguments():
    """ Parse commandline arguments."""

    parser = argparse.ArgumentParser(
        prog='list_sshkeypairs.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
        Create CSV list of all SSH Keypairs for a CloudStack intance.

        Autor: Melanie Desaive <m.desaive@mailbox.org>
        '''),
        epilog=textwrap.dedent('''\
        Examples:

        List all ssh keypairs in some project:
            ./list_sshkeypairs.py --project "Test von Melanie (Mauerpark)"

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
        '-o', '--outputfile',
        dest='name_outputfile',
        help='Write output to file.',
        required=False)
    args = parser.parse_args()

    return args


def collect_sshkeys(cloudstack, project="n.a."):
    """ Collects all keys for one project. """

    if project != "n.a.":
        sshkeys_container = cloudstack.listSSHKeyPairs(
            listall=True,
            projectid=project["id"])
        projectname = project["name"]
    else:
        sshkeys_container = cloudstack.listSSHKeyPairs(listall=True)
        projectname = "n.a."

    if sshkeys_container != {}:
        sshkeys = sshkeys_container["sshkeypair"]
        for sshkey in sshkeys:
            sshkey["project"] = projectname
            # for key in ["project", "projectid"]:
            #     if key not in sshkey:
            #         sshkey[key] = "n.a."
            if sshkey["domain"] == "ROOT":
                sshkey["domain"] = " ROOT"
    else:
        sshkeys = []

    return sshkeys


def filter_sshkeys(all_sshkeys, args):
    """ Filter set of ssh keypairs according to commandline parameters."""
    filtered_sshkeys = all_sshkeys.copy()

    # if args.only_public:
    #     filtered_sshkeys = filter(
    #         lambda d: d["ispublic"], filtered_sshkeys)
    # if args.only_featured:
    #     filtered_sshkeys = filter(
    #         lambda d: d["isfeatured"], filtered_sshkeys)
    if args.project:
        filtered_sshkeys = filter(
            lambda d: d["project"] == args.project, filtered_sshkeys)

    return filtered_sshkeys


def print_sshkeys(filtered_sshkeys, outputfile):
    """ Printout list of sshkeys."""

    filtered_sshkeys = list(filtered_sshkeys)

    output_string = (
        'Domain;Project;Name\n')
    outputfile.write(output_string)

    for sshkey in sorted(filtered_sshkeys, key=lambda i: (
            i["domain"],
            i["project"],
            i["name"])):
        output_string = (
            f'{sshkey["domain"]};{sshkey["project"]};'
            f'{sshkey["name"]}')
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

    all_sshkeys = collect_sshkeys(cloudstack)

    projects_container = cloudstack.listProjects(listall=True)
    projects = projects_container["project"]

    for project in sorted(projects, key=lambda key: key["name"]):
        all_sshkeys = all_sshkeys + collect_sshkeys(
            cloudstack, project)

    # pprint.pprint(all_sshkeys)

    filtered_sshkeys = filter_sshkeys(all_sshkeys, args)

    print_sshkeys(filtered_sshkeys, outputfile)

    if args.name_outputfile is not None:
        outputfile.close()


if __name__ == "__main__":
    main()
