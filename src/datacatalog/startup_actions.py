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


async def add_resource_identifiers(app):
    dataset_iterator = await app.hooks.storage_all(app=app)
    changed = 0
    async for docid, etag, doc in dataset_iterator:
        canonical_doc = await app.hooks.mds_canonicalize(data=doc, id=docid)
        identifiers_added = await datasets._add_distribution_identifiers(app, canonical_doc)
        if identifiers_added > 0:
            # Let the metadata plugin grab the full-text search representation
            searchable_text = await app.hooks.mds_full_text_search_representation(
                data=canonical_doc
            )
            new_etag = await app.hooks.storage_update(
                app=app, docid=docid, doc=canonical_doc,
                searchable_text=searchable_text, etags={etag},
                iso_639_1_code="nl")
            logger.debug(f'Added {identifiers_added} identifiers for {docid}')

        changed += identifiers_added
    logger.info(f'Set new identifiers for {changed} resources')
    return True


_startup_actions = [
#   DISABLE replace_old_identifiers until Service  & Delivery did check if old URL links are still used
#   and this can be done without too much impact.
#    ("replace_old_identifiers", replace_old_identifiers),
    ("add_resource_identifiers", add_resource_identifiers),
]


async def run_startup_actions(app):
    for (name, action) in _startup_actions:
        if not await app.hooks.check_startup_action(app=app, name=name):
            result = await action(app)
            if result:
                await app.hooks.add_startup_action(app=app, name=name)

