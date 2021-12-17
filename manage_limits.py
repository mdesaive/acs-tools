#!/usr/bin/python3

# pylint: disable=invalid-name
""" Manage Limits. """

import sys
import pprint
import argparse
import textwrap
from cs import CloudStack, read_config

limit_data_list = [
        {
            "id": 1,
            "type": 'user_vm',
            "key_limit": 'vmlimit',
            "key_avail": 'vmavailable'
        },
        {
            "id": 2,
            "type": 'public_ip',
            "key_limit": 'iplimit',
            "key_avail": 'ipavailable'
        },
        {
            "id": 3,
            "type": 'volume',
            "key_limit": 'volumelimit',
            "key_avail": 'volumeavailable'
        },
        {
            "id": 4,
            "type": 'snapshot',
            "key_limit": 'snapshotlimit',
            "key_avail": 'snapshotavailable'
        },
        # Project limits are not set in a project scope.
        # {
        #     "id": 5,
        #     "type": 'project',
        #     "key_limit": 'n.a.',
        #     "key_avail": 'n.a.'
        # },
        {
            "id": 6,
            "type": 'network',
            "key_limit": 'networklimit',
            "key_avail": 'networkavailable'
        },
        {
            "id": 7,
            "type": 'vpc',
            "key_limit": 'vpclimit',
            "key_avail": 'vpcavailable'
        },
        {
            "id": 8,
            "type": 'cpu',
            "key_limit": 'cpulimit',
            "key_avail": 'cpuavailable'
        },
        {
            "id": 9,
            "type": 'memory',
            "key_limit": 'memorylimit',
            "key_avail": 'memoryavailable'
        },
        {
            "id": 10,
            "type": 'primary_storage',
            "key_limit": 'primarystoragelimit',
            "key_avail": 'primarystorageavailable'
        },
        {
            "id": 11,
            "type": 'secondarystoragelimit',
            "key_limit": 'secondarystorageavailable',
            "key_avail": 'vmavailable'
        }
    ]


def prepare_arguments():
    """ Parse commandline arguments."""

    parser = argparse.ArgumentParser(
        prog='list_systemvms.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
        Create CSV list of all VMs for a CloudStack intance.

        Autor: Melanie Desaive <m.desaive@mailbox.org>
        '''),
        epilog=textwrap.dedent('''\
        Examples:

        List actual limits and manually change them
            ./manage_limits.py

        Manage limits for one project
            ./manage_limits.py --project "Test von Melanie (Mauerpark)"

        Disable limits for mentioned projects
            ./manage_limits.py --disable-limits

        Additional Infos:

        Uses the "CS" CloudStack API Client.
        See https://github.com/exoscale/cs.
        To install use "pip install cs".

        Requires configuration file ~/.cloudstack.ini.

        Todo:

        '''))

    parser.add_argument(
        '--disable-limits',
        dest='disable_limits',
        help='Disable limits.',
        action='store_true',
        required=False)
    parser.add_argument(
        '--force-disable',
        dest='force-disable',
        help='Disable limits without prompting for confirmation.',
        action='store_true',
        required=False)
    parser.add_argument(
        '-p', '--project_id',
        dest='project_id',
        help='List only VMs of this project.',
        required=False)
    parser.add_argument(
        '--print-csv',
        dest='print_csv',
        help='Print current configuration as CSV format (default is table).',
        action='store_true',
        required=False)
    parser.add_argument(
        '-o', '--outputfilie',
        dest='name_outputfile',
        help='Write output to file.',
        required=False)
    parser.add_argument(
        '-s', '--set-from-file',
        dest='set_from_filename',
        help='Set limits from inputfile.',
        required=False)
    args = parser.parse_args()

    return args


def manage_project_limits(project, print_csv, limit_matrix, outputfile):
    """ Handle limits for one project. """

    if limit_matrix != []:
        limit_matrix_filtered = list(
                filter(
                    lambda limit: limit["project_id"] == project["id"],
                    limit_matrix))
        pprint.pprint(limit_matrix_filtered)

    if print_csv:
        for limit_record in limit_data_list:
            if project[limit_record["key_limit"]] == "Unlimited":
                limit = -1
            else:
                limit = project[limit_record["key_limit"]]
            outputfile.write(
                f'{project["domain"]};{project["name"]};{project["id"]};' +
                f'{limit_record["id"]};{limit_record["type"]};' +
                f'{project[limit_record["key_avail"]]};{limit}\n')

    else:
        outputfile.write(
            f'\n\nLimits for domain: {project["domain"]} - ' +
            f'project: {project["name"]}.\n')

        outputfile.write(
                '-----------------------------------------------------------' +
                '----\n')
        outputfile.write(
                f'| {"ID":3} | {"Name":23} | {"Current":>12} | {"Max":>12} |' +
                '\n')
        outputfile.write(
                '-----------------------------------------------------------' +
                '----\n')
        for limit_record in limit_data_list:
            outputfile.write(
                f'| {limit_record["id"]:3} | {limit_record["type"]:23} | ' +
                f'{project[limit_record["key_avail"]]:>12} | ' +
                f'{project[limit_record["key_limit"]]:>12} |\n')
        outputfile.write(
                '-----------------------------------------------------------' +
                '----\n')


def main():
    """ main :) """
    args = prepare_arguments()

    if args.name_outputfile is not None:
        outputfile = open(args.name_outputfile, 'w')
    else:
        outputfile = sys.stdout

    # Reads ~/.cloudstack.ini
    cs = CloudStack(**read_config())

    # all_vms = collect_vms(cs, args.with_total_volumes)

    if args.print_csv:
        outputfile.write(
                'Domain;Project Name;Project UUID;Limit ID;Limit Name;' +
                'Current Utilisation;Limit\n')

    projects_container = cs.listProjects(listall=True)
    projects = projects_container["project"]

    if args.set_from_filename:
        tmp_limit_matrix = []
        input_file = open(args.set_from_filename)
        for line in input_file:
            line_list = line.split(";")
            tmp_limit_matrix.append(
                    {
                        "project_id": line_list[2],
                        "limit_type": line_list[3],
                        "limit_name": line_list[4],
                        "new_limit": line_list[6]
                    })
        limit_matrix = tmp_limit_matrix
    else:
        limit_matrix = []

    if args.project_id:
        projects_filtered = list(
                filter(
                    lambda project: project['id'] == args.project_id,
                    projects))
        if projects_filtered == []:
            print(
                    f'Project id \"{args.project_id}\" is not valid, ' +
                    'please choose a UUID from below:')
            for project in sorted(projects, key=lambda key: (
                    key["domain"],
                    key["name"])):
                print(
                    f'Domain: {project["domain"]}; ' +
                    f'Project Name: {project["name"]}; ' +
                    f'Project UUID: {project["id"]}')
    else:
        projects_filtered = projects

    for project in sorted(projects_filtered, key=lambda key: key["name"]):
        manage_project_limits(
                project,
                args.print_csv,
                limit_matrix,
                outputfile)


if __name__ == "__main__":
    main()
