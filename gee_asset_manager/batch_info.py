# Much of the code below has been copied from
# https://github.com/google/earthengine-api/blob/master/python/ee/cli/commands.py

import sys
import datetime
import csv
import ee


class ReportWriter(object):

    def __init__(self, filename=None):
        self.total_size = 0
        self.writers = [csv.writer(sys.stdout)]
        self.writer_fo = None
        if filename:
            if sys.version_info[0] < 3:
                self.writer_fo = open(filename + '.csv', 'wb')
            else:
                self.writer_fo = open(filename + '.csv', 'w')
            self.writers.append(csv.writer(self.writer_fo))

    def __del__(self):
        if self.writer_fo and not self.writer_fo.closed:
            self.writer_fo.close()
        print('Total size [MB]: {:.2f}'.format(self.total_size))

    def writerow(self, data):
        [writer.writerow(data) for writer in self.writers]

def report(filename):
    ee.Initialize()
    assets_root = ee.data.getAssetRoots()
    writer = ReportWriter(filename)
    writer.writerow(['Asset id', 'Type', 'Size [MB]', 'Time', 'Owners', 'Readers', 'Writers'])

    for asset in assets_root:
        # List size+name for every leaf asset, and show totals for non-leaves.
        if asset['type'] == ee.data.ASSET_TYPE_FOLDER:
            children = ee.data.getList(asset)
            for child in children:
                _print_size(child, writer)
        else:
            _print_size(asset, writer)

def get_datetime_str(epoch):
    dt = datetime.datetime.fromtimestamp(epoch / 10**6) # microseconds to seconds
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def _print_size(asset, writer):
    asset_info = ee.data.getInfo(asset['id'])

    if 'properties' in asset_info and 'system:asset_size' in asset_info['properties']:
        size = asset_info['properties']['system:asset_size']
    else:
        size = _get_size(asset)
    size = round(size / 1024**2, 2) # size in MB

    type = asset_info['type']
    time = get_datetime_str(asset_info['version'])

    acl = ee.data.getAssetAcl(asset['id'])
    owners = ' '.join(acl['owners'])
    readers = ' '.join(acl['readers'])
    writers = ' '.join(acl['writers'])

    writer.writerow([asset['id'], type, size, time, owners, readers, writers])
    writer.total_size += size


def _get_size(asset):
    """Returns the size of the given asset in bytes."""
    size_parsers = {
        'Folder': _get_size_folder,
        'ImageCollection': _get_size_image_collection,
    }

    if asset['type'] not in size_parsers:
        raise ee.EEException(
            'Cannot get size for asset type "%s"' % asset['type'])

    return size_parsers[asset['type']](asset)


def _get_size_image(asset):
    info = ee.data.getInfo(asset['id'])

    return info['properties']['system:asset_size']


def _get_size_folder(asset):
    children = ee.data.getList(asset)
    sizes = [_get_size(child) for child in children]

    return sum(sizes)


def _get_size_image_collection(asset):
    images = ee.ImageCollection(asset['id'])
    sizes = images.aggregate_array('system:asset_size')

    return sum(sizes.getInfo())


if __name__ == '__main__':
    report(None)