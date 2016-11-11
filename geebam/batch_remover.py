import logging
import sys

import ee


def delete(asset_path):
    full_path = __get_full_path(asset_path)
    __delete_recursive(full_path)
    logging.info('Collection %s removed', full_path)


def __delete_recursive(asset_path):
    items_in_destination = ee.data.getList({'id': asset_path})
    if not items_in_destination: # empty already - remove
        ee.data.deleteAsset(asset_path)
    info = ee.data.getInfo(asset_path)
    if not info:
        return
    elif info['type'] == 'Folder':
        for item in items_in_destination:
            logging.info('Removing items in %s folder', item['id'])
            delete(item['id'])
    else:
        for item in items_in_destination:
            ee.data.deleteAsset(item['id'])

def __get_full_path(asset_id):
    full_id = asset_id
    if 'users' not in asset_id:
        root_path_in_gee = ee.data.getAssetRoots()[0]['id']
        full_id = root_path_in_gee + '/' + asset_id
    if not ee.data.getInfo(full_id):
        logging.warning('%s asset could not be found.', full_id)
        sys.exit(1)
    return full_id


