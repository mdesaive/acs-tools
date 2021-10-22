#!/usr/bin/python3

# pylint: disable=invalid-name
""" Create a Report about VM Utilization. """

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
        Create CSV list of all VMs for a CloudStack intance.

        Autor: Melanie Desaive <m.desaive@mailbox.org>
        '''),
        epilog=textwrap.dedent('''\
        Examples:

        List all VMs running on host acs-compute-7 with used storage space.
            ./report_performance_vm.py

        Additional Infos:

        Uses the "CS" CloudStack API Client.
        See https://github.com/exoscale/cs.
        To install use "pip install cs".

        Requires configuration file ~/.cloudstack.ini.

        Todo:

        '''))

    parser.add_argument(
        '--only-running-vms',
        dest='only_running_vms',
        help='List only running VMs.',
        action='store_true',
        required=False)
    parser.add_argument(
        '--only-stopped-vms',
        dest='only_stopped_vms',
        help='List only stopped VMs.',
        action='store_true',
        required=False)
    parser.add_argument(
        '-p', '--project',
        dest='project',
        help='List only VMs of this project.',
        required=False)
    parser.add_argument(
        '--host',
        dest='host',
        help='List only VMs running on this host.',
        required=False)
    parser.add_argument(
        '-o', '--outputfile',
        dest='name_outputfile',
        help='Write output to file.',
        required=False)
    args = parser.parse_args()

    return args


def collect_vms(cs, projectid=""):
    """ Collects all VMs for one project. """

    project_vms = []
    if projectid != "":
        vms_container = cs.listVirtualMachines(
            listall=True,
            projectid=projectid)
    else:
        vms_container = cs.listVirtualMachines(listall=True)

    if vms_container != {}:
        project_vms = vms_container["virtualmachine"]
        for my_vm in project_vms:
            for key in [
                    "project",
                    "projectid",
                    "hostname",
                    ]:
                if key not in my_vm:
                    my_vm[key] = "n.a."
            for key in [
                    "diskioread",
                    "diskiowrite",
                    "diskkbsread",
                    "diskkbswrite"
                    ]:
                if key not in my_vm:
                    my_vm[key] = 0

    return project_vms


def filter_vms(all_vms, args):
    """ Filter set of VMs according to commandline parameters."""
    filtered_vms = all_vms.copy()
    if args.only_running_vms:
        filtered_vms = filter(lambda d: d["state"] == "Running", filtered_vms)
    if args.only_stopped_vms:
        filtered_vms = filter(lambda d: d["state"] == "Stopped", filtered_vms)
    # pprint.pprint(args.host)
    if args.host is not None:
        filtered_vms = filter(
            lambda d: d["hostname"] == args.host, filtered_vms)
    if args.project is not None:
        filtered_vms = filter(
            lambda d: d["project"] == args.project, filtered_vms)

    return filtered_vms


def print_vms(filtered_vms, outputfile, hosts_dict):
    """ Printout list of VMs."""

    filtered_vms = list(filtered_vms)

    output_string = (
            'Domain;Project;Name;Instancename;State;'
            'Cluster;Hostname;CPUs;RAM [GB];'
            'Disk IO Read;Disk IO Write;Disk KBs Read;Disk KBs Write')
    outputfile.write(f'{output_string}\n')

    for vm in sorted(filtered_vms, key=lambda i: (
            i["domain"],
            i["project"],
            i["name"])):
        output_string = (
            f'{vm["domain"]};{vm["project"]};{vm["name"]};'
            f'{vm["instancename"]};{vm["state"]};'
            f'{hosts_dict[vm["hostname"]][1]};{vm["hostname"]};'
            f'{vm["cpunumber"]};{float(round(vm["memory"]/1024,1))};'
            f'{vm["diskioread"]};{vm["diskiowrite"]};'
            f'{float(vm["diskkbsread"]):.0f};'
            f'{float(vm["diskkbswrite"]):.0f}')
        outputfile.write(f'{output_string}\n')


def list_hosts(cs):
    """ Creates listing of all hosts with info of cluster to add
    cluster info to output."""
    all_hosts = cs.listHosts(listall=True)["host"]
    # pprint.pprint(all_hosts)

    host_dict = {}

    for item in all_hosts:
        # pprint.pprint(item)
        if item["type"] == "Routing":
            host_dict[item["name"]] = [
                    item["id"],
                    item["clustername"]]
    host_dict["n.a."] = ["n.a.", "n.a."]

    return host_dict


def main():
    """ main :) """
    args = prepare_arguments()

    if args.name_outputfile is not None:
        outputfile = open(args.name_outputfile, 'w')
    else:
        outputfile = sys.stdout

    # Reads ~/.cloudstack.ini
    cs = CloudStack(**read_config())

    all_vms = collect_vms(cs)

    projects_container = cs.listProjects(listall=True)
    projects = projects_container["project"]

    for project in sorted(projects, key=lambda key: key["name"]):
        project_id = project["id"]
        all_vms = all_vms + collect_vms(
            cs, project_id)

    # pprint.pprint(all_vms)
    filtered_vms = filter_vms(all_vms, args)

    hosts_dict = list_hosts(cs)
    # pprint.pprint(all_hosts)
    print_vms(filtered_vms, outputfile, hosts_dict)

    if args.name_outputfile is not None:
        outputfile.close()


if __name__ == "__main__":
    main()
