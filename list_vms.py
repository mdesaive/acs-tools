#!/usr/bin/python3

# pylint: disable=invalid-name
""" List CloudStack virtualmachines. """

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
            ./list_vms.py --with-total-volumes --host acs-compute-7

        List all VMs in some project:
            ./list_vms.py --project "Test von Melanie (Mauerpark)"

        List only stopped VMs:
            ./list_vms.py --only-stopped-vms

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
        '--with-total-volumes',
        dest='with_total_volumes',
        help='List total used diskspace for each VM.',
        action='store_true',
        required=False)
    parser.add_argument(
        '--with-networks',
        dest='with_networks',
        help='List networks attached to VM.',
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


def collect_vms(cs, with_total_volumes, projectid=""):
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
            for key in ["project", "projectid", "hostname"]:
                if key not in my_vm:
                    my_vm[key] = "n.a."

            if with_total_volumes:
                tmp_volumestotal = 0
                tmp_volumescount = 0

                if my_vm["projectid"] == "n.a.":
                    volumes_container = cs.listVolumes(
                        virtualmachineid=my_vm["id"],
                        listall=True)
                else:
                    volumes_container = cs.listVolumes(
                        virtualmachineid=my_vm["id"],
                        projectid=my_vm["projectid"],
                        listall=True)
                if volumes_container:
                    volumes = volumes_container["volume"]
                    for volume in volumes:
                        tmp_volumestotal = (
                            tmp_volumestotal + int(volume["size"]))
                        tmp_volumescount = tmp_volumescount + 1
                my_vm["volumestotalsize"] = f'{int(tmp_volumestotal/1024**3)}'
                my_vm["volumescount"] = f'{tmp_volumescount}'

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


def print_vms(filtered_vms, args, outputfile):
    """ Printout list of VMs."""

    filtered_vms = list(filtered_vms)

    max_nics = 0
    if args.with_networks:
        # Find maximum number of networks assigned to VM
        for vm in filtered_vms:
            number_nics = len(vm["nic"])
            if number_nics > max_nics:
                max_nics = number_nics

    output_string = 'Domain;Project;Name;State;Hostname;CPUs;RAM [GB]'
    if args.with_total_volumes:
        output_string = output_string + ';Volumes Total [GB];Volumes Count'
    if args.with_networks:
        for i in range(number_nics):
            output_string = (
                output_string + f';[{i}] Is Default;[{i}] Network Name')
    outputfile.write(f'{output_string}\n')

    for vm in sorted(filtered_vms, key=lambda i: (
            i["domain"],
            i["project"],
            i["name"])):
        output_string = (
            f'{vm["domain"]};{vm["project"]};{vm["name"]};{vm["state"]};'
            f'{vm["hostname"]};{vm["cpunumber"]};{int(vm["memory"]/1024)}')
        if args.with_total_volumes:
            output_string = (
                output_string +
                f';{vm["volumestotalsize"]};{vm["volumescount"]}')
        if args.with_networks:
            for nic in sorted(vm["nic"], key=lambda i: i["networkname"]):
                output_string = (
                    output_string +
                    f';{nic["isdefault"]};{nic["networkname"]}')
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

    all_vms = collect_vms(cs, args.with_total_volumes)

    projects_container = cs.listProjects(listall=True)
    projects = projects_container["project"]

    for project in sorted(projects, key=lambda key: key["name"]):
        project_id = project["id"]
        all_vms = all_vms + collect_vms(
            cs, args.with_total_volumes, project_id)

    # pprint.pprint(all_vms)
    filtered_vms = filter_vms(all_vms, args)

    print_vms(filtered_vms, args, outputfile)

    if args.name_outputfile is not None:
        outputfile.close()


if __name__ == "__main__":
    main()
