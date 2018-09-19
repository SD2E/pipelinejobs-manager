PIPELINE JOBS MANAGER
=====================

Ssupports a stateful job tracking service for SD2 Data Catalog. This actor can
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
