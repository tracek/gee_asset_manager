import logging
import sys

import ee


def delete(asset_path):
    __delete_recursive(asset_path)
    logging.info('Collection %s removed', asset_path)


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


if __name__ == '__main__':
    ee.Initialize()
    delete('testfolder')