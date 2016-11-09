import ast
import getpass
import glob
import logging
import os
import sys
import urllib

import ee
import requests
import retrying
from requests_toolbelt.multipart import encoder
from bs4 import BeautifulSoup

import helper_functions
import metadata_loader


def upload(user, source_path, destination_path=None, metadata_path=None, collection_name=None, multipart_upload=False):
    """
    Uploads content of a given directory to GEE. The function first uploads an asset to Google Cloud Storage (GCS)
    and then uses ee.data.startIngestion to put it into GEE, Due to GCS intermediate step, users is asked for
    Google's account name and password.

    In case any exception happens during the upload, the function will repeat the call a given number of times, after
    which the error will be propagated further.

    :param user: name of a Google account
    :param source_path: path to a directory
    :param destination_path: where to upload (absolute path)
    :param metadata_path: (optional) path to file with metadata
    :param collection_name: (optional) name to be given for the uploaded collection
    :return:
    """

    metadata = metadata_loader.load_metadata_from_csv(metadata_path) if metadata_path else None

    password = getpass.getpass()
    google_session = __get_google_auth_session(user, password)

    absolute_directory_path_for_upload = __get_absolute_path_for_upload(collection_name, destination_path)
    helper_functions.create_image_collection(absolute_directory_path_for_upload)

    path = os.path.join(os.path.expanduser(source_path), '*.tif')
    all_images_paths = glob.glob(path)
    no_images = len(all_images_paths)

    images_for_upload_path = __find_remaining_assets_for_upload(all_images_paths, absolute_directory_path_for_upload)

    for current_image_no, image_path in enumerate(images_for_upload_path):
        logging.info('Processing image %d out of %d: %s', current_image_no+1, no_images, image_path)
        filename = helper_functions.get_filename_from_path(path=image_path)

        asset_full_path = absolute_directory_path_for_upload + '/' + filename

        if metadata and not filename in metadata:
            logging.warning("No metadata exists for image %s: it will not be ingested", filename)
            with open('assets_missing_metadata.log', 'a') as missing_metadata_file:
                missing_metadata_file.write(image_path + '\n')
            continue

        properties = metadata[filename] if metadata else None

        try:
            r = __upload_to_gcs_and_start_ingestion_task(current_image_no, asset_full_path, google_session, image_path,
                                                         properties, multipart_upload)
        except Exception as e:
            logging.exception('Upload of %s has failed.', filename)


def __find_remaining_assets_for_upload(path_to_local_assets, path_remote):
    local_assets = [helper_functions.get_filename_from_path(path) for path in path_to_local_assets]
    if helper_functions.collection_exist(path_remote):
        remote_assets = helper_functions.get_asset_names_from_collection(path_remote)
        if len(remote_assets) > 0:
            assets_left_for_upload = set(local_assets) - set(remote_assets)
            if len(assets_left_for_upload) == 0:
                logging.warning('Collection already exists and contains all assets provided for upload. Exiting ...')
                sys.exit(1)

            logging.info('Collection already exists. %d assets left for upload to %s.', len(assets_left_for_upload), path_remote)
            assets_left_for_upload_full_path = [path for path in path_to_local_assets if helper_functions.get_filename_from_path(path) in assets_left_for_upload]
            return assets_left_for_upload_full_path
        else:
            logging.info('Collection already exists, but it is empty.')

    return path_to_local_assets


def __get_absolute_path_for_upload(collection_name, destination_path):
    if destination_path: # user has provided an absolute path
        return destination_path
    if collection_name.startswith('users') or collection_name.startswith('/users'): # absolute path
        return collection_name
    else: # relative path
        root_path_in_gee = ee.data.getAssetRoots()[0]['id']
        absolute_path = root_path_in_gee + '/' + collection_name
        return absolute_path


@retrying.retry(wait_exponential_multiplier=1000, wait_exponential_max=4000, stop_max_attempt_number=5)
def __upload_to_gcs_and_start_ingestion_task(current_image_no, asset_full_path, google_session, image_path, properties, multipart_upload):
    if multipart_upload:
        asset_request = __upload_large_file(session=google_session,
                                      file_path=image_path,
                                      asset_name=asset_full_path,
                                      properties=properties)
    else:
        asset_request = __upload_file(session=google_session,
                                      file_path=image_path,
                                      asset_name=asset_full_path,
                                      properties=properties)
    task_id = ee.data.newTaskId(1)[0]
    r = ee.data.startIngestion(task_id, asset_request)
    __periodic_wait(current_image=current_image_no, period=50)
    return r


def __validate_metadata(path_for_upload, metadata_path):
    validation_result = metadata_loader.validate_metadata_from_csv(metadata_path)
    keys_in_metadata = {result.keys for result in validation_result}
    images_paths = glob.glob(os.path.join(path_for_upload, '*.tif*'))
    keys_in_data = {helper_functions.get_filename_from_path(path) for path in images_paths}
    missing_keys = keys_in_data - keys_in_metadata

    if missing_keys:
        logging.warning('%d images does not have a corresponding key in metadata', len(missing_keys))
        print('\n'.join(e for e in missing_keys))
    else:
        logging.info('All images have metadata available')

    if not validation_result.success:
        print('Validation finished with errors. Type "y" to continue, default NO: ')
        choice = raw_input().lower()
        if choice not in ['y', 'yes']:
            logging.info('Application will terminate')
            exit(1)


def __extract_metadata_for_image(filename, metadata):
    if filename in metadata:
        return metadata[filename]
    else:
        logging.warning('Metadata for %s not found', filename)
        return None


def __get_google_auth_session(username, password):
    google_accounts_url = 'https://accounts.google.com'
    authentication_url = 'https://accounts.google.com/ServiceLoginAuth'

    session = requests.session()

    login_html = session.get(google_accounts_url)
    soup_login = BeautifulSoup(login_html.content, 'html.parser').find('form').find_all('input')
    payload = {}
    for u in soup_login:
        if u.has_attr('value'):
            payload[u['name']] = u['value']

    payload['Email'] = username
    payload['Passwd'] = password

    auto = login_html.headers.get('X-Auto-Login')
    follow_up = urllib.unquote(urllib.unquote(auto)).split('continue=')[-1]
    galx = login_html.cookies['GALX']

    payload['continue'] = follow_up
    payload['GALX'] = galx

    session.post(authentication_url, data=payload)
    return session


def __get_upload_url(session):
    r = session.get('https://ee-api.appspot.com/assets/upload/geturl?')
    d = ast.literal_eval(r.text)
    return d['url']


def __upload_large_file(session, file_path, asset_name, properties=None):
    upload_url = __get_upload_url(session)
    with open(file_path, 'rb') as f:
        form = encoder.MultipartEncoder({
            "documents": (file_path, f, "application/octet-stream"),
            "composite": "NONE",
        })
        headers = {"Prefer": "respond-async", "Content-Type": form.content_type}
        resp = session.post(upload_url, headers=headers, data=form)
        gsid = resp.json()[0]
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


def __upload_file(session, file_path, asset_name, properties=None):
    with open(file_path, 'rb') as f:
        files = {'file': f}
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