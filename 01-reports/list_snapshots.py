#!/usr/bin/python3

# pylint: disable=invalid-name
""" List CloudStack Configurations. """

import sys
# import pprint
import argparse
import textwrap
from cs import CloudStack, read_config

parser = argparse.ArgumentParser(
    prog='list_snapshots.py',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
    Create CSV list of all snapshots for a CloudStack intance.

    Autor: Melanie Desaive <m.desaive@mailbox.org>
    '''),
    epilog=textwrap.dedent('''\
    Examples:

    List all snapshots:
        python list_snapshots.py --only-vm-snapshots

    List only VM-snapshots:
        python list_snapshots.py --only-vm-snapshots

    List only volume-snapshots:
        python list_snapshots.py --only-volume-snapshots

    Send output to file:
        python list_snapshots.py -o some-outputfile.csv

    Additional Infos:

    Uses the "CS" CloudStack API Client. See https://github.com/exoscale/cs.
    To install use "pip install cs".

    Requires configuration file ~/.cloudstack.ini.

    Todo:

    '''))

parser.add_argument('--only-volume-snapshots',
                    dest='only_volume_snapshots',
                    help='List volume snapshots',
                    action='store_true',
                    required=False)
parser.add_argument('--only-vm-snapshots',
                    dest='only_vm_snapshots',
                    help='List VM snapshots',
                    action='store_true',
                    required=False)
parser.add_argument('-o', '--outputfile',
                    dest='name_outputfile',
                    help='Write output to file.',
                    required=False)
args = parser.parse_args()


def print_volume_snapshots(projectid=""):
    """ Prints all snapshots for one project."""

    tmp_snapshots = []

    if projectid != "":
        snapshots_container = cs.listSnapshots(
            listall=True,
            projectid=projectid)
    else:
        snapshots_container = cs.listSnapshots(listall=True)

    if snapshots_container != {}:
        snapshots = snapshots_container["snapshot"]
        # pprint.pprint(snapshots)
        # pylint: disable=redefined-outer-name
        for snapshot in snapshots:
            if projectid != "":
                snapshot_project = snapshot["project"]
            else:
                snapshot_project = ""
            snapshot_project = snapshot["project"]

            # Query VMName to snapshot
            volumes_container = cs.listVolumes(
                listall=True,
                id=snapshot["volumeid"],
                projectid=projectid)
            if volumes_container != {}:
                volumes = volumes_container["volume"]
                volume = volumes[0]
                volume_name = volume["name"]
                # volume_virtualmachineid = volume["virtualmachineid"]
                volume_virtualmachinename = volume["vmname"]
            else:
                volume_name = "n.a."
                # volume_virtualmachineid = "n.a."
                volume_virtualmachinename = "n.a."
            tmp_snapshots = tmp_snapshots + [({
                "domain": snapshot["domain"],
                "project": snapshot_project,
                "vmname": volume_virtualmachinename,
                "volname": volume_name,
                "snapshot_name": snapshot["name"],
                "vm_or_vol_snappy": 'Volume Snapshot',
                "snapshot_state": snapshot["state"],
                "created": snapshot["created"],
                "physicalsize": snapshot["physicalsize"],
                "intervaltype": snapshot["intervaltype"],
                "revertable": snapshot["revertable"],
                "snapshottype": snapshot["snapshottype"]}), ]
    return tmp_snapshots


def print_vm_snapshots(projectid=""):
    """Print all VM Snapshots."""

    tmp_snapshots = []

    if projectid != "":
        vms_container = cs.listVirtualMachines(
            listall=True,
            projectid=projectid)
    else:
        vms_container = cs.listVirtualMachines(listall=True)

    if vms_container != {}:
        vms = vms_container["virtualmachine"]
        for vm in vms:
            vm_name = vm["name"]
            vm_id = vm["id"]
            if projectid != "":
                vmsnapshots_container = cs.listVMSnapshot(
                    listall=True,
                    virtualmachineid=vm_id, projectid=projectid)
            else:
                vmsnapshots_container = cs.listVMSnapshot(
                    listall=True,
                    virtualmachineid=vm_id)

            if vmsnapshots_container != {}:
                vmsnapshots = vmsnapshots_container["vmSnapshot"]
                for vmsnapshot in vmsnapshots:
                    tmp_snapshots = tmp_snapshots + [({
                        "domain": vmsnapshot["domain"],
                        "project": vmsnapshot["project"],
                        "vmname": vm_name,
                        "volname": 'n.a.',
                        "snapshot_name": vmsnapshot["name"],
                        "vm_or_vol_snappy": 'VM Snapshot',
                        "snapshot_state": vmsnapshot["state"],
                        "created": vmsnapshot["created"]})]
    return tmp_snapshots


if args.name_outputfile is not None:
    outputfile = open(args.name_outputfile, 'w')
else:
    outputfile = sys.stdout

# Reads ~/.cloudstack.ini
cs = CloudStack(**read_config())

projects_container = cs.listProjects(listall=True)
# pprint.pprint(projects_container)
if projects_container != {}:
    projects = projects_container["project"]
else:
    projects = {}

all_snapshots = []

if not args.only_vm_snapshots:
    for project in sorted(projects, key=lambda key: key["name"]):
        project_name = project["name"]
        project_id = project["id"]
        all_snapshots = all_snapshots + (print_volume_snapshots(project_id))
    all_snapshots = all_snapshots + (print_volume_snapshots())

if not args.only_volume_snapshots:
    # if args.only_vm_snapshots:
    #     outputfile.write(
    #         'Domain;Projekt;VM Name;Volumename;Snapshot Name;'
    #         'VM or Volume Snapshot;State;Created\n')
    for project in sorted(projects, key=lambda key: key["name"]):
        project_name = project["name"]
        project_id = project["id"]
        all_snapshots = all_snapshots + (print_vm_snapshots(project_id))
    all_snapshots = all_snapshots + (print_vm_snapshots())


outputfile.write(
    'Domain;Projekt;VM Name;Volumename;Snapshot Name;'
    'VM or Volume Snapshot;State;Created;Physical Size;Intervaltype;'
    'Revertable;Type\n')
# pprint.pprint(all_snapshots)
# pylint: disable=redefined-outer-name
for snapshot in sorted(all_snapshots, key=lambda i: (
        i["domain"].lower(), i["project"].lower(),
        i["vmname"].lower(), i["created"])):
    if snapshot["vm_or_vol_snappy"] == 'Volume Snapshot':
        outputfile.write(
            f'{snapshot["domain"]};{snapshot["project"]};{snapshot["vmname"]};'
            f'{snapshot["volname"]};{snapshot["snapshot_name"]};'
            f'{snapshot["vm_or_vol_snappy"]};'
            f'{snapshot["snapshot_state"]};{snapshot["created"]};'
            f'{snapshot["physicalsize"]};{snapshot["intervaltype"]};'
            f'{snapshot["revertable"]};{snapshot["snapshottype"]}\n')
    else:
        outputfile.write(
            f'{snapshot["domain"]};{snapshot["project"]};'
            f'{snapshot["vmname"]};n.a.;'
            f'{snapshot["snapshot_name"]};{snapshot["vm_or_vol_snappy"]};'
            f'{snapshot["snapshot_state"]};{snapshot["created"]};'
            f'n.a.;n.a.;'
            f'n.a.;n.a.\n')


if args.name_outputfile is not None:
    outputfile.close()
