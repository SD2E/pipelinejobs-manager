import os
from .. import identifiers
from ..basestore import BaseStore, time_stamp
from .job import DataCatalogJob
class JobCreateFailure(Exception):
    pass

class JobUpdateFailure(Exception):
    pass
class JobStore(BaseStore):
    """Manages creation and management of datacatalog.jobs records and states"""

    def __init__(self, mongodb, config, pipeline_store=None, session=None):
        super(JobStore, self).__init__(mongodb, config, session)
        coll = config['collections']['jobs']
        if config['debug']:
            coll = '_'.join([coll, str(time_stamp(rounded=True))])
        self.name = coll
        # Used for looking up references to pipeline IDs
        self.pipelines = pipeline_store
        self.coll = self.db[coll]
        self._post_init()

    def create_job(self, pipeline_uuid, job_def, session=None, binary_uuid=True):
        """Create and return a new job instance
        Parameters:
        pipeline_uuid:uuid5 - valid db.pipelines.uuid
        job_def:dict - JSON serializable dict describing parameterization of the job
        Arguments:
        session:str - Optional correlation string
        binary_uuid:bool - whether to return the text or BSON binary UUID
        Returns:
        A jobs.uuid referring to the job in the data catalog
        """
        # Validate pipeline
        self.__validate_pipeline_id(pipeline_uuid)
        # job definition gets validated in DataCatalogJob
        new_job = DataCatalogJob(pipeline_uuid, job_def)
        try:
            result = self.coll.insert_one(new_job.as_dict())
            return self.coll.find_one({'_id': result.inserted_id})
        except Exception as exc:
            raise JobCreateFailure('Failed to create job for pipeline {}'.format(pipeline_uuid), exc)


    def handle_job_event(self, job_uuid, event_name, options={}, permissive=False):
        """Accept and process a job state-transition event
        Parameters:
        job_uuid:uuid5 - identifier for the job that is recieving an event
        event_name:str - event to be processed (Must validate to JobStateMachine.events)
        Arguments:
        options:dict - optional dict to pass to JobStateMachine event handler
        permissive:bool - ignore state and other Exceptions
        Returns:
        Boolean for successful handling of the event
        """
        pass


    def delete_job(self, job_uuid):
        pass

    def __validate_pipeline_id(self, pipeline_id):
        # Is it a UUID5
        try:
            identifiers.datacatalog_uuid.validate(pipeline_id)
        except Exception as exc:
            raise exc
        # FIXME: Check if it is known pipeline UUID via self.pipelines.query()
        return True

    def __validate_job_def(self, job_def):
        # Noop for now
        return True

