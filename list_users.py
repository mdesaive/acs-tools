#!/usr/bin/python3

# pylint: disable=invalid-name
""" List CloudStack Users. """

import sys
import pprint
import argparse
import textwrap
from cs import CloudStack, read_config

parser = argparse.ArgumentParser(
    prog='list_users.py',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
    Create CSV list of all users for a CloudStack intance.

    Autor: Melanie Desaive <m.desaive@mailbox.org>
    '''),
    epilog=textwrap.dedent('''\
    Examples:

    List all users:
        python list_users.py

    Send output to file:
        python list_users.py -o some-outputfile.csv

    Additional Infos:

    Uses the "CS" CloudStack API Client. See https://github.com/exoscale/cs.
    To install use "pip install cs".

    Requires configuration file ~/.cloudstack.ini.

    Todo:

    '''))

parser.add_argument('--only-volume-users',
                    dest='only_volume_users',
                    help='List volume users',
                    action='store_true',
                    required=False)
parser.add_argument('--only-vm-users',
                    dest='only_vm_users',
                    help='List VM users',
                    action='store_true',
                    required=False)
parser.add_argument('-o', '--outputfile',
                    dest='name_outputfile',
                    help='Write output to file.',
                    required=False)
args = parser.parse_args()


def print_users(domain=""):
    """ Prints all users for one project."""

    if domain != "":
        users_container = cs.listUsers(
            listall=True,
            domainid=domain)
    else:
        users_container = cs.listUsers(listall=True)

    if users_container != {}:
        users = users_container["user"]
        for user in users:
            for key in ["email",]:
                if key not in user:
                    user[key] = "n.a."
    return users


if args.name_outputfile is not None:
    outputfile = open(args.name_outputfile, 'w')
else:
    outputfile = sys.stdout

# Reads ~/.cloudstack.ini
cs = CloudStack(**read_config())

all_users = print_users()

outputfile.write(
    'Domain;Username;First Name;Last Name;'
    'Email;Created;\n')

# pylint: disable=redefined-outer-name
for user in sorted(all_users, key=lambda i: (
        i["domain"].lower(),
        i["account"].lower(), i["username"].lower())):
    outputfile.write(
        f'{user["domain"]};'
        f'{user["username"]};'
        f'{user["firstname"]};{user["lastname"]};'
        f'{user["email"]};{user["created"]}\n')


if args.name_outputfile is not None:
    outputfile.close()
