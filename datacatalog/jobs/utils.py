from uuid import UUID
import petname
import os
import arrow
from .. import identifiers

ARCHIVE_PATH_VERSIONS = ['v1']
ARCHIVE_PATH_PREFIXES = ['products']

def get_job_instance_directory(session=None):
    if session is None or len(session) < 4:
        return identifiers.interesting_animal.generate()
    if not session.endswith('-'):
        session = session + '-'
    return session + arrow.utcnow().format('YYYYMMDDTHHmmss') + 'Z'

def get_archive_path(pipeline_id, lab_name, experiment_reference, measurement_id=None, session=None):
    return __get_v1_archive_path(pipeline_id, lab, experiment_reference, measurement_id=None, session=session)

def __get_v1_archive_path(pipeline_id, lab_name, experiment_reference, measurement_id=None, session=None):
    """Construct an archivePath for a pipeline job
    Arguments:
    Parameters:
    Returns:
    String representation of a job archiving path
    """

    # FIXME Actually validate against known pipeline UUIDs
    identifiers.datacatalog_uuid.validate(pipeline_id)

    version = ARCHIVE_PATH_VERSIONS[0]
    path_els = [ARCHIVE_PATH_PREFIXES[0], version]

    # FIXME Validate lab, etc. against known metadata entries
    path_els.append(identifiers.datacatalog_uuid.generate(lab_name, binary=False))
    path_els.append(identifiers.datacatalog_uuid.generate(
        experiment_reference, binary=False))
    if measurement_id is not None:
        path_els.append(identifiers.datacatalog_uuid.generate(
            measurement_id, binary=False))
    if pipeline_id is not None:
        path_els.append(pipeline_id)
    # Allow settable session for correlation with other platform events
    path_els.append(get_job_instance_directory(session))

    # NOTE /products/v1/<lab.uuid>/<experiment.uuid>/<measurement.uuid>/<pipeline.uuid/<session|petname>-MMMMDDYYHHmmss
    return '/'.join(path_els)
