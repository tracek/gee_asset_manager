import csv
import logging
import re


class IllegalPropertyName(Exception):
    pass


def validate_metadata_from_csv(path):
    """
    Check if metadata is ok
    :param path:
    :return: true / false
    """
    with open(path, mode='r') as metadata_file:
        logging.info('Running metatdata validator for %s', path)
        validation_result = True
        reader = csv.reader(metadata_file)
        header = reader.next()

        if not properties_allowed(properties=header, validator=allowed_property_key):
            validation_result = False

        for row in reader:
            if not properties_allowed(properties=row, validator=allowed_property_value):
                validation_result = False

        if validation_result == True: logging.info('Validation successful')
        else: logging.error('Validation failed')

        return validation_result


def load_metadata_from_csv(path):
    """
    Grabs properties from the give csv file. The csv should be organised as follows:
    filename (without extension), property1, property2, ...

    Example:
    id_no,class,category,binomial
    my_file_1,GASTROPODA,EN,Aaadonta constricta
    my_file_2,GASTROPODA,CR,Aaadonta irregularis

    The corresponding files are my_file_1.tif and my_file_2.tif.

    The program will turn the above into a json object:

    { id_no: my_file_1, class: GASTROPODA, category: EN, binomial: Aaadonta constricta},
    { id_no: my_file_2, class: GASTROPODA, category: CR, binomial: Aaadonta irregularis}

    :param path to csv:
    :return: dictionary of dictionaries
    """
    with open(path, mode='r') as metadata_file:
        reader = csv.reader(metadata_file)
        header = reader.next()

        if not properties_allowed(properties=header, validator=allowed_property_key):
            raise IllegalPropertyName()

        metadata = {row[0]: dict(zip(header, row)) for row in reader
                    if properties_allowed(properties=row, validator=allowed_property_value)}
        return metadata


def properties_allowed(properties, validator):
    return all(validator(prop) for prop in properties)


def allowed_property_value(prop):
    if prop:
        return True
    else:
        logging.warning('Illegal property: empty string or None')
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
