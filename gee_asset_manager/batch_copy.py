import ee
import os
import csv
import logging

def copy(source, destination):
    with open(source, 'r') as f:
        reader = csv.reader(f)
        for line in reader:
            name = line[0]
            gme_id = line[1]
            gme_path = 'GME/images/' + gme_id
            ee_path = os.path.join(destination, name)
            logging.info('Copying asset %s to %s', gme_path, ee_path)
            try:
                ee.data.copyAsset(gme_path, ee_path)
            except ee.EEException as e:
                with open('failed_batch_copy.csv', 'w') as fout:
                    fout.write('{},{},{},{}'.format(name, gme_id, ee_path,e))


if __name__ == '__main__':
    ee.Initialize()
    assets = '/home/tracek/Data/consbio2016/test.csv'
    with open(assets, 'r') as f:
        reader = csv.reader(f)