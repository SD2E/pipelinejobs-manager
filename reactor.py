import os
import sys
import json
from attrdict import AttrDict
from jsonschema import ValidationError
from pprint import pprint
from reactors.runtime import Reactor, agaveutils

from datacatalog.linkedstores.pipelinejob import AgaveEvents
from datacatalog.linkedstores.pipelinejob.exceptions import *
from datacatalog.managers.pipelinejobs import ManagedPipelineJobInstance
from datacatalog.managers.pipelinejobs import ManagedPipelineJobError

def minify_job_dict(post_dict):
    """Strip out extraneous keys from an Agave job POST

    Returns:
        dict: Slim, svelte job dictionary
    """
    for strip_key in ["_links", "retries", "localId"]:
        if strip_key in post_dict:
            del post_dict[strip_key]
    return post_dict


def forward_event(uuid, event, state=None, data={}, robj=None):
    # Propagate events to events-manager via message
    try:
        handled_event_body = {
            'job_uuid': uuid,
            'event_name': event,
            'job_state': state,
            'data': data
        }
        # robj.logger.info('forward_event: {}'.format(handled_event_body))
        resp = robj.send_message(robj.settings.pipelines.events_manager_id,
                                 handled_event_body,
                                 retryMaxAttempts=3)
        return True
    except Exception as exc:
        robj.logger.warning(
            "Failed to propagate handled({0}) for {1}: {2}".format(
                event, uuid, exc))


def message_control_annotator(up_job, states, rx):
    if up_job['state'] in states:
        try:
            message = {'uuid': up_job['uuid'], "state": up_job['state']}
            rx.logger.info("message: {}".format(message))
            resp = rx.send_message("control-annotator.prod",
                                   message,
                                   retryMaxAttempts=3)
        except Exception as exc:
            rx.logger.warning(
                "Failed to send message to control-annotator.prod for job {}: {}"
                .format(up_job['uuid'], exc))
    else:
        rx.logger.info(
            "skipping message to control_annotator.prod for {}".format(
                up_job["state"]))


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
    action = "emptypost"
    try:
        for a in ["aloejobs", "event", "agavejobs"]:
            try:
                rx.logger.info("Testing against {} schema".format(a))
                rx.validate_message(m,
                                    messageschema="/schemas/" + a +
                                    ".jsonschema",
                                    permissive=False)
                action = a
                break
            except Exception as exc:
                print("Validation error: {}".format(exc))
        if action is None:
            pprint(m)
            raise ValidationError("Message did not a known schema")
    except Exception as vexc:
        rx.on_failure("Failed to process message", vexc)

    # rx.logger.debug("SCHEMA DETECTED: {}".format(action))

    # store = PipelineJobStore(mongodb=rx.settings.mongodb)
    # Process the event

    # Get URL params from Abaco context
    #
    # These can be overridden by the event body or custom
    # code implemented to process the message. This has a
    # side effect of allowing the manager to process empty
    # POST bodies so long as the right values are presented
    # as URL params.
    #
    # cb_* variables are always overridden by the contents of
    #   the POST body
    #
    cb_event_name = rx.context.get("event", None)
    cb_job_uuid = rx.context.get("uuid", None)
    cb_token = rx.context.get("token", "null")
    # Accept a 'note' as a URL parameter
    # TODO - urldecode the contents of 'note'
    cb_note = rx.context.get("note", "Event had no JSON payload")
    # NOTE - contents of cb_data will be overridden in create, event. aloejob
    cb_data = {"note": cb_note}
    # Accept 'status', the Aloe-centric name for job.state
    # as well as 'state'
    cb_agave_status = rx.context.get("status", rx.context.get("state", None))

    # Prepare template PipelineJobsEvent
    event_dict = {
        "uuid": cb_job_uuid,
        "name": cb_event_name,
        "token": cb_token,
        "data": cb_data,
    }

    # This is the default message schema 'event'
    if action == "event":
        # Filter message and override values in event_dict with its contents
        for k in ["uuid", "name", "token", "data"]:
            event_dict[k] = m.get(k, event_dict.get(k))

    # AgaveJobs can update the status of an existing job but cannot
    # create one. To do so, an Agave job must be launched
    # using the PipelineJobsAgaveProxy resource.
    if action == "agavejobs":
        rx.on_failure("Agave job callbacks are no longer supported")
    elif action == "aloejobs":
        try:
            # Aloe jobs POST their current JSON representation to
            # callback URL targets. The POST body contains a 'status' key.
            # If for some reason it doesn't, job status is determined by
            # the 'state' or 'status' URL parameter.
            if cb_agave_status is None:
                cb_agave_status = m.get("status", None)
            # Agave job message bodies include 'id' which is the jobId
            mes_agave_job_id = m.get("id", None)
            rx.logger.debug("aloe_status: {}".format(cb_agave_status))
            if cb_agave_status is not None:
                cb_agave_status = cb_agave_status.upper()
        except Exception as exc:
            rx.on_failure(
                "Aloe callback POST and associated URL parameters were missing some required fields",
                exc,
            )

        # If the job status is 'RUNNING' then use a subset of the POST for
        # event.data. Otherwise, create an event.data from the most recent
        # entry in the Agave job history. One small detail to note is that
        # callbacks are sent at the beginning of event processing in the
        # Agave jobs service and so a handful of fields in the job record
        # that are late bound are not yet populated when the event is sent.
        if cb_agave_status == "RUNNING":
            cb_data = minify_job_dict(dict(m))
        else:
            cb_data = {"status": cb_agave_status}
            # Fetch latest history entry to put in event.data
            try:
                # Is there a better way than grabbing entire history that can
                # be implemented in a pure Agave call? Alternatively, we could
                # cache last offset for this job in rx.state but that will
                # limit our scaling to one worker
                #
                agave_job_latest_history = rx.client.jobs.getHistory(
                    jobId=mes_agave_job_id,
                    limit=100)[-1].get("description", None)
                if agave_job_latest_history is not None:
                    cb_data["description"] = agave_job_latest_history
            except Exception as agexc:
                rx.logger.warning("Failed to get history for {}: {}".format(
                    mes_agave_job_id, agexc))

        # Map the Agave job status to an PipelineJobsEvent name
        if cb_event_name is None and cb_agave_status is not None:
            cb_event_name = AgaveEvents.agavejobs.get(cb_agave_status,
                                                      "update")
            rx.logger.debug("Status: {} => Event: {}".format(
                cb_agave_status, cb_event_name))

        # Event name and data can be updated as part of processing an Agave POST
        # so apply the current values to event_dict here
        event_dict["name"] = cb_event_name
        event_dict["data"] = cb_data

    # Sanity check event_dict and token
    if event_dict["uuid"] is None or event_dict[
            "name"] is None or cb_token is None:
        rx.on_failure("No actionable event was received.")

    # Instantiate a job instance to leverage the MPJ framework
    store = ManagedPipelineJobInstance(rx.settings.mongodb, event_dict["uuid"], agave=rx.client)

    # Handle event...
    try:

        # First, proxy events. This code forwards index and indexed events to the jobs-indexer
        # Proxy 'index'
        if event_dict["name"] == "index":
            rx.logger.info("Forwarding 'index'")
            index_mes = {
                "name": "index",
                "uuid": event_dict["uuid"],
                "token": event_dict["token"],
            }
            rx.send_message(rx.settings.pipelines.job_indexer_id, index_mes)
            # Disable this since it should be picked up via events-manager subscription
            # message_control_annotator(up_job, ["INDEXING"], rx)

        # Proxy 'indexed'
        elif event_dict["name"] == "indexed":
            rx.logger.info("Forwarding 'indexed'")
            index_mes = {
                "name": "indexed",
                "uuid": event_dict["uuid"],
                "token": event_dict["token"],
            }
            rx.send_message(rx.settings.pipelines.job_indexer_id, index_mes)
            # Disable this since it should be picked up via events-manager subscription
            # message_control_annotator(up_job, ["FINISHED"], rx)

        # Handle all other events
        else:
            rx.logger.info("Handling '{}'".format(event_dict["name"]))
            # Get the current state of the MPJ. We use this to detect if 
            # handling the event has resulted in a change of state
            store_state = store.state
            # Send event at the beginning of state change so subscribers can pick 
            # up, for instance, a case where the job receives an index event and 
            # is in the FINISHED state.
            forward_event(event_dict["uuid"], event_dict['name'], store_state,
                          {}, rx)
            up_job = store.handle(event_dict, cb_token)
            if store_state != up_job["state"]:
                rx.logger.debug("Job state now: '{}'".format(up_job["state"]))
                # Only send second event if a state transition was detected
                forward_event(up_job["uuid"], event_dict['name'],
                              up_job["state"], {}, rx)

    except Exception as exc:
        rx.on_failure("Event not processed", exc)

    rx.on_success("Processed event in {} usec".format(rx.elapsed()))

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


if __name__ == "__main__":
    main()
