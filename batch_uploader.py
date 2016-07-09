import argparse
import csv
import glob
import json
import logging
import logging.config
import os
import sys
import urllib
from getpass import getpass

import ee
import requests


def load_metadata_from_csv(path):
    with open(path, mode='r') as metadata_file:
        reader = csv.reader(metadata_file)
        header = reader.next()
        result = {row[0]: dict(zip(header, row)) for row in reader}
        return result


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
    appspot_url = 'https://ee-api.appspot.com/assets/upload/geturl?'
    r = session.get(appspot_url)
    return r.json()['url']

def upload_file(session, file_path, asset_name, properties=None):
    files = {'file': open(file_path, 'rb')}
    uploadurl = get_upload_url(session)

    r = session.post(uploadurl, files=files)

    gsid = r.json()[0]
    asset_data = {"id": asset_name,
                  "tilesets": [
                      {"sources": [
                          {"primaryPath": gsid,
                           "additionalPaths": []}
                      ]}
                  ],
                  "bands": [],
                  "properties": properties,
                  "reductionPolicy": "MEAN"}
    return asset_data

def collection_exist(path):
    return True if ee.data.getInfo(path) else False

def create_image_collection(root, name):
    full_path_to_collection = os.path.join(root, name)
    if collection_exist(full_path_to_collection):
        logging.warning("Collection %s already exists", full_path_to_collection)
    else:
        ee.data.createAsset({'type': ee.data.ASSET_TYPE_IMAGE_COLL}, full_path_to_collection)
        logging.info('New collection %s created', full_path_to_collection)


if __name__ == '__main__':
    setup_logging(path='logconfig.json')
    parser = argparse.ArgumentParser(description='Google Earth Engine Asset Manager', prog='GEE asset manager')
    parser.add_argument('-u', '--user', help='Google account name (gmail address)', required=True)
    parser.add_argument('-d', '--directory', help='Path to the directory with images', required=True)
    parser.add_argument('-p', '--properties', help='Path to CSV with metadata')
    parser.add_argument('-c', '--collection', help='Name of the collection to create')
    args = parser.parse_args()

    image_collection_name = args.collection or os.path.basename(os.path.normpath(args.directory))

    ee.Initialize()
    root_path_in_gee = ee.data.getAssetRoots()[0]['id']
    create_image_collection(root_path_in_gee, image_collection_name)

    password = getpass()

    session = get_google_auth_session(args.user, password)

    for images in glob.glob(os.path.join(args.directory, '*.tif')):
        pass

    asset_request = upload_file(session, img, 'users/rspb/test_collection/test_lucy8')

    taskid = ee.data.newTaskId(1)[0]
    ret = ee.data.startIngestion(taskid, asset_request)
