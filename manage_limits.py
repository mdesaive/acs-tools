#!/usr/bin/python3

# pylint: disable=invalid-name
""" Manage Limits. """

import sys
# import pprint
import argparse
import textwrap
from cs import CloudStack, read_config

limit_data_list = [
        {
            "id": 0,
            "type": 'user_vm',
            "key_limit": 'vmlimit',
            "key_avail": 'vmavailable'
        },
        {
            "id": 1,
            "type": 'public_ip',
            "key_limit": 'iplimit',
            "key_avail": 'ipavailable'
        },
        {
            "id": 2,
            "type": 'volume',
            "key_limit": 'volumelimit',
            "key_avail": 'volumeavailable'
        },
        {
            "id": 3,
            "type": 'snapshot',
            "key_limit": 'snapshotlimit',
            "key_avail": 'snapshotavailable'
        },
        {
            "id": 4,
            "type": 'template',
            "key_limit": 'templatelimit',
            "key_avail": 'templateavailable'
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
            "type": 'secondary_storage',
            "key_limit": 'secondarystoragelimit',
            "key_avail": 'secondarystorageavailable'
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
        '--set-limits',
        dest='set_limits',
        help='Set limits.',
        action='store_true',
        required=False)
    parser.add_argument(
        '--print-limits',
        dest='print_limits',
        help='Print limits.',
        action='store_true',
        required=False)
    parser.add_argument(
        '--disable-limits',
        dest='disable_limits',
        help='Disable limits.',
        action='store_true',
        required=False)
    parser.add_argument(
        '--disable-list',
        dest='disable_list',
        help='Disable list.',
        required=False)
    parser.add_argument(
        '-p', '--project_id',
        dest='project_id',
        help='List only VMs of this project.',
        required=False)
    parser.add_argument(
        '-o', '--outputfile',
        dest='outputfile',
        help='Write output to file.',
        required=False)
    parser.add_argument(
        '-i', '--inputfile',
        dest='inputfile',
        help='Read limits from file.',
        required=False)
    args = parser.parse_args()

    return args


def print_limits(projects, name_outputfile):
    """ Print current limit to CSV format. """

    if name_outputfile is not None:
        outputfile = open(name_outputfile, 'w')
    else:
        outputfile = sys.stdout

    limit_string = 'Domain;Project Name;Project UUID;'
    for limit_record in limit_data_list:
        limit_string += f'{limit_record["type"]};'
    outputfile.write(limit_string + '\n')

    for project in sorted(projects, key=lambda key: (
            key["domain"],
            key["name"])):
        limit_string = (
                f'{project["domain"]};{project["name"]};{project["id"]};')
        for limit_record in limit_data_list:
            if project[limit_record["key_limit"]] == "Unlimited":
                limit = -1
            else:
                limit = project[limit_record["key_limit"]]
            limit_string += f'{limit};'
        outputfile.write(limit_string + '\n')


def prepare_limit_matrix(input_file_name):
    """ Prepare the datastructure with limits to set."""
    limit_matrix = []
    input_file = open(input_file_name)
    for line in input_file:
        line_list = line.split(";")
        limit_record = {
                    "domain": line_list[0],
                    "project": line_list[1],
                    "uuid": line_list[2],
                }
        i = 3
        for limit_data_record in sorted(
                limit_data_list, key=lambda key: key["id"]):
            limit_record[limit_data_record["key_limit"]] = line_list[i]
            i += 1
        limit_matrix.append(limit_record)
    return limit_matrix


def prepare_disable_matrix(projects, disable_string):
    """Prepares a list with IDs of limits to disable."""
    disable_list = []
    for i in disable_string.split(','):
        disable_list.append(int(i))

    disable_matrix = []
    for project in projects:
        limit_record = {
                    "domain": project["domain"],
                    "project": project["name"],
                    "uuid": project["id"],
                }
        i = 3
        for limit_data_record in sorted(
                limit_data_list, key=lambda key: key["id"]):
            if limit_data_record["id"] in disable_list:
                limit_record[limit_data_record["key_limit"]] = '-1'
            else:
                limit_record[limit_data_record["key_limit"]] = "No Change"
            i += 1
        disable_matrix.append(limit_record)
    return disable_matrix


def set_limits(cs, projects, limit_matrix):
    """ Handle limits for one project. """

    for project in sorted(projects, key=lambda key: (
            key["domain"],
            key["name"])):
        project_id = project["id"]
        if limit_matrix != []:
            limit_matrix_filtered = list(
                    filter(
                        lambda lim, pid=project_id: lim["uuid"] == pid,
                        limit_matrix))
            # pprint.pprint(limit_matrix_filtered)

        print(
            f'\nLimits for domain: {project["domain"]} - ' +
            f'project: {project["name"]}.')
        print(
                '-----------------------------------------------------------' +
                '-------------------------')
        print(
                f'| {"ID":3} | {"Name":23} | {"Capacity Left":>14} | ' +
                f'{"Old Max":>14} | {"New Max":>14} |')
        print(
                '-----------------------------------------------------------' +
                '-------------------------')
        for limit_record in limit_data_list:
            old_limit = project[limit_record["key_limit"]]
            if old_limit == 'Unlimited':
                old_limit = '-1'
            new_limit = limit_matrix_filtered[0][limit_record["key_limit"]]
            if old_limit == new_limit:
                new_limit = "No Change"
            print(
                f'| {limit_record["id"]:3} | {limit_record["type"]:23} | ' +
                f'{project[limit_record["key_avail"]]:>14} | ' +
                f'{old_limit:>14} | ' +
                f'{new_limit:>14} |')
        print(
                '-----------------------------------------------------------' +
                '-------------------------')

        # pprint.pprint(limit_data_list)
        for limit_record in limit_data_list:
            old_limit = project[limit_record["key_limit"]]
            if old_limit == 'Unlimited':
                old_limit = '-1'
            new_limit = limit_matrix_filtered[0][limit_record["key_limit"]]
            if new_limit not in (old_limit, 'No Change'):
                print(
                    f'OK to change {limit_record["key_limit"]} from ' +
                    f'\"{old_limit}\" to ' +
                    f'\"{new_limit}\"? (yes/no)')
                answer = None
                while answer not in ("yes", "no"):
                    answer = input("Enter yes or no: ")
                    if answer == "yes":
                        print('Do change!')
                        cs.updateResourceLimit(
                                projectid=project["id"],
                                resourcetype=limit_record["id"],
                                max=new_limit)
                    elif answer == "no":
                        print('Not changing this limit.')
                    else:
                        print("Please enter yes or no.")


def main():
    """ main :) """
    args = prepare_arguments()

    if args.set_limits and args.print_limits:
        print(
                'Please use only one of the options ' +
                '--print-limits --set-limits --disable-limits.')
        sys.exit(1)
    if not args.set_limits and not args.print_limits and \
            not args.disable_limits:
        print(
                'Please use one of the paramters ' +
                '--print-limits --set-limits or --disable-limits.')
        sys.exit(1)
    if args.disable_limits and not args.disable_list:
        print(
                'Please provide a list of limit types to disable.:\n' +
                'e.g --disable-list=\"1,2,4,7\"\n' +
                'Limit types are: \n' +
                '     0 - Instance. Number of instances a user can create.\n' +
                '     1 - IP. Number of public IP addresses.\n' +
                '     2 - Volume. Number of disk volumes.\n' +
                '     3 - Snapshot. Number of snapshots a user can create.\n' +
                '     4 - Template. Number of templates.\n' +
                '     6 - Network. Number of guest network.\n' +
                '     7 - VPC. Number of VPC a user can create.\n' +
                '     8 - CPU. Total number of CPU cores a user can use.\n' +
                '     9 - Memory. Total Memory (in MB) a user can use.\n' +
                '    10 - PrimaryStorage. Primary storage space (in GiB).\n' +
                '    11 - SecondaryStorage.')

    # Reads ~/.cloudstack.ini
    cs = CloudStack(**read_config())

    projects_container = cs.listProjects(listall=True)
    projects = projects_container["project"]
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
            sys.exit(1)
    else:
        projects_filtered = projects

    project = projects_filtered

    if args.print_limits:
        print_limits(projects_filtered, args.outputfile)
    if args.set_limits:
        limit_matrix = prepare_limit_matrix(args.inputfile)
        set_limits(cs, projects_filtered, limit_matrix)
    if args.disable_limits:
        limit_matrix = prepare_disable_matrix(
                projects_filtered,
                args.disable_list)
        set_limits(cs, projects_filtered, limit_matrix)


if __name__ == "__main__":
    main()
