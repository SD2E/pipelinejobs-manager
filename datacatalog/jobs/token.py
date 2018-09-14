import hashlib
from ..constants import Constants

class InvalidToken(ValueError):
    pass

def new_token(job_def):
    token_data = {'pipeline_uuid': job_def['_pipeline_uuid'],
                  'job_uuid': job_def['_uuid'],
                  'actor_id': job_def['actor_id']}
    return job_token(**token_data)


def validate_token(token, pipeline_uuid=None, job_uuid=None, actor_id=None, permissive=False):
    # Values for pipeline_uuid and actor_id should be looked up in Database
    token_data = {'pipeline_uuid': pipeline_uuid,
                  'job_uuid': job_uuid,
                  'actor_id': actor_id}
    valid_token = job_token(**token_data)
    if str(token) == valid_token:
        return True
    else:
        if permissive is True:
            return False
        else:
            raise InvalidToken('Token is not valid')

    return job_token(**token_data)

def job_token(**kwargs):
    msg = ':'.join(
        [
            Constants.JOBS_TOKEN_SALT,
            str(kwargs['pipeline_uuid']),
            str(kwargs['job_uuid']),
            str(kwargs['actor_id'])
        ])
    return str(hashlib.sha256(msg.encode('utf-8')).hexdigest()[0:16])
