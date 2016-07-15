import csv
import logging
import re
import glob
import os

class IllegalPropertyName(Exception):
    pass


def load_metadata_from_csv(path, directory):
    """
    Grabs properties from the given csv file. The csv should be organised as follows:
    filename (without extension), property1, property2, ...

    Example:
    id_no,class,category,binomial
    my_file_1,GASTROPODA,EN,Aaadonta constricta
    my_file_2,GASTROPODA,CR,Aaadonta irregularis

    The corresponding files are my_file_1.tif and my_file_2.tif.

    The program will turn the above into a json object:

    { id_no: my_file_1, class: GASTROPODA, category: EN, binomial: Aaadonta constricta},
    { id_no: my_file_2, class: GASTROPODA, category: CR, binomial: Aaadonta irregularis}

    Checks the images in the specified directory to ensure that a metadata entry exists for each one
    if this is not the case, remove that image from the upload list.
    Also check for blank values in the metadata fields, which will cause Property KeyErrors on GEE
    Behaviour at the moment is to stop the upload if blank fields are found, to allow the user to edit the file.
    If images are present without metadata, the user can inspect the warnings to generate metadata rows for those images.
    :param met - a dictionary of dictionaries containing the metadata entries:

    :param path to csv:
    :return: dictionary of dictionaries:
    :return: list of full filepaths to upload
    """
    with open(path, mode='r') as metadata_file:
        reader = csv.reader(metadata_file)
        header = reader.next()

        if not properties_allowed(properties=header, validator=allowed_property_key):
            raise IllegalPropertyName()

        metadata = {row[0]: dict(zip(header, row)) for row in reader
                    if properties_allowed(properties=row, validator=allowed_property_value)}

        all_images_paths = glob.glob(os.path.join(directory, '*.tif'))
        filter_list = []
        for filepath in all_images_paths:
            if os.path.splitext(os.path.basename(os.path.normpath(filepath)))[0] not in metadata:
                
                filter_list.append(filepath)
                logging.warning("No metadata exists for image %s: it will not be ingested", filepath)
        
        all_images_paths = filter(lambda x: x not in filter_list, all_images_paths)
        
        return metadata, all_images_paths


def properties_allowed(properties, validator):
    return all(validator(prop) for prop in properties)


def allowed_property_value(prop):
    if prop:
        return True
    else:
        logging.warning('Illegal property: empty string')
        return False


def allowed_property_key(prop):
    google_special_properties = ('system:description',
                                 'system:provider_url',
                                 'system:tags',
                                 'system:time_end',
                                 'system:time_start',
                                 'system:title')

    if prop in google_special_properties or re.match("^[A-Za-z0-9_]+$", prop):
        return True
    else:
        logging.warning('Property name %s is invalid. Special properties [system:description, system:provider_url, '
                        'system:tags, system:time_end, system:time_start, system:title] are allowed; other property '
                        'keys must contain only letters, digits and underscores.')
        return False


def is_legal_gee_metadata(row):
    key = row[0]
    values = row[1:]
    re.match("^[A-Za-z0-9_]+$", ' asss_sasa')
