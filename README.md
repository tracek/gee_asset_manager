# Google Earth Engine batch asset uploader
Google Earth Engine Batch Asset Manager ambition is helping user with batch actions on assets. It will be developed on use case basis, so if there's something missing feel free to post a feature request in [Issues](https://github.com/tracek/gee_asset_manager/issues) tab.

## Prerequisites
We assume Earth Engine Python API is installed and EE authorised as desribed [here](https://developers.google.com/earth-engine/python_install).

## Batch uploader
The script creates an Image Collection from GeoTIFFs in your local directory. By default, the collection name is the same as the local directory name; with optional parameter you can provide a different name. Another optional parameter is a path to a CSV file with metadata for images, which is covered in the next section: [Parsing metadata](#parsing-metadata).

As usual, to print help:
```
python batch_manager.py -h
usage: GEE asset manager [-h] {delete,upload,cancel} ...

Google Earth Engine Batch Asset Manager

positional arguments:
  {delete,upload,cancel}
    delete              Deletes collection and all items inside.
    upload              Batch Asset Uploader.
    cancel              Cancel all running tasks

optional arguments:
  -h, --help            show this help message and exit
```

To obtain help for a specific functionality, simply call it with "help" switch, e.g.:

```
python batch_manager.py upload -h

usage: GEE asset manager [-h] -u USER -d DIRECTORY [-p PROPERTIES]
                         [-c COLLECTION]

Google Earth Engine Batch Asset Uploader

optional arguments:
  -h, --help            show this help message and exit

Required named arguments:
  -u USER, --user USER  Google account name (gmail address)
  -d DIRECTORY, --directory DIRECTORY
                        Path to the directory with images

Optional named arguments:
  -p PROPERTIES, --properties PROPERTIES
                        Path to CSV with metadata
  -c COLLECTION, --collection COLLECTION
                        Name of the collection to create

```

### Parsing metadata
By metadata we understand here the properties associated with each image. Thanks to these, GEE user can easily filter collection based on specified criteria. The file with metadata should be organised as follows:

| filename (without extension) | property1 header | property2 header |
|------------------------------|------------------|------------------|
| file1                        | value1           | value2           |
| file2                        | value3           | value4           |

Example:

| id_no     | class      | category | binomial             |
|-----------|------------|----------|----------------------|
| my_file_1 | GASTROPODA | EN       | Aaadonta constricta  |
| my_file_2 | GASTROPODA | CR       | Aaadonta irregularis |

The corresponding files are my_file_1.tif and my_file_2.tif.

The program will match the file names from the upload directory with ones provided in the CSV and pass the metadata in JSON format:

```
{ id_no: my_file_1, class: GASTROPODA, category: EN, binomial: Aaadonta constricta}
```

The program will report any illegal fields, it will also complain if not all of the images passed for upload have metadata associated. User can opt to ignore it, in which case some assets will have no properties.

Having metadata helps in organising your asstets, but is not mandatory - you can skip it.

### Usage example

#### Delete a collection with content:
```
python batch_manager.py delete test
```

Console output:
```
2016-07-17 16:14:09,212 :: oauth2client.client :: INFO :: Attempting refresh to obtain initial access_token
2016-07-17 16:14:09,213 :: oauth2client.client :: INFO :: Refreshing access_token
2016-07-17 16:14:10,842 :: root :: INFO :: Attempting to delete collection test
2016-07-17 16:14:16,898 :: root :: INFO :: Collection users/username/test removed
```

#### Upload a directory with images and associate properties with each image:
```
python batch_manager.py upload -u my_account@gmail.com -d path_to_directory_with_tif -p path_to_metadata.csv
```
The script will prompt the user for Google account password. The program will also check that all properties in path_to_metadata.csv do not contain any illegal characters for GEE. Don't need metadata? Simply skip this option.
