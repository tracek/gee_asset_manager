import ast
import getpass
import glob
import logging
import os
import sys
import urllib
import csv

import ee
import requests
import retrying
from requests_toolbelt.multipart import encoder
from bs4 import BeautifulSoup

import helper_functions
import metadata_loader

def upload(user, source_path, destination_path=None, metadata_path=None, collection_name=None, multipart_upload=False,
           nodata_value=None):
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
    submitted_tasks_id = {}
    failed_upload_file = open('failed_upload.csv', 'wb')
    failed_upload_writer = csv.writer(failed_upload_file)
    failed_upload_writer.writerow(['filename', 'task_id', 'error_msg'])

    metadata = metadata_loader.load_metadata_from_csv(metadata_path) if metadata_path else None

    password = getpass.getpass()
    google_session = __get_google_auth_session(user, password)

    absolute_directory_path_for_upload = __get_absolute_path_for_upload(collection_name, destination_path)
    helper_functions.create_image_collection(absolute_directory_path_for_upload)

    path = os.path.join(os.path.expanduser(source_path), '*.tif')
    all_images_paths = glob.glob(path)
    images_for_upload_path = __find_remaining_assets_for_upload(all_images_paths, absolute_directory_path_for_upload)
    no_images = len(images_for_upload_path)

    if no_images == 0:
        logging.error('No images found that match %s. Exiting...', path)
        sys.exit(1)

    for current_image_no, image_path in enumerate(images_for_upload_path):
        logging.info('Processing image %d out of %d: %s', current_image_no+1, no_images, image_path)
        filename = helper_functions.get_filename_from_path(path=image_path)

        asset_full_path = absolute_directory_path_for_upload + '/' + filename

        if metadata and not filename in metadata:
            logging.warning("No metadata exists for image %s: it will not be ingested", filename)
            failed_upload_writer.writerow([filename, 0, 'Missing metadata'])
            continue

        properties = metadata[filename] if metadata else None

        try:
            task_id = __upload_to_gcs_and_start_ingestion_task(asset_full_path, google_session, image_path,
                                                               properties, multipart_upload, nodata_value)
            submitted_tasks_id[task_id] = filename
            __periodic_check(current_image=current_image_no, period=4, tasks=submitted_tasks_id, writer=failed_upload_writer)
        except Exception as e:
            logging.exception('Upload of %s has failed.', filename)
            failed_upload_writer.writerow([filename, 0, str(e)])

    __check_for_failed_tasks_and_report(tasks=submitted_tasks_id, writer=failed_upload_writer)
    failed_upload_file.close()


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
            assets_left_for_upload_full_path = [path for path in path_to_local_assets
                                                if helper_functions.get_filename_from_path(path) in assets_left_for_upload]
            return assets_left_for_upload_full_path

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


@retrying.retry(wait_exponential_multiplier=1000, wait_exponential_max=4000, stop_max_attempt_number=3)
def __upload_to_gcs_and_start_ingestion_task(asset_full_path, google_session, image_path, properties,
                                             multipart_upload, nodata_value):
    if multipart_upload:
        asset_request = __upload_large_file(session=google_session,
                                      file_path=image_path,
                                      asset_name=asset_full_path,
                                      properties=properties,
                                      nodata=nodata_value)
    else:
        asset_request = __upload_file(session=google_session,
                                      file_path=image_path,
                                      asset_name=asset_full_path,
                                      properties=properties,
                                      nodata=nodata_value)
    task_id = ee.data.newTaskId(1)[0]
    r = ee.data.startIngestion(task_id, asset_request)
    return task_id


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


def __upload_large_file(session, file_path, asset_name, properties=None, nodata=None):
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
                      "properties": properties,
                      "missingData": {"value": nodata}
                      }
        return asset_data


def __upload_file(session, file_path, asset_name, properties=None, nodata=None):
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
                      "properties": properties,
                      "missingData": {"value": nodata}
                      }
        return asset_data


def __periodic_check(current_image, period, tasks, writer):
    if (current_image + 1) % period == 0:
        logging.info('Periodic check')
        __check_for_failed_tasks_and_report(tasks=tasks, writer=writer)
        # Time to check how many tasks are running!
        helper_functions.wait_for_tasks_to_complete(waiting_time=10, no_allowed_tasks_running=20)


def __check_for_failed_tasks_and_report(tasks, writer):
    if len(tasks) == 0:
        return

    statuses = ee.data.getTaskStatus(tasks.keys())

    for status in statuses:
        if status['state'] == 'FAILED':
            task_id = status['id']
            filename = tasks[task_id]
            error_message = status['error_message']
            writer.writerow(filename, task_id, error_message)
            logging.error('Ingestion of image %s has failed with message %s', filename, error_message)

    tasks.clear()