import os
import json
from attrdict import AttrDict
from jsonschema import ValidationError
from pprint import pprint
from reactors.runtime import Reactor, agaveutils
from datacatalog.jobs import JobStore, JobCreateFailure, JobUpdateFailure, EventMappings

def main():

    r = Reactor()
    m = AttrDict(r.context.message_dict)
    if m == {}:
        try:
            jsonmsg = json.loads(r.context.raw_message)
            m = jsonmsg
        except Exception:
            pass

    action = None
    try:
        for a in ['create', 'agavejobs', 'event', 'delete']:
            try:
                r.logger.info('Testing against {} schema'.format(a))
                r.validate_message(
                    m, messageschema='/schemas/' + a + '.jsonschema', permissive=False)
                action = a
                break
            except Exception as exc:
                print('Validation error: {}'.format(exc))
                pass
        if action is None:
            raise ValidationError('Message did not match any known schema')
    except Exception as vexc:
        r.on_failure('Failed to process message', vexc)

    r.logger.debug('Action selected: {}'.format(action))

    # allow override of settings
    if '__options' in m:
        try:
            options_settings = m.get('__options', {}).get('settings', {})
            if isinstance(options_settings, dict):
                options_settings = AttrDict(options_settings)
            r.settings = r.settings + options_settings
        except Exception as exc:
            r.on_failure('Failed to handle options', exc)

    # small-eel/w7M4JZZJeGXml/EGy13KRPQMeWV
    stores_session = '/'.join([r.nickname, r.uid, r.execid])
    r.logger.debug('db.updates.session: {}'.format(stores_session))

    # Set up Store objects
    job_store = JobStore(mongodb=r.settings.mongodb,
                         config=r.settings.get('catalogstore', {}),
                         session=stores_session)

    r.logger.info('HANDLING {}...'.format(action))

    if action == 'create':
        create_dict = {}
        for k in job_store.CREATE_OPTIONAL_KEYS:
            if k in m:
                create_dict[k] = m.get(k)
        try:
            new_job = job_store.create(pipeline_uuid=m['pipeline_uuid'], archive_path=m['archive_path'], actor_id=r.uid, **create_dict)
            r.on_success('Created job {} with access token {} for pipeline {}'.format(
                str(new_job['uuid']), str(new_job['token']), m['pipeline_uuid']))
        except Exception as exc:
            r.on_failure('Create failed', exc)

    if action == 'event':
        event_dict = {}
        for k in job_store.EVENT_OPTIONAL_KEYS:
            if k in m:
                event_dict[k] = m.get(k)
        try:
            up_job = job_store.handle_event(m.get('uuid'), m.get(
                'event'), m.get('token'), **event_dict)
            r.on_success('New status for job {} is {}'.format(
                up_job['_uuid'], up_job['status']))
        except Exception as exc:
            r.on_failure('Event was not processed', exc)

    # Event processor
    cb_event = None
    cb_uuid = None
    cb_token = None
    if action == 'agavejobs':
        event_dict = {}
        try:
            cb_agave_status = r.context.get('status', None)
            if cb_agave_status is not None:
                cb_agave_status = cb_agave_status.upper()
                cb_event = EventMappings.agavejobs.get(cb_agave_status, 'update')
            if cb_event is None:
                cb_event = r.context.get('event').lower()
            cb_uuid = r.context.get('uuid')
            cb_token = r.context('token')
        except Exception:
            r.on_failure('POST was missing one or more parameters')
        # Push the Agave jobs POST into data
        event_dict['data'] = dict(m)

        # Process it as normal
        try:
            up_job = job_store.handle_event(cb_uuid, cb_event, cb_token, **event_dict)
            r.on_success('New status for job {} is {}'.format(
                up_job['_uuid'], up_job['status']))
        except Exception as exc:
            r.on_failure('Event was not processed', exc)


    if action == 'delete':
        create_dict = {}
        for k in job_store.CREATE_OPTIONAL_KEYS:
            if k in m:
                create_dict[k] = m.get(k)
        try:
            new_job = job_store.create(
                pipeline_uuid=m['pipeline_uuid'], archive_path=m['archive_path'], actor_id=r.uid, **create_dict)
            r.on_success('Successfully created job {} for pipeline {}'.format(
                str(new_job['uuid']), m['pipeline_uuid']))
        except Exception as exc:
            r.on_failure('Create failed', exc)

if __name__ == '__main__':
    main()
