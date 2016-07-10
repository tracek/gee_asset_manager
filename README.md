# Google Earth Engine batch asset uploader
Google Earth Engine batch asset manager ambition is helping user with batch actions on assets. It will be developed on use case basis, so if there's something missing feel free to post a feature request in [Issues](https://github.com/tracek/gee_asset_manager/issues) tab.

## Batch uploader
The script creates an Image Collection from GeoTIFFs in your local directory. By default, the collection name is the same as the local directory name; with optional parameter you can provide a different name. Another optional parameter is a path to a CSV file with metadata for images, which is covered in the next section: [Parsing metadata](#parsing-metadata).

As usual, to print help:

```
python batch_uploader.py -h

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

### Usage example
```
python batch_uploader -u my_account@gmail.com -d path_to_directory_with_tif -p path_to_metadata.csv
```
