#!/usr/bin/python3

# pylint: disable=invalid-name
""" Compare two sets of mysql variables. """

import sys
# import pprint
import argparse
import re
import textwrap


def prepare_arguments():
    """ Parse commandline arguments."""

    parser = argparse.ArgumentParser(
        prog='list_systemvms.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
        Compare two lists of MySQL variable settings and printout differences.

        Autor: Melanie Desaive <m.desaive@mailbox.org>
        '''),
        epilog=textwrap.dedent('''\
        Examples:

        Compare two files
            ./compare_mysql_variables.py \
                -n <some newly created list of settings> \
                -t template-deb-8-default-5_5.txt \
                -a annotations.csv \
                -o /tmp/config-delta.csv 
        Additional Infos:
          To prepare a list of settingns for the new setup use:
            mysqld --version --help
          on the respective machine.

          Some sets of vanillasettings are provided in the files:
            mysql-variables-*.

        A file with annotation, mappings to units and MySQL cnf parameter
        names may be supplied. An example can be found in <annotations.csv>.

        Files with settings of unconfigured/vanilla installation are provided
        in:
            template-deb-10-community-8_0.txt
            template-deb-8-default-5_5.txt

        Todo:

        '''))
    parser.add_argument(
        '-n', '--new-settings',
        dest='new_settings',
        help='New settings to be compared with template',
        required=True)

    parser.add_argument(
        '-t', '--template-settings',
        dest='template_settings',
        help='Template settings against which the new settings will be ' +
        'compared.',
        required=True)

    parser.add_argument(
        '-o', '--outputfile',
        dest='name_outputfile',
        help='Write output to file.',
        required=False)

    parser.add_argument(
        '-a', '--annotations',
        dest='annotations',
        help='Read file with annotations.',
        required=False)
    args = parser.parse_args()

    return args


def read_variable_set(filename_variable_set):
    """ Build a list of settings from the file."""
    dataset_variables = {}
    with open(filename_variable_set) as file_variable_set:
        at_relevant_portion = False
        for line in file_variable_set:
            if at_relevant_portion:
                if line != '\n':
                    key = line.split()[0]
                    value = re.sub('^' + key, '', line)
                    value = value.strip()
                    dataset_variables[key] = {"value": value}
                else:
                    at_relevant_portion = False
            else:
                if line[0:9] == '---------':
                    at_relevant_portion = True
    return dataset_variables


def prepare_annotations(filename_annotations):
    """Add annotations to dict with differences."""
    dict_annotations = {}
    if filename_annotations:
        with open(filename_annotations) as file_annotations:
            for line in file_annotations:
                list_annotations = line.split(';')
                dict_annotations[list_annotations[0]] = {
                    "cnf_param_name": list_annotations[1], }
                if len(list_annotations) > 2:
                    dict_annotations[
                        list_annotations[0]][
                            "unit"] = list_annotations[2].strip('\n')
                if len(list_annotations) > 3:
                    dict_annotations[
                        list_annotations[0]][
                            "annotation"] = list_annotations[3].strip('\n')
    return dict_annotations


def compare_variable_sets(
        new_dataset,
        template_dataset):
    """ Compare datasets. """
    # Compute differences
    new_dataset_keys = set(new_dataset.keys())
    template_dataset_keys = set(template_dataset.keys())

    keys_intersection = new_dataset_keys.intersection(template_dataset_keys)
    keys_new = new_dataset_keys.difference(template_dataset_keys)
    keys_lost = template_dataset_keys.difference(new_dataset_keys)

    differences = {}
    for key in keys_intersection:
        if template_dataset[key]["value"] != new_dataset[key]["value"]:
            differences[key] = {
                "value_template": template_dataset[key]["value"],
                "value_new": new_dataset[key]["value"]}
    for key in keys_new:
        differences[key] = {
            "value_template": "setting not provided",
            "value_new": new_dataset[key]["value"]}
    for key in keys_lost:
        differences[key] = {
            "value_template": template_dataset[key]["value"],
            "value_new": "setting not provided"}

    return differences


def merge_annotations(differences, dict_annotations):
    """Merges the annotations into the list of differences"""
    if dict_annotations:
        for key in differences:
            if key in dict_annotations:
                differences[key][
                    "cnf_param_name"] = dict_annotations[key]["cnf_param_name"]
                for field in ["unit", "annotation"]:
                    if field in dict_annotations[key]:
                        differences[key][field] = dict_annotations[key][field]
                    else:
                        differences[key][field] = ""
            else:
                for field in ["cnf_param_name", "unit", "annotation"]:
                    differences[key][field] = ""

    return differences


def print_differences(outputfile, differences):
    """Printout the differences as CSV."""
    # pprint.pprint(differences)
    outputfile.write(
        'Setting;CNF Param Name;New Value;Template Value;Unit;Annotation\n')
    for key, value in sorted(differences.items()):
        outputfile.write((
            f'{key};{value["cnf_param_name"]};'
            f'{value["value_new"]};'
            f'{value["value_template"]};{value["unit"]};'
            f'{value["annotation"]}\n'))


def main():
    """ main :) """
    args = prepare_arguments()

    if args.name_outputfile is not None:
        outputfile = open(args.name_outputfile, 'w')
    else:
        outputfile = sys.stdout

    template_dataset = read_variable_set(args.template_settings)
    new_dataset = read_variable_set(args.new_settings)

    differences = compare_variable_sets(
        new_dataset,
        template_dataset)

    if args.annotations:
        dict_annotations = prepare_annotations(args.annotations)

    differences = merge_annotations(differences, dict_annotations)

    print_differences(outputfile, differences)

    if args.name_outputfile is not None:
        outputfile.close()


if __name__ == "__main__":
    main()
