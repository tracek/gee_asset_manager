import getpass
import logging
import os
import random
import string

import ee
import pytest
from builtins import input

from gee_asset_manager.batch_remover import delete
from gee_asset_manager.batch_uploader import upload

logging.basicConfig(level=logging.INFO)


class memoize:
  def __init__(self, function):
    self.function = function
    self.memoized = {}

  def __call__(self, *args):
    try:
      return self.memoized[args]
    except KeyError:
      self.memoized[args] = self.function(*args)
      return self.memoized[args]


def get_random_string(length):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))


@memoize
def mockreturn_pass():
    return input("Password: ")


@memoize
def get_username():
    return input("\nUser name: ")


@pytest.fixture(scope='module')
def setup_testfolder():
    ee.Initialize()
    root = ee.data.getAssetRoots()[0]['id']
    testfolder_name = root + '/test_geebam_' + get_random_string(8)
    ee.data.createAsset({'type': ee.data.ASSET_TYPE_FOLDER}, testfolder_name)
    logging.info('Setting up test folder %s', testfolder_name)
    return testfolder_name


def test_upload_with_metadata(monkeypatch, setup_testfolder):
    logging.info('Upload test. WARNING. Requires user name and password, which will be passed in open text.')
    username = get_username()
    monkeypatch.setattr(getpass, 'getpass', mockreturn_pass)
    source = os.path.join(os.path.dirname(__file__), 'images')
    metadata = os.path.join(os.path.dirname(__file__), 'images', 'metadata.csv')
    dest = setup_testfolder + '/test_upload_with_metadata'
    multipart = False
    nodata = None
    logging.info('Testing upload with metadata')
    upload(user=username, source_path=source, destination_path=dest, metadata_path=metadata, multipart_upload=multipart, nodata_value=nodata)


def test_upload_with_nodata_multipart(monkeypatch, setup_testfolder):
    username = get_username()
    monkeypatch.setattr(getpass, 'getpass', mockreturn_pass)
    source = os.path.join(os.path.dirname(__file__), 'images')
    dest = setup_testfolder + '/test_upload_with_nodata_multipart'
    multipart = True
    nodata = 42
    logging.info('Testing upload with nodata and multipart option')
    upload(user=username, source_path=source, destination_path=dest, multipart_upload=multipart, nodata_value=nodata)


def test_delete(setup_testfolder):
    ee.data.createAsset({'type': ee.data.ASSET_TYPE_FOLDER}, setup_testfolder + '/one_more_to_delete')
    logging.info('Removing test directory')
    delete(setup_testfolder)
    info = ee.data.getInfo(setup_testfolder)
    assert info == None