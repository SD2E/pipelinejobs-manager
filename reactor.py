import os
import sys
import json
from attrdict import AttrDict
from jsonschema import ValidationError
from pprint import pprint
from reactors.runtime import Reactor, agaveutils
from datacatalog.linkedstores.pipelinejob import PipelineJobStore, AgaveEvents
from datacatalog.linkedstores.pipelinejob.exceptions import *

def minify_job_dict(post_dict):
    """Strip out extraneous keys from an Agave job POST

    Returns:
        dict: Slim, svelte job dictionary
    """
    for strip_key in ['_links', 'retries', 'localId']:
        if strip_key in post_dict:
            del post_dict[strip_key]
    return post_dict

def main():

    rx = Reactor()
    m = AttrDict(rx.context.message_dict)

    if m == {}:
        try:
            jsonmsg = json.loads(rx.context.raw_message)
            m = jsonmsg
        except Exception:
            pass

#    ['event', 'agavejobs', 'create', 'delete']
    action = 'emptypost'
    try:
        for a in ['agavejobs']:
            try:
                rx.logger.info('Testing against {} schema'.format(a))
                rx.validate_message(
                    m, messageschema='/schemas/' + a + '.jsonschema', permissive=False)
                action = a
                break
            except Exception as exc:
                print('Validation error: {}'.format(exc))
        if action is None:
            pprint(m)
            raise ValidationError('Message did not a known schema')
    except Exception as vexc:
        rx.on_failure('Failed to process message', vexc)

    rx.logger.debug('SCHEMA DETECTED: {}'.format(action))

    store = PipelineJobStore(mongodb=rx.settings.mongodb)
        # rx.logger.debug('Verify database: {}'.format(store.db.list_collection_names()))

    # Event processing

    # Get URL params from Abaco context
    #
    # These can be overridden by the event body or custom
    # code implemented to process the message. This has a
    # side effect of allowing the manager to process empty
    # POST bodies so long as the right values are presented
    # as URL params. To make it very clear what is going on,
    # the event will be annotated with a 'note' indicating
    # its provenance.
    cb_event_name = rx.context.get('event', None)
    cb_job_uuid = rx.context.get('uuid', None)
    cb_token = rx.context.get('token', 'null')
    # RESEARCH - will we need to urldecode the contents of 'note'?
    cb_note = rx.context.get('note', 'Event had no JSON payload')
    # Accomodate 'status' which is what Agave jobs know about
    cb_agave_status = rx.context.get('status', None)
    cb_data = {'note': cb_note}

    event_dict = {'uuid': None,
                  'name': None,
                  'token': cb_token,
                  'data': cb_data}

    if action == 'agavejobs':
        try:
            # This assumes a callback URL that sends the Agave job status
            # as url parameter 'status', which is the default behavior
            # baked into the PipelineJobs system
            cb_agave_status = m.get('status', cb_agave_status)
            mes_agave_job_id = m.get('id', None)
            rx.logger.debug('agave_status: {}'.format(cb_agave_status))
            if cb_agave_status is not None:
                cb_agave_status = cb_agave_status.upper()
                # # Map any unknown state to update and store it
                # cb_event_name = AgaveEvents.agavejobs.get(
                #     cb_agave_status, 'update')
        except Exception as exc:
            rx.on_failure('Agave callback POST was had missing or invalid parameters', exc)

        # Push a filtered form of the Agave job POST into data
        # on RUNNING and a simple status update otherwise

        if cb_agave_status == 'RUNNING':
            cb_data = minify_job_dict(dict(m))
        else:
            cb_data = {'status': cb_agave_status}
            # fetch latest history entry and store as 'description' in event.data
            try:
                # Is there a better way than grabbing entire history that can
                # be implemented in a pure Agave call? Alternatively, we coulc
                # cache last offset for this job in rx.state but that will
                # limit our scaling to one worker
                agave_job_latest_history = rx.client.jobs.getHistory(jobId=mes_agave_job_id, limit=100)[-1].get('description', None)
                if agave_job_latest_history is not None:
                    cb_data['description'] = agave_job_latest_history
            except Exception as agexc:
                rx.logger.warning('Failed to get history for {}'.format(mes_agave_job_id))

    # If no event name was received but we do have an agave_status, use that
    if cb_event_name is None and cb_agave_status is not None:
        cb_event_name = AgaveEvents.agavejobs.get(cb_agave_status, 'update')
        rx.logger.debug('Status: {} => Event: {}'.format(
            cb_agave_status, cb_event_name))

    # This handler should go after all schema-informed handler code
    #
    # Update event dictionary with final values
    event_dict['uuid'] = cb_job_uuid
    event_dict['name'] = cb_event_name
    event_dict['data'] = cb_data

    # Sanity check event_dict and token
    if event_dict['uuid'] is None or event_dict['name'] is None or cb_token is None:
        rx.on_failure('No actionable message was received and a mandatory URL parameter is missing.')

    # Do the update
    try:
        up_job = store.handle(event_dict, cb_token)
        rx.on_success('Status for job {}: {}'.format(
            up_job['uuid'], up_job['state']))
    except Exception as exc:
        rx.on_failure('Event not processed', exc)

    # TODO: Implement support for generic schema. Must be last one evaluated!

    # # allow override of settings
    # if '__options' in m:
    #     try:
    #         options_settings = m.get('__options', {}).get('settings', {})
    #         if isinstance(options_settings, dict):
    #             options_settings = AttrDict(options_settings)
    #         rx.settings = rx.settings + options_settings
    #     except Exception as exc:
    #         rx.on_failure('Failed to handle options', exc)

    # # small-eel/w7M4JZZJeGXml/EGy13KRPQMeWV
    # stores_session = '/'.join([rx.nickname, rx.uid, rx.execid])
    # rx.logger.debug('db.updates.session: {}'.format(stores_session))

    # # Set up Store objects
    # job_store = JobStore(mongodb=rx.settings.mongodb,
    #                      config=rx.settings.get('catalogstore', {}),
    #                      session=stores_session)

    # rx.logger.info('HANDLING {}...'.format(action))

    # if action == 'create':
    #     create_dict = {}
    #     for k in job_store.CREATE_OPTIONAL_KEYS:
    #         if k in m:
    #             create_dict[k] = m.get(k)
    #     try:
    #         new_job = job_store.create(
    #             pipeline_uuid=m['pipeline_uuid'], archive_path=m['archive_path'], actor_id=rx.uid, **create_dict)
    #         rx.on_success('Created job {} with access token {} for pipeline {}'.format(
    #             str(new_job['uuid']), str(new_job['token']), m['pipeline_uuid']))
    #     except Exception as exc:
    #         rx.on_failure('Create failed', exc)

    # if action == 'event':
    #     event_dict = {}
    #     for k in job_store.EVENT_OPTIONAL_KEYS:
    #         if k in m:
    #             event_dict[k] = m.get(k)
    #     try:
    #         up_job = job_store.handle_event(m.get('uuid'), m.get(
    #             'event'), m.get('token'), **event_dict)
    #         rx.on_success('New status for job {} is {}'.format(
    #             up_job['_uuid'], up_job['status']))
    #     except Exception as exc:
    #         rx.on_failure('Event was not processed', exc)

    # # Event processor
    # cb_event = None
    # cb_uuid = None
    # cb_token = None
    # if action == 'agavejobs':
    #     event_dict = {}
    #     try:
    #         cb_agave_status = rx.context.get('status', None)
    #         if cb_agave_status is not None:
    #             cb_agave_status = cb_agave_status.upper()
    #             cb_event = EventMappings.agavejobs.get(
    #                 cb_agave_status, 'update')
    #         if cb_event is None:
    #             cb_event = rx.context.get('event').lower()
    #         cb_uuid = rx.context.get('uuid')
    #         cb_token = rx.context('token')
    #     except Exception:
    #         rx.on_failure('POST was missing one or more parameters')
    #     # Push the Agave jobs POST into data
    #     event_dict['data'] = dict(m)

    #     # Process it as normal
    #     try:
    #         up_job = job_store.handle_event(
    #             cb_uuid, cb_event, cb_token, **event_dict)
    #         rx.on_success('New status for job {} is {}'.format(
    #             up_job['_uuid'], up_job['status']))
    #     except Exception as exc:
    #         rx.on_failure('Event was not processed', exc)

    # if action == 'delete':
    #     create_dict = {}
    #     for k in job_store.CREATE_OPTIONAL_KEYS:
    #         if k in m:
    #             create_dict[k] = m.get(k)
    #     try:
    #         new_job = job_store.create(
    #             pipeline_uuid=m['pipeline_uuid'], archive_path=m['archive_path'], actor_id=rx.uid, **create_dict)
    #         rx.on_success('Successfully created job {} for pipeline {}'.format(
    #             str(new_job['uuid']), m['pipeline_uuid']))
    #     except Exception as exc:
    #         rx.on_failure('Create failed', exc)


if __name__ == '__main__':
    main()
