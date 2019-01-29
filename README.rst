====================
PipelineJobs Manager
====================

This Reactor manages updates to **PipelineJobs** once they are created by other
processes using the **ManagedPipelineJob** and **ReactorManagedPipelineJob**
classes.

Update Job State
----------------

**PipelineJobs Manager** can update a job's state via three mechanisms:

#. Receipt of a JSON-formatted **pipelinejob_manager_event**
#. Receipt of URL parameters sufficient to form a **pipelinejob_manager_event**
#. Receipt of a **agave_job_callback** POST combined with ``uuid``, ``status`` and ``token`` URL parameters

These named document formats are documented below in jsonschemas_.

JSON Event Messages
^^^^^^^^^^^^^^^^^^^

The default method for updating a PipelineJob's state is to send a JSON message
to the Manager actor. Here is an example of a **finish** event for job
``1073f4ff-c2b9-5190-bd9a-e6a406d9796a``, which will indicate the job has
completed primary computation and archiving steps.

.. code-block:: json

    {
      "uuid": "1073f4ff-c2b9-5190-bd9a-e6a406d9796a",
      "name": "finish",
      "token": "0dc73dc3ff39b49a"
    }

This can be sent directly over HTTP like so:

.. code-block:: console

    curl -XPOST -H "Authorization: Bearer 969d11396c43b0b810387e4da840cb37" \
        --data '{"uuid": "1073f4ff-c2b9-5190-bd9a-e6a406d9796a", \
        "token": "0dc73dc3ff39b49a",\
        "name": "finish"}' \
        https://api.tacc.cloud/actors/v2/<actorId>/messages

It can also be sent from within a Recator like so:

.. code-block:: python

    rx = Reactor()
    manager_id = '<actorId>'
    finish_mes = { 'uuid': '1073f4ff-c2b9-5190-bd9a-e6a406d9796a',
                   'name': 'finish',
                   'token': '0dc73dc3ff39b49a'}
    rx.send_message(manager_id, finish_mes)

URL Parameters Event
^^^^^^^^^^^^^^^^^^^^

The ``uuid``, and ``event``, ``token`` fields can be sent as URL parameters in
an HTTP POST. The contents of the POST body will be attached to the event if
one is present. Our **finish** event expressed as URL parameters looks like:

.. code-block:: shell

    curl -XPOST --data '{"arbitrary": "key value data"}' \
        https://api.tacc.cloud/actors/v2/<actorId>/messages?uuid=1073f4ff-c2b9-5190-bd9a-e6a406d9796a&\
        event=finish&token=0dc73dc3ff39b49a

Agave Jobs Notification
^^^^^^^^^^^^^^^^^^^^^^^

HTTP POST body and URL parameters are combined to link the Agave
Jobs system with **PipelineJobs**, which is quite handy as Agave jobs often
are enlisted to do the computational heavy lifting in analysis workflows. This
approach is demonstrated in the **demo-jobs-reactor-app** repository.

PipelineJobs Events
--------------------

The state of every PipelineJob proceeds through a defined lifecycle, where
transitions occur in response to receipt of named events. This is illustrated
in the following image:

.. image:: http://docs.catalog.sd2e.org/en/gh-pages/_images/fsm-created.png
   :alt: PipelineJob States
   :align: right

**PipelineJobs Manager** accepts any of the events (lower case words attached
to the graph edges) save for **create**, which is reserved for other agents.

Authentication
--------------

POSTs to a **PipelineJobs Manager** must be authenticated by one of two means:

  1. Send a valid TACC.cloud Oauth2 Bearer token with the request
  2. Include a special URL parameter called a **nonce** with the HTTP request

.. _jsonschemas:

JSON Schemas
------------

.. literalinclude:: schemas/agavejobs.jsonschema
   :language: json
   :linenos:
   :caption: agave_job_callback

.. literalinclude:: schemas/event.jsonschema
   :language: json
   :linenos:
   :caption: pipelinejob_manager_event
