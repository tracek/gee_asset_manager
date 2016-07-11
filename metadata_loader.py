import csv


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
        metadata = {row[0]: dict(zip(header, row)) for row in reader}
        return metadata

def validate_against_metadata(met, paths):
    """
    Checks the list of images to ensure that a metadata entry exists for each one
    if this is not the case, remove that image from the upload list.
    Also check for blank values in the metadata fields, which will cause Property KeyErrors on GEE
    Behaviour at the moment is to stop the upload if either type of errors is found, to allow the user to edit the file.
    :param met - a dictionary of dictionaries containing the metadata entries:
    :param paths - a list of full filepaths:
    :return: updated list of full filepaths
    """
    filter_list = []
    for filepath in paths:
        filename = get_filename_from_path(filepath)
        if filename not in met:
            # add the file path to the list that should be filtered out
            filter_list.append(filepath)
            logging.warning("No metadata exists for image %s: it will not be ingested", filename)
    # keeping this bit so that the user can specify whether this is a problem TODO
    result = filter(lambda x: x not in filter_list, paths)
    if len(filter_list) >0:
        return None
    # Now check for empty values in the metadata - these will throw errors on the Earth Engine side
    for key in met:
        for k, value in met[key].iteritems():
            if value is None or value == '':
                logging.warning("Found an empty value for item %s - field %s" % (key, k))
                return None