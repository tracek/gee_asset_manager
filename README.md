# Google Earth Engine Batch Asset Manager
Google Earth Engine Batch Asset Manager ambition is helping user with batch actions on assets. It will be developed on use case basis, so if there's something missing feel free to post a feature request in [Issues](https://github.com/tracek/gee_asset_manager/issues) tab.

## Table of contents
* [Installation](#installation)
* [Getting started](#getting-started)
    * [Batch uploader](#batch-uploader)
    * [Parsing metadata](#parsing-metadata)
* [Usage examples](#usage-examples)
    * [Delete a collection with content:](#delete-a-collection-with-content)
    * [Upload a directory with images and associate properties with each image:](#upload-a-directory-with-images-and-associate-properties-with-each-image)

## Installation
We assume Earth Engine Python API is installed and EE authorised as desribed [here](https://developers.google.com/earth-engine/python_install). To install:
```
git clone https://github.com/tracek/gee_asset_manager
cd gee_asset_manager && pip install -e .
```

Installation is an optional step; the application can be also run
directly by executing geebam.py script. The advantage of having it
installed is being able to execute geebam as any command line tool. I
recommend installation within virtual environment.

## Getting started

As usual, to print help:
```
geebam -h

positional arguments:
  {delete,upload,cancel,report}
    delete              Deletes collection and all items inside. Supports
                        Unix-like wildcards.
    upload              Batch Asset Uploader.
    cancel              Cancel all running tasks
    report              Produce summary of all assets.

optional arguments:
  -h, --help            show this help message and exit
  -s SERVICE_ACCOUNT, --service-account SERVICE_ACCOUNT
                        Google Earth Engine service account.
  -k PRIVATE_KEY, --private-key PRIVATE_KEY
                        Google Earth Engine private key file.
```

To obtain help for a specific functionality, simply call it with _help_
switch, e.g.: `geebam upload -h`. If you didn't install geebam, then you
can run it just by going to _geebam_ directory and running `python
geebam.py [arguments go here]`

## Batch uploader
The script creates an Image Collection from GeoTIFFs in your local
directory. By default, the collection name is the same as the local
directory name; with optional parameter you can provide a different
name. Another optional parameter is a path to a CSV file with metadata
for images, which is covered in the next section:
[Parsing metadata](#parsing-metadata).



```
geebam upload -h

usage: geebam upload [-h] --source SOURCE --dest DEST [-m METADATA] [--large]
                     [--nodata NODATA] [-u USER] [-s SERVICE_ACCOUNT]
                     [-k PRIVATE_KEY] [-b BUCKET]

optional arguments:
  -h, --help            show this help message and exit

Required named arguments.:
  --source SOURCE       Path to the directory with images for upload.
  --dest DEST           Destination. Full path for upload to Google Earth
                        Engine, e.g. users/pinkiepie/myponycollection
  -u USER, --user USER  Google account name (gmail address).

Optional named arguments:
  -m METADATA, --metadata METADATA
                        Path to CSV with metadata.
  --large               (Advanced) Use multipart upload. Might help if upload
                        of large files is failing on some systems. Might cause
                        other issues.
  --nodata NODATA       The value to burn into the raster as NoData (missing
                        data)
  -b BUCKET, --bucket BUCKET
                        Google Cloud Storage bucket name

```

### Parsing metadata
By metadata we understand here the properties associated with each image. Thanks to these, GEE user can easily filter collection based on specified criteria. The file with metadata should be organised as follows:

| filename (without extension) | property1 header | property2 header |
|------------------------------|------------------|------------------|
| file1                        | value1           | value2           |
| file2                        | value3           | value4           |

Note that header can contain only letters, digits and underscores. 

Example:

| id_no     | class      | category | binomial             |system:time_start|
|-----------|------------|----------|----------------------|-----------------|
| my_file_1 | GASTROPODA | EN       | Aaadonta constricta  |1478943081000    |
| my_file_2 | GASTROPODA | CR       | Aaadonta irregularis |1478943081000    |

The corresponding files are my_file_1.tif and my_file_2.tif. With each of the files five properties are associated: id_no, class, category, binomial and system:time_start. The latter is time in Unix epoch format, in milliseconds, as documented in GEE glosary. The program will match the file names from the upload directory with ones provided in the CSV and pass the metadata in JSON format:

```
{ id_no: my_file_1, class: GASTROPODA, category: EN, binomial: Aaadonta constricta, system:time_start: 1478943081000}
```

The program will report any illegal fields, it will also complain if not all of the images passed for upload have metadata associated. User can opt to ignore it, in which case some assets will have no properties.

Having metadata helps in organising your asstets, but is not mandatory - you can skip it.

## Usage examples

### Delete a collection with content:

The delete is recursive, meaning it will delete also all children assets: images, collections and folders. Use with caution!
```
geebam delete users/pinkiepie/test
```

Console output:
```
2016-07-17 16:14:09,212 :: oauth2client.client :: INFO :: Attempting refresh to obtain initial access_token
2016-07-17 16:14:09,213 :: oauth2client.client :: INFO :: Refreshing access_token
2016-07-17 16:14:10,842 :: root :: INFO :: Attempting to delete collection test
2016-07-17 16:14:16,898 :: root :: INFO :: Collection users/pinkiepie/test removed
```

### Delete all directories / collections based on a Unix-like pattern

```
geebam delete users/pinkiepie/*weird[0-9]?name*
```


### Upload a directory with images to your myfolder/mycollection and associate properties with each image:
```
geebam upload -u pinkiepie@gmail.com --source path_to_directory_with_tif -m path_to_metadata.csv --dest users/pinkiepie/myfolder/myponycollection
```
The script will prompt the user for Google account password. The program will also check that all properties in path_to_metadata.csv do not contain any illegal characters for GEE. Don't need metadata? Simply skip this option.

### Upload a directory with images with specific NoData value to a selected destination 
```
geebam upload -u pinkiepie@gmail.com --source path_to_directory_with_tif --dest users/pinkiepie/myfolder/myponycollection --nodata 222
```
In this case we need to supply full path to the destination, which is helpful when we upload to a shared folder. In the provided example we also burn value 222 into all rasters for missing data (NoData).