import csv
import glob
import os


def load_from_csv(path):
    with open(path, mode='r') as metadata_file:
        reader = csv.reader(metadata_file)
        header = reader.next()
        result = {row[0]: dict(zip(header, row)) for row in reader}
        return result


if __name__ == '__main__':
    data_dir = r'/home/tracek/Data/lucy_species/'
    for csv_file in glob.glob(os.path.join(data_dir, '*.tif')):
        pass

    with open(os.path.join(data_dir, 'metadata.csv'), mode='r') as metadata_file:
        reader = csv.reader(metadata_file)
        header = reader.next()
        result = {row[0]: dict(zip(header, row)) for row in reader}

