import fnmatch
import logging
import sys

import ee


def delete(asset_path):
    root_idx = asset_path.rfind('/')
    if root_idx == -1:
        logging.warning('Asset not found. Make sure you pass full asset name, e.g. users/pinkiepie/rainbow')
        sys.exit(1)
    root = asset_path[:root_idx]
    all_assets_names = [e['id'] for e in ee.data.getList({'id': root})]
    filtered_names = fnmatch.filter(all_assets_names, asset_path)
    if not filtered_names:
        logging.warning('Nothing to remove. Exiting.')
        sys.exit(1)
    else:
        for path in filtered_names:
            __delete_recursive(path)
            logging.info('Collection %s removed', path)


def __delete_recursive(asset_path):
    info = ee.data.getInfo(asset_path)
    if not info:
        logging.warning('Nothing to delete.')
        sys.exit(1)
    elif info['type'] == 'Image':
        pass
    elif info['type'] == 'Folder':
        items_in_destination = ee.data.getList({'id': asset_path})
        for item in items_in_destination:
            logging.info('Removing items in %s folder', item['id'])
            delete(item['id'])
    else:
        items_in_destination = ee.data.getList({'id': asset_path})
        for item in items_in_destination:
            ee.data.deleteAsset(item['id'])
    ee.data.deleteAsset(asset_path)
