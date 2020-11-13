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
                -a categories.csv \
                -o /tmp/config-delta.csv
        Additional Infos:
          To prepare a list of settingns for the new setup use:
            mysqld --version --help
          on the respective machine.

          Some sets of vanillasettings are provided in the files:
            mysql-variables-*.

        A file with category, mappings to units and MySQL cnf parameter
        names may be supplied. An example can be found in <categories.csv>.

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
        '-c', '--categories',
        dest='categories',
        help='Read file with categories.',
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


def prepare_categories(filename_categories):
    """Add categories to dict with differences."""
    dict_categories = {}
    if filename_categories:
        with open(filename_categories) as file_categories:
            for line in file_categories:
                list_categories = line.split(';')
                dict_categories[list_categories[0]] = {
                    "cnf_param_name": list_categories[1], }
                if len(list_categories) > 2:
                    dict_categories[
                        list_categories[0]][
                            "unit"] = list_categories[2].strip('\n')
                if len(list_categories) > 3:
                    dict_categories[
                        list_categories[0]][
                            "category"] = list_categories[3].strip('\n')
    return dict_categories


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

    differences = []
    for key in keys_intersection:
        if template_dataset[key]["value"] != new_dataset[key]["value"]:
            differences = differences + [{
                "key": key,
                "value_template": template_dataset[key]["value"],
                "value_new": new_dataset[key]["value"]}, ]
    for key in keys_new:
        differences = differences + [{
            "value_template": "setting not provided",
            "value_new": new_dataset[key]["value"]}, ]
    for key in keys_lost:
        differences = differences + [{
            "value_template": template_dataset[key]["value"],
            "value_new": "setting not provided"}, ]

    return differences


def merge_categories(differences, dict_categories):
    """Merges the categories into the list of differences"""
    differences_annotated = []
    if dict_categories:
        for item in differences:
            if item["key"] in dict_categories:
                item["cnf_param_name"] = dict_categories[item["key"]]["cnf_param_name"]
                for field in ["unit", "category"]:
                    if field in dict_categories[item["key"]]:
                        item[field] = dict_categories[item["key"]][field]
                    else:
                        item[field] = ""
            else:
                for field in ["cnf_param_name", "unit", "category"]:
                    item[field] = ""
            differences_annotated = differences_annotated + [item, ]

    return differences_annotated


def print_differences(outputfile, differences):
    """Printout the differences as CSV."""
    # pprint.pprint(differences)
    outputfile.write(
        'Category;Setting;CNF Param Name;New Value;Template Value;Unit\n')
    for item in sorted(differences, key=lambda i: (i["category"], i["key"])):
        outputfile.write((
            f'{item["category"]};{item["key"]};{item["cnf_param_name"]};'
            f'{item["value_new"]};'
            f'{item["value_template"]};{item["unit"]}\n'))


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

    if args.categories:
        dict_categories = prepare_categories(args.categories)
    # pprint.pprint(dict_categories)

    differences_annotated = merge_categories(differences, dict_categories)

    print_differences(outputfile, differences_annotated)

    if args.name_outputfile is not None:
        outputfile.close()


if __name__ == "__main__":
    main()
