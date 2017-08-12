#!/usr/bin/env python

"""
Convert all sagenb worksheets to .ipynb jupyter files. The notebook base 
directory can be at an arbitrary location in the file system.
This tool is adapted from the one in the sagenb_export module in 
Sagemath 8.0.
sagenb_export module is required.
"""

import argparse
import logging
import os
import pickle
import sys

from sagenb_export.logger import log
from sagenb_export.sagenb_reader import NotebookSageNB as WorksheetSageNB
from sagenb_export.actions import action_print
from sagenb_export.actions import action_convert_ipynb


description = 'Convert sagenb worksheets to ipynb'


def load(path):
    with open(path, 'rb') as f:
        return pickle.load(f)


def all_iter(sagenb):
    store = os.path.join(sagenb, 'home', '__store__')
    return all_in_path(store)


def all_in_path(store):
    for path, dirs, files in os.walk(store):
        worksheet = os.path.join(path, 'worksheet.html')
        if os.path.isfile(worksheet):
            yield WorksheetSageNB(path)


def find_worksheet(sagenb, unique_id):
    user, wst_index = unique_id.split(':')
    path = os.path.join(sagenb, 'home', user, wst_index)
    return WorksheetSageNB(path)


def action_list(sagenb):
    def tr(unique_id, name):
        print(u'{0:<15} | {1}'.format(unique_id, name))
    tr('Unique ID', 'Worksheet Name')
    print('-' * 79)
    worksheets = dict(
        (worksheet.sort_key, worksheet)
        for worksheet in all_iter(sagenb)
    )
    for key in sorted(worksheets.keys()):
        worksheet = worksheets[key]
        tr(worksheet.unique_id, worksheet.name)


def convert_all(sagenb):
    users = [user[0] for user in load(os.path.join(sagenb, 'users.pickle'))
             if user[0] not in ['_sage_', 'pub', 'guest']]
    for user in users:
        path = os.path.join(sagenb, 'home', user)
        for worksheet in all_in_path(path):
            action_convert_ipynb(
                worksheet,
                os.path.join(
                    path, '{}.ipynb'.format(worksheet.unique_id)))


def make_parser():
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--log', dest='log', default=None,
                        help='one of [DEBUG, INFO, ERROR, WARNING, CRITICAL]')
    parser.add_argument('--sagenb', dest='sagenb', default='.',
                        help='location of the .sage directory')
    parser.add_argument('--list', dest='list', action='store_true',
                        help='list all SageNB notebooks')
    parser.add_argument('--all', dest='all', action='store_true',
                        help='Convert all worksheets')
    parser.add_argument('--ipynb', dest='ipynb', default=None,
                        help='output .ipynb notebook filename')
    parser.add_argument('--print', dest='print_text', action='store_true',
                        help='print notebook')
    parser.add_argument('worksheet', default=None, nargs='?',
                        help='SageNB worsheet unique id')
    return parser


def main():
    parser = make_parser()
    args = parser.parse_args()
    if args.log is not None:
        level = getattr(logging, args.log)
        log.setLevel(level=level)

    sagenb = os.path.expanduser(args.sagenb)

    if args.all:
        convert_all(args.sagenb)
    else:
        if args.list:
            action_list(sagenb)

        if not args.worksheet:
            sys.exit(0)
        worksheet = find_worksheet(sagenb, args.worksheet)

        if args.print_text:
            action_print(worksheet)

        if args.ipynb:
            ipynb_name = args.ipynb.format(nb=args.worksheet)
            if os.path.exists(ipynb_name):
                raise RuntimeError('file exists: {0}'.format(ipynb_name))
            action_convert_ipynb(worksheet, ipynb_name)


if __name__ == '__main__':
    main()
