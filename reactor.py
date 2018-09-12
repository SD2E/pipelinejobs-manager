import os
import json
from attrdict import AttrDict
from pprint import pprint
from reactors.runtime import Reactor, agaveutils
from datacatalog.jobs import JobStore, JobCreateFailure, JobUpdateFailure
from datacatalog.identifiers import datacatalog_uuid

def main():

    r = Reactor()
    m = AttrDict(r.context.message_dict)
    if m == {}:
        try:
            print(r.context.raw_message)
            jsonmsg = json.loads(r.context.raw_message)
            m = jsonmsg
        except Exception:
            pass

    try:
        r.validate_message(m, permissive=False)
    except Exception as exc:
        r.on_failure('Failed to validate message', exc)

    if '__options' in m:
        # allow override of settings
        try:
            options_settings = m.get('__options', {}).get('settings', {})
            if isinstance(options_settings, dict):
                options_settings = AttrDict(options_settings)
            r.settings = r.settings + options_settings
        except Exception as exc:
            r.on_failure('Failed to handle options', exc)

    # small-eel/w7M4JZZJeGXml/EGy13KRPQMeWV
    stores_session = '/'.join([r.nickname, r.uid, r.execid])

    # Set up Store objects
    job_store = JobStore(mongodb=r.settings.mongodb,
                         config=r.settings.catalogstore,
                         session=stores_session)

    # Process message
    pipeline_uuid = datacatalog_uuid.mock(binary=False)
    # if 'pipeline_id' in m:
    #     pipeline_uuid = m.get('pipeline_id', datacatalog_uuid.mock())
    # else:
    #     pipeline_uuid = datacatalog_uuid.mock()

    event = m.get('event')
    if event.lower() == 'create':
        job = job_store.create_job(pipeline_uuid, m.get('data', {}))
        pprint(job)

if __name__ == '__main__':
    main()
