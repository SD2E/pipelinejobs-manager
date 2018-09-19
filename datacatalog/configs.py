from .constants import *

class CatalogStore():
    debug = False
    uuid5_namespace = Constants.UUID_NAMESPACE
    agave_storage_system = 'data-sd2e-community'
    agave_root_dir = '/work/projects/SD2E-Community/prod/data'
    store_dir = Constants.UPLOADS_ROOT
    batch = 1000
    collections = {'updates': 'updates', 'fixity': 'datafiles',
        'challenges': 'challenges', 'experiments': 'experiments',
        'samples': 'samples', 'measurements': 'measurements',
        'files': 'files', 'pipelines': 'pipelines', 'jobs': 'jobs',
        'tokens': 'tokens'}
    mongodb = {'host': 'catalog.sd2e.org',
        'port': '27020', 'username': None,
        'password': None, 'replica_set': None}
