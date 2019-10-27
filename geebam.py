#! /usr/bin/env python

__copyright__ = """

    Copyright 2016 Lukasz Tracewski

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""
__license__ = "Apache 2.0"

import argparse
import logging
import os

import ee

from gee_asset_manager.batch_remover import delete
from gee_asset_manager.batch_uploader import upload
from gee_asset_manager.config import setup_logging
from gee_asset_manager.batch_info import report
from gee_asset_manager.batch_copy import copy


def cancel_all_running_tasks():
    logging.info('Attempting to cancel all running tasks')
    running_tasks = [task for task in ee.data.getTaskList() if task['state'] == 'RUNNING']
    for task in running_tasks:
        ee.data.cancelTask(task['id'])
    logging.info('Cancel all request completed')


def cancel_all_running_tasks_from_parser(args):
    cancel_all_running_tasks()


def delete_collection_from_parser(args):
    delete(args.id)


def produce_report(args):
    report(args.filename)


def batch_copy(args):
    copy(args.source, args.dest)


def upload_from_parser(args):
    upload(user=args.user,
           source_path=args.source,
           destination_path=args.dest,
           headless=args.headless,
           metadata_path=args.metadata,
           multipart_upload=args.large,
           nodata_value=args.nodata,
           bucket_name=args.bucket,
           band_names=args.bands,
           signal_if_error=args.upload_catch_error,
           tolerate_assets_already_exist=args.tolerate_assets_already_exist)
    

def _comma_separated_strings(string):
    """Parses an input consisting of comma-separated strings.
       Slightly modified version of: https://pypkg.com/pypi/earthengine-api/f/ee/cli/commands.py
    """
    error_msg = 'Argument should be a comma-separated list of alphanumeric strings (no spaces or other' \
                'special characters): {}'
    values = string.split(',')
    for name in values:
        if not name.isalnum():
            raise argparse.ArgumentTypeError(error_msg.format(string))
    return values



def main(args=None):
    setup_logging()
    parser = argparse.ArgumentParser(description='Google Earth Engine Batch Asset Manager')
    parser.add_argument('-s', '--service-account', help='Google Earth Engine service account.', required=False)
    parser.add_argument('-k', '--private-key', help='Google Earth Engine private key file.', required=False)

    subparsers = parser.add_subparsers()
    parser_delete = subparsers.add_parser('delete', help='Deletes collection and all items inside. Supports Unix-like wildcards.')
    parser_delete.add_argument('id', help='Full path to asset for deletion. Recursively removes all folders, collections and images.')
    parser_delete.set_defaults(func=delete_collection_from_parser)

    parser_upload = subparsers.add_parser('upload', help='Batch Asset Uploader.')
    required_named = parser_upload.add_argument_group('Required named arguments.')
    required_named.add_argument('--source', help='Path to the directory with images for upload.', required=True)
    required_named.add_argument('--dest', help='Destination. Full path for upload to Google Earth Engine, e.g. users/pinkiepie/myponycollection', required=True)
    optional_named = parser_upload.add_argument_group('Optional named arguments')
    optional_named.add_argument('-m', '--metadata', help='Path to CSV with metadata.')
    optional_named.add_argument('--large', action='store_true', help='(Advanced) Use multipart upload. Might help if upload of large '
                                                                     'files is failing on some systems. Might cause other issues.')
    optional_named.add_argument('--nodata', type=int, help='The value to burn into the raster as NoData (missing data)')
    optional_named.add_argument('--bands', type=_comma_separated_strings, help='Comma-separated list of names to use for the image bands. Spaces'
                                                                               'or other special characters are not allowed.')

    required_named.add_argument('-u', '--user', help='Google account name (gmail address).')
    optional_named.add_argument('-b', '--bucket', help='Google Cloud Storage bucket name.')
    optional_named.add_argument(
        '-e',
        '--upload-catch-error',
        action='store_true',
        help='Return exit code 1 when upload catches an error')
    optional_named.add_argument(
        '-a',
        '--tolerate-assets-already-exist',
        action='store_true',
        help='Return exit 0 when assets already exist')
    optional_named.add_argument('--headless', help='Run the browser in headless mode (i.e. no user interface).', action='store_true')

    parser_upload.set_defaults(func=upload_from_parser)

    parser_cancel = subparsers.add_parser('cancel', help='Cancel all running tasks')
    parser_cancel.set_defaults(func=cancel_all_running_tasks_from_parser)

    parser_info = subparsers.add_parser('report', help='Produce summary of all assets.')
    parser_info.set_defaults(func=produce_report)
    parser_info.add_argument('--filename', help='File name for the output CSV (optional)')

    parser_copy = subparsers.add_parser('copy', help='Batch copy of assets. Helps in migrating assets from Google Maps to GEE')
    parser_copy.set_defaults(func=batch_copy)
    parser_copy.add_argument('--source', help='File with the following structure: [asset name],[asset id in GME]')
    parser_copy.add_argument('--dest', help='Full path to the directory or collection in EE')

    args = parser.parse_args()

    if args.service_account:
        credentials = ee.ServiceAccountCredentials(args.service_account, args.private_key)
        ee.Initialize(credentials)
    else:
        ee.Initialize()

    if args.private_key is not None:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = args.private_key

    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()