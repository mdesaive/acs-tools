#!/usr/bin/python3

# pylint: disable=invalid-name
""" List CloudStack Templates. """

import sys
# import pprint
import argparse
import textwrap

from cs import CloudStack, read_config

parser = argparse.ArgumentParser(
    prog='list_templates.py',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
    Create CSV list of all templates for a CloudStack intance.

    Autor: Melanie Desaive <m.desaive@mailbox.org>
    '''),
    epilog=textwrap.dedent('''\
    Examples:

    List all templates:
        python list_templates.py

    Filter Template Types
        python list_templates.py --templatefilter="featured,self"

        possible values are "featured", "self", "selfexecutable",
        "sharedexecutable","executable", and "community".

        featured : templates that have been marked as featured and public.
        self :             templates that have been registered or created by
                           the calling user.
        selfexecutable :   same as self, but only returns templates that can be
                           used to deploy a new VM.
        sharedexecutable : templates ready to be deployed that have been
                           granted to the calling user by another user.
        executable :       templates that are owned by the calling user, or
                           public templates, that can be used to deploy a VM.
        community :        templates that have been marked as public but not
                           featured.
        all :              all templates (only usable by admins).

    Send output to file:
        python list_templates.py -o some-outputfile.csv

    Additional Infos:

    Uses the "CS" CloudStack API Client. See https://github.com/exoscale/cs.
    To install use "pip install cs".

    Requires configuration file ~/.cloudstack.ini.

    Todo:

    '''))

parser.add_argument('--templatefilter',
                    dest='templatefilter',
                    help='Filter Template Types',
                    required=False)
parser.add_argument('-o', '--outputfile',
                    dest='name_outputfile',
                    help='Write output to file.',
                    required=False)

args = parser.parse_args()


def collect_templates(list_templatefilter, projectid=""):
    """ Collect all template datasets."""
    if projectid != "":
        # pprint.pprint(list_templatefilter)
        worklist = list_templatefilter.copy()
        for filter_flag in ["featured", "community", "executable"]:
            if filter_flag in worklist:
                worklist.remove(filter_flag)
    else:
        worklist = list_templatefilter.copy()

    temp_templates = []

    for loop_templatefilter in worklist:
        if projectid != "":
            templates_container = cs.listTemplates(
                listall=True,
                templatefilter=loop_templatefilter,
                projectid=projectid)
        else:
            templates_container = cs.listTemplates(
                listall=True,
                templatefilter=loop_templatefilter)

        if templates_container != {}:
            templates = templates_container["template"]
            for template in templates:
                for key in ["project", "size", "bootable"]:
                    if key not in template:
                        template[key] = "n.a."
                temp_templates = temp_templates + [{
                    "id": template["id"],
                    "domain": template["domain"],
                    "project": template["project"],
                    "name": template["name"],
                    "used_filter": loop_templatefilter,
                    "status": template["status"],
                    "size": template["size"],
                    "hypervisor": template["hypervisor"],
                    "ostypename": template["ostypename"],
                    "format": template["format"],
                    "bootable": template["bootable"],
                    "isdynamicallyscalable":
                        template["isdynamicallyscalable"],
                    "isextractable": template["isextractable"],
                    "ispublic": template["ispublic"],
                    "isready": template["isready"],
                    "passwordenabled": template["passwordenabled"]}, ]
    return temp_templates


if args.name_outputfile is not None:
    outputfile = open(args.name_outputfile, 'w')
else:
    outputfile = sys.stdout

if args.templatefilter is not None:
    templatefilter = args.templatefilter.split(',')
    # pprint.pprint(templatefilter)
else:
    templatefilter = [
        "featured", "self", "selfexecutable", "sharedexecutable",
        "executable", "community"]
# Reads ~/.cloudstack.ini
cs = CloudStack(**read_config())

projects_container = cs.listProjects(listall=True)
projects = projects_container["project"]

all_templates = []

for project in sorted(projects, key=lambda key: key["name"]):
    project_name = project["name"]
    project_id = project["id"]
    # pprint.pprint(templatefilter)
    all_templates = all_templates + collect_templates(
        projectid=project_id, list_templatefilter=templatefilter)
# pprint.pprint(templatefilter)
all_templates = all_templates + collect_templates(
        projectid="", list_templatefilter=templatefilter)

# Filter out duplicates

# pprint.pprint(all_templates)
templates_condensed = []
last_id = ''
for loop_template in sorted(all_templates, key=lambda i: (
        i["id"],
        i["used_filter"])):

    if loop_template["id"] != last_id:
        templates_condensed = templates_condensed + [loop_template.copy(), ]
    else:
        templates_condensed[-1]["used_filter"] = (
            f'{templates_condensed[-1]["used_filter"]}/'
            f'{loop_template["used_filter"]}')
    last_id = loop_template["id"]

outputfile.write(
    'Domain;Project;Name;Templatetype;Status;Size;Hypervisor;OSTypename;'
    'Format;Bootable;isDynamicallyScalable;isExtractable;isPublic;isReady;'
    'Passwordenabled\n')
for loop_template in sorted(templates_condensed, key=lambda i: (
        i["domain"], i["project"], i["name"])):
    outputfile.write(
        f'{loop_template["domain"]};{loop_template["project"]};'
        f'{loop_template["name"]};{loop_template["used_filter"]};'
        f'{loop_template["status"]};'
        f'{loop_template["size"]};{loop_template["hypervisor"]};'
        f'{loop_template["ostypename"]};'
        f'{loop_template["format"]};{loop_template["bootable"]};'
        f'{loop_template["isdynamicallyscalable"]};'
        f'{loop_template["isextractable"]};'
        f'{loop_template["ispublic"]};{loop_template["isready"]};'
        f'{loop_template["passwordenabled"]}\n')
if args.name_outputfile is not None:
    outputfile.close()
