import argparse
import logging

import ee


def delete_collection(id):
    ee.Initialize()
    logging.info('Attempting to delete collection %s', id)
    if 'users' not in id:
        root_path_in_gee = ee.data.getAssetRoots()[0]['id']
        id = root_path_in_gee + '/' + id
    params = {'id': id}
    items_in_collection = ee.data.getList(params)
    for item in items_in_collection:
        ee.data.deleteAsset(item['id'])
    ee.data.deleteAsset(id)
    logging.info('Collection %s removed', id)


def cancel_all_running_tasks():
    ee.Initialize()
    logging.info('Attempting to cancel all running tasks')
    running_tasks = [task for task in ee.data.getTaskList() if task['state'] == 'RUNNING']
    for task in running_tasks:
        ee.data.cancelTask(task['id'])
    logging.info('Cancel all request completed')


def delete(args):
    print(args)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Google Earth Engine Batch Asset Manager', prog='GEE asset manager')
    # parser.add_argument('function', choices=['cancell', 'delete'])
    # delete_parser = parser.add_subparsers(help='Delete collection')
    # delete_parser.add_parser('delete', help='ID of the collection')
    # delete_parser.set_defaults(func=delete)
    # cancel_parser = parser.add_subparsers(help='Cancell all')
    # cancel_parser.add_parser('cancel', action='store_true')

    subparsers = parser.add_subparsers()
    parser_delete = subparsers.add_parser('delete')
    parser_delete.add_argument('id')
    parser_delete.set_defaults(func=delete)
    parser.parse_args()


