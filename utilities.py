def delete_collection(ee, id):
    if 'users' not in id:
        root_path_in_gee = ee.data.getAssetRoots()[0]['id']
        id = root_path_in_gee + '/' + id
    params = {'id': id}
    items_in_collection = ee.data.getList(params)
    for item in items_in_collection:
        ee.data.deleteAsset(item['id'])
    ee.data.deleteAsset(id)