import glob
import logging
import os
import sys
import urllib
import getpass

import ee
import requests

import helper_functions
import metadata_loader


def upload(user, path_for_upload, metadata_path=None, collection_name=None):
    """
    Uploads content of a given directory to GEE. The function first uploads an asset to Google Cloud Storage (GCS)
    and then uses ee.data.startIngestion to put it into GEE, Due to GCS intermediate step, users is asked for
    Google's account name and password.

    :param user: name of a Google account
    :param path_for_upload: path to a directory
    :param metadata_path: (optional) path to file with metadata
    :param collection_name: (optional) name to be given for the uploaded collection
    :return:
    """

    password = getpass.getpass()
    google_session = __get_google_auth_session(user, password)

    root_path_in_gee = ee.data.getAssetRoots()[0]['id']

    full_path_to_collection = os.path.join(root_path_in_gee, collection_name)

    helper_functions.create_image_collection(full_path_to_collection)

    metadata = metadata_loader.load_metadata_from_csv(metadata_path)
    all_images_paths = glob.glob(os.path.join(path_for_upload, '*.tif'))
    no_images = len(all_images_paths)

    for current_image_no, image in enumerate(all_images_paths):
        logging.info('Processing image %d out of %d: %s', current_image_no, no_images, image)
        filename = helper_functions.get_filename_from_path(path=image)
        properties = metadata[filename]
        asset_request = __upload_file(session=google_session,
                                      file_path=image,
                                      asset_name=os.path.join(full_path_to_collection, filename),
                                      properties=properties)
        task_id = ee.data.newTaskId(1)[0]
        r = ee.data.startIngestion(task_id, asset_request)
        __periodic_wait(current_image=current_image_no, period=50)


def __get_google_auth_session(username, password):
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


def __get_upload_url(session):
    r = session.get('https://ee-api.appspot.com/assets/upload/geturl?')
    return r.json()['url']


def __upload_file(session, file_path, asset_name, properties=None):
    files = {'file': open(file_path, 'rb')}
    upload_url = __get_upload_url(session)
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


def __periodic_wait(current_image, period):
    if (current_image + 1) % period == 0:
        # Time to check how many tasks are running!
        logging.info('Periodic check for number of running tasks is due')
        helper_functions.wait_for_tasks_to_complete()