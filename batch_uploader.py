import argparse
import csv
import glob
import json
import logging
import logging.config
import os
import sys
import time
import urllib
from getpass import getpass

import ee
import requests


def load_metadata_from_csv(path):
    """
    Grabs properties from the give csv file. The csv should be organised as follows:
    filename (without extension), property1, property2, ...

    Example:
    id_no,class,category,binomial
    my_file_1,GASTROPODA,EN,Aaadonta constricta
    my_file_2,GASTROPODA,CR,Aaadonta irregularis

    The corresponding files are my_file_1.tif and my_file_2.tif.

    The program will turn the above into a json object:

    { id_no: my_file_1, class: GASTROPODA, category: EN, binomial: Aaadonta constricta},
    { id_no: my_file_2, class: GASTROPODA, category: CR, binomial: Aaadonta irregularis}

    :param path to csv:
    :return: dictionary of dictionaries
    """
    with open(path, mode='r') as metadata_file:
        reader = csv.reader(metadata_file)
        header = reader.next()
        metadata = {row[0]: dict(zip(header, row)) for row in reader}
        return metadata


def setup_logging(path, default_level=logging.INFO):
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


def get_google_auth_session(username, password):
    google_accounts_url = 'https://accounts.google.com'
    authentication_url = 'https://accounts.google.com/ServiceLoginAuth'

    session = requests.session()
    r = session.get(google_accounts_url)

    auto = r.headers.get('X-Auto-Login')
    follow_up = urllib.unquote(urllib.unquote(auto)).split('continue=')[-1]
    galx = r.cookies['GALX']

    payload = {
        'continue': follow_up,
        'Email': username,
        'Passwd': password,
        'GALX': galx
    }

    r = session.post(authentication_url, data=payload)

    if r.url != authentication_url:
        logging.info("Logged in")
        return session
    else:
        logging.critical("Logging failed")
        sys.exit(1)


def get_upload_url(session):
    r = session.get('https://ee-api.appspot.com/assets/upload/geturl?')
    return r.json()['url']


def upload_file(session, file_path, asset_name, properties=None):
    files = {'file': open(file_path, 'rb')}
    upload_url = get_upload_url(session)
    upload = session.post(upload_url, files=files)
    gsid = upload.json()[0]
    asset_data = {"id": asset_name,
                  "tilesets": [
                      {"sources": [
                          {"primaryPath": gsid,
                           "additionalPaths": []
                          }
                      ]}
                  ],
                  "bands": [],
                  "properties": properties
                  }
    return asset_data


def collection_exist(path):
    return True if ee.data.getInfo(path) else False


def create_image_collection(full_path_to_collection):
    if collection_exist(full_path_to_collection):
        logging.warning("Collection %s already exists", full_path_to_collection)
    else:
        ee.data.createAsset({'type': ee.data.ASSET_TYPE_IMAGE_COLL}, full_path_to_collection)
        logging.info('New collection %s created', full_path_to_collection)


def get_filename_from_path(path):
    return os.path.splitext(os.path.basename(os.path.normpath(path)))[0]


def get_number_of_running_tasks(ee):
    return len([task for task in ee.data.getTaskList() if task['state'] == 'RUNNING'])


def wait_for_tasks_to_complete(ee, waiting_time=10, no_allowed_tasks_running=8):
    tasks_running = get_number_of_running_tasks(ee)
    if tasks_running > no_allowed_tasks_running:
        logging.info('Number of running tasks is %d. Sleeping for %d s until it goes down to %d',
                     tasks_running, waiting_time, no_allowed_tasks_running)
        time.sleep(waiting_time)
        wait_for_tasks_to_complete(ee, waiting_time, no_allowed_tasks_running)


def periodic_wait(ee, current_image, period):
    if (current_image + 1) % period == 0:
        # Time to check how many tasks are running!
        logging.info('Periodic check for number of running tasks is due')
        wait_for_tasks_to_complete(ee)


def main(argv):
    setup_logging(path='logconfig.json')
    parser = argparse.ArgumentParser(description='Google Earth Engine Batch Asset Uploader', prog='GEE asset manager')
    required_named = parser.add_argument_group('Required named arguments')
    required_named.add_argument('-u', '--user', help='Google account name (gmail address)', required=True)
    required_named.add_argument('-d', '--directory', help='Path to the directory with images', required=True)
    optional_named = parser.add_argument_group('Optional named arguments')
    optional_named.add_argument('-p', '--properties', help='Path to CSV with metadata')
    optional_named.add_argument('-c', '--collection', help='Name of the collection to create')
    args = parser.parse_args()

    image_collection_name = args.collection or get_filename_from_path(args.directory)

    ee.Initialize()

    root_path_in_gee = ee.data.getAssetRoots()[0]['id']

    full_path_to_collection = os.path.join(root_path_in_gee, image_collection_name)

    create_image_collection(full_path_to_collection)

    password = getpass()

    google_session = get_google_auth_session(args.user, password)

    metadata = load_metadata_from_csv(args.properties)
    all_images_paths = glob.glob(os.path.join(args.directory, '*.tif'))
    no_images = len(all_images_paths)

    for current_image_no, image in enumerate(all_images_paths):
        logging.info('Processing image %d out of %d: %s', current_image_no, no_images, image)
        filename = get_filename_from_path(path=image)
        properties = metadata[filename]
        asset_request = upload_file(session=google_session,
                                    file_path=image,
                                    asset_name=os.path.join(full_path_to_collection, filename),
                                    properties=properties)
        task_id = ee.data.newTaskId(1)[0]
        r = ee.data.startIngestion(task_id, asset_request)
        periodic_wait(ee, current_image=current_image_no, period=50)


if __name__ == '__main__':
    main(sys.argv)
