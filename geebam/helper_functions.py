import os
import logging
import ee
import time


def get_filename_from_path(path):
    return os.path.splitext(os.path.basename(os.path.normpath(path)))[0]


def get_number_of_running_tasks():
    return len([task for task in ee.data.getTaskList() if task['state'] == 'RUNNING'])


def wait_for_tasks_to_complete(ee, waiting_time=10, no_allowed_tasks_running=20):
    tasks_running = get_number_of_running_tasks()
    if tasks_running > no_allowed_tasks_running:
        logging.info('Number of running tasks is %d. Sleeping for %d s until it goes down to %d',
                     tasks_running, waiting_time, no_allowed_tasks_running)
        time.sleep(waiting_time)
        wait_for_tasks_to_complete(ee, waiting_time, no_allowed_tasks_running)


def collection_exist(path):
    return True if ee.data.getInfo(path) else False


def create_image_collection(full_path_to_collection):
    if collection_exist(full_path_to_collection):
        logging.warning("Collection %s already exists", full_path_to_collection)
    else:
        ee.data.createAsset({'type': ee.data.ASSET_TYPE_IMAGE_COLL}, full_path_to_collection)
        logging.info('New collection %s created', full_path_to_collection)

def get_asset_names_from_collection(collection_path):
    assets_list = ee.data.getList(params={'id': collection_path})
    assets_names = [os.path.basename(asset['id']) for asset in assets_list]
    return assets_names
