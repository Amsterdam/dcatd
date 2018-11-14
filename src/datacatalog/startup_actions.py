import logging
from .handlers import datasets


logger = logging.getLogger(__name__)


async def replace_old_identifiers(app):
    old_identifiers = await app.hooks.get_old_identifiers(app=app)
    count = 0
    changed = 0
    for old_id in old_identifiers:
        count += 1
        new_id = await app.hooks.storage_id()
        result = await app.hooks.set_new_identifier(app=app, old_id=old_id, new_id=new_id)
        if result == 'UPDATE 1':
            changed += 1
    logger.info(f'Set new identifiers for {changed} datasets')
    if changed == count:
        return True
    else:
        return False


async def read_write_all_ch_shape_format(app):
    dataset_iterator = await app.hooks.storage_all(app=app)
    count = 0
    changed = 0
    logger.info('start rewriting datasets')
    async for docid, etag, doc in dataset_iterator:
        canonical_doc = await app.hooks.mds_canonicalize(app=app, data=doc)
        for distribution in canonical_doc.get('dcat:distribution', []):
            # TODO : remove code once it is in production
            # Rename old shape mediatype because the semicolon gives problems with filtering
            if 'dcat:mediaType' in distribution and distribution['dcat:mediaType'] == 'application/zip; format="shp"':
                distribution['dcat:mediaType'] = 'application/x-zipped-shp'
            if 'dct:format' in distribution and distribution['dct:format'] == 'application/zip; format="shp"':
                distribution['dct:format'] = 'application/x-zipped-shp'
            # END TODO : remove code once it is in production

        canonical_doc = await app.hooks.mds_before_storage(app=app, data=canonical_doc, old_data=canonical_doc)
        # Let the metadata plugin grab the full-text search representation
        searchable_text = await app.hooks.mds_full_text_search_representation(
            data=canonical_doc
        )
        count += 1
        result = await app.hooks.storage_update(
            app=app, docid=docid, doc=canonical_doc,
            searchable_text=searchable_text, etags={etag},
            iso_639_1_code="nl")
        if result:
            changed += 1
    logger.info(f'read_write for {changed} datasets')
    if changed == count:
        return True
    else:
        return False


_startup_actions = [
    #   DISABLE replace_old_identifiers until Service  & Delivery did check if old URL links are still used
    #   and this can be done without too much impact.
    #    ("replace_old_identifiers", replace_old_identifiers),
    ("rw_all_2018_11_14", read_write_all_ch_shape_format),
]


async def run_startup_actions(app):
    for (name, action) in _startup_actions:
        if not await app.hooks.check_startup_action(app=app, name=name):
            result = await action(app)
            if result:
                await app.hooks.add_startup_action(app=app, name=name)

