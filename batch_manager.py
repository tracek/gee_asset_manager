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
    print(args.id)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Google Earth Engine Batch Asset Manager', prog='GEE asset manager')

    subparsers = parser.add_subparsers()
    parser_delete = subparsers.add_parser('delete', help='Deletes collection and all items inside')
    parser_delete.add_argument('id', help='ID of the collection, either fully qualified or abbreviated (no need to pass users/username)')
    parser_delete.set_defaults(func=delete)
    args = parser.parse_args()
    args.func(args)


