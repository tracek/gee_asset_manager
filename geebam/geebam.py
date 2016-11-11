#! /usr/bin/env python

import argparse
import json
import logging
import logging.config
import os
import sys

import ee

import batch_remover
import batch_uploader


def setup_logging(path):
    with open(path, 'rt') as f:
        config = json.load(f)
    logging.config.dictConfig(config)


def cancel_all_running_tasks():
    logging.info('Attempting to cancel all running tasks')
    running_tasks = [task for task in ee.data.getTaskList() if task['state'] == 'RUNNING']
    for task in running_tasks:
        ee.data.cancelTask(task['id'])
    logging.info('Cancel all request completed')


def get_filename_from_path(path):
    return os.path.splitext(os.path.basename(os.path.normpath(path)))[0]


def cancel_all_running_tasks_from_parser(args):
    cancel_all_running_tasks()
    

def delete_collection_from_parser(args):
    batch_remover.delete(args.id)


def upload_from_parser(args):
    if args.collection and args.path:
        logging.error('Collection and Path options are mutually exclusive')
        sys.exit(1)
    batch_uploader.upload(user=args.user,
                          source_path=args.directory,
                          destination_path=args.path,
                          metadata_path=args.metadata,
                          collection_name=args.collection or get_filename_from_path(args.directory),
                          multipart_upload=args.large,
                          nodata_value=args.nodata)


def main(args=None):
    setup_logging(path=os.path.join(os.path.dirname(__file__), 'logconfig.json'))
    parser = argparse.ArgumentParser(description='Google Earth Engine Batch Asset Manager')

    subparsers = parser.add_subparsers()
    parser_delete = subparsers.add_parser('delete', help='Deletes collection and all items inside.')
    parser_delete.add_argument('id', help='ID of the collection, either fully qualified or abbreviated (no need to pass users/username).')
    parser_delete.set_defaults(func=delete_collection_from_parser)

    parser_upload = subparsers.add_parser('upload', help='Batch Asset Uploader.')
    required_named = parser_upload.add_argument_group('Required named arguments.')
    required_named.add_argument('-u', '--user', help='Google account name (gmail address).', required=True)
    required_named.add_argument('-d', '--directory', help='Path to the directory with images.', required=True)
    optional_named = parser_upload.add_argument_group('Optional named arguments')
    optional_named.add_argument('-m', '--metadata', help='Path to CSV with metadata.')
    optional_named.add_argument('-c', '--collection', help='Name with path of the collection to create. If not provided, directory name '
                                                           'will be used. It assumes the upload goes to the user folder. Need upload to '
                                                           'a shared directory? Use --path instead. They are mutuall exclusive')
    optional_named.add_argument('-p', '--path', help='Absolute upload path. It does not take any assumptions about user folder, so '
                                                     'it can be used to upload to a shared folder. Mutually exclusive with --collection.')
    optional_named.add_argument('--large', action='store_true', help='(Advanced) Use multipart upload. Might help if upload of large '
                                                                     'files is failing on some systems. Might cause other issues.')
    optional_named.add_argument('--nodata', type=int, help='The value to burn into the raster as NoData (missing data)')
    parser_upload.set_defaults(func=upload_from_parser)

    parser_cancel = subparsers.add_parser('cancel', help='Cancel all running tasks')
    parser_cancel.set_defaults(func=cancel_all_running_tasks_from_parser)

    args = parser.parse_args()


    ee.Initialize()
    args.func(args)

if __name__ == '__main__':
    main()