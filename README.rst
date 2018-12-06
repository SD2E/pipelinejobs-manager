PIPELINE JOBS MANAGER
=====================

This service manages PipelineJobs. It works in synergy with Reactors that create
jobs using the ``ManagedPipelineJob`` class from ``python-datacatalog``. It accepts
messages via HTTPS POST that allow it to accomplish the following actions:

- Update a job's state by:
	- Handling a native ``PipelineJobEvent`` message
	- Interpreting an ``AgaveJobsPost`` message as state-change event
	- (Future) Interpreting callback messages from other platforms
- Create a new ``PipelineJob`` for a ``Pipeline``
- Delete an existing ``PipelineJob``

Changing State
--------------

The PipelineJobs system integrates state and metadata over multiple web-enabled
processing platform. At present, it integrates Agave and Abaco systems, but
will be extended in future work. Integration is straightforward: the work
platform must only send a formatted JSON payload to a PipelineJobsManager
webhook URL. This payload must contain three pieces of information:

1. UUID of the ``PipelineJob``
2. State of the task on the processing platform itself
3. The token authorizing updates to the ``PipelineJob``

It also may convey, for storage in the history of the specific ``PipelineJob``,
additional data formatted as a JSON object.

Useing a Native Message
^^^^^^^^^^^^^^^^^^^^^^^

The simplest path to update a job uses a JSON document in the native
``PipelineJobEvent`` schema. In this example, the state for job ``1073f4ff-c2b9-5190-bd9a-e6a406d9796a``
is updated to ``RUNNING`` by posting The following document would be posted to ``https://<tenantUrl>/actors/v2/<actorId>/messages``.

.. code-block:: json

	{
	  "uuid": "1073f4ff-c2b9-5190-bd9a-e6a406d9796a",
	  "data": {
	    "arbitrary": "key value data"
	  },
	  "name": "run",
	  "token": "0dc73dc3ff39b49a"
	}

This document body is posted to ``https://<tenantUrl>/actors/v2/<actorId>/messages``

Management Actions
^^^^^^^^^^^^^^^^^^

Presently, **delete** is the only action supported.  POST a message in the
``PipelineJobDeleteAction`` schema to ``https://<tenantUrl>/actors/v2/<actorId>/messages``

.. code-block:: json

	{
	  "uuid": "5c7133d1-b297-592f-a236-2a2aa5c90824",
	  "action": "delete",
	  "force": true,
	  "token": "0dc73dc3ff39b49a"
	}



   job tracking service for SD2 Data Catalog. This actor can
process messages to accomplish the following goals. Behavior is determined by
which JSON schema the incoming message validates to.

Actions:
* create - Create a new job for a given pipeline_uuid. Schema: `create.json`
* event - Send a state-change event to a given job by its UUID. Schema: `event.jsonschema`
* delete - Delete a job (actually hides it unless forced)

The Pipeline Jobs Manager can respond to POST callbacks sent by Agave jobs. In
this case, it will process the the message body as job "data" and reads the
job UUID, authorization token, and event from url parameters.

Actor Messages
--------------

A Pipelines-enabled actor may update the status of a job by sending an *event*
message status to the Pipeline Jobs Manager actor with the following schema:

```json
{
	"$schema": "http://json-schema.org/draft-04/schema#",
	"title": "PipelinesJobStateEvent",
	"description": "Directly send a state-change event to a Pipelines Job",
	"type": "object",
	"properties": {
		"uuid": {
			"description": "a UUID referring to a known Pipeline Job",
			"type": "string"
		},
		"event": {
			"description": "a valid Pipeline Job state-change event",
			"type": "string",
			"enum": ["run", "update", "fail", "finish"]
		},
		"details": {
			"description": "an object containing additional context about the event (optional)",
			"type": "object"
		},
		"token": {
			"description": "an authorization token issued when the job was created",
			"type": "string",
			"minLength": 16,
			"maxLength": 17
		},
		"__options": {
			"type": "object",
			"description": "an object used to pass runtime options to a pipeline (private, optional)"
		}
	},
	"required": ["uuid", "event"],
	"additionalProperties": false
}
```
