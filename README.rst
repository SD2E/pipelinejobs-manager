PIPELINE JOBS MANAGER
=====================

This is a dedicated Abaco actor that manages creation, deletion, and status
updates for ``PipelineJobs``. It works in synergy with other Abaco actors that
create jobs using the ``ManagedPipelineJob`` class from ``python-datacatalog``.
It accepts multiple types of JSON message via authenticated HTTP POST and can
take the following actions:

- Update a job's state
- Create a new job for an existing pipeline
- Delete a job

Updating State
--------------

The PipelineJobs system is designed to integrate state and metadata over
multiple service platforms. Currently, it integrates compute jobs between Agave
and Abaco systems, but is also able to express how those jobs depend on other
services such as web services, third party databases, and the like. Eventually,
it will be able to orchestrate and integrate tasks on other systems.

Sending an Event Message
^^^^^^^^^^^^^^^^^^^^^^^^

PipelineJobs is built on Abaco actors, which are event-driven by nature. Thus,
the simplest means to update a PipelineJob is to send a JSON document in the
``PipelineJobEvent`` schema to a ``PipelineJobManager`` actor. Here is an
example of sending an **finish** event to job
``1073f4ff-c2b9-5190-bd9a-e6a406d9796a`` indicating that the job has completed.
The specific URL for a ``PipelineJobManager`` can vary, but will follow the
form ``https://<tenantUrl>/actors/v2/<actorId>/messages``.

.. code-block:: json

    {
      "uuid": "1073f4ff-c2b9-5190-bd9a-e6a406d9796a",
      "data": {
        "arbitrary": "key value data"
      },
      "name": "finish",
      "token": "0dc73dc3ff39b49a"
    }

Sending State via URL Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``token``, ``uuid``, and ``name`` fields can be sent as URL parameters of
an HTTP POST, so long as the body of the POST is valid JSON. In this case, the
JSON will be treated as ``data`` and attached to the job's history. The example
from above could be replicated with URL parameters like so:

.. code-block:: shell

    curl -XPOST --data '{"arbitrary": "key value data"}' \
        https://<tenantUrl>/actors/v2/<actorId>/messages?uuid=1073f4ff-c2b9-5190-bd9a-e6a406d9796a&\
        name=finish&token=0dc73dc3ff39b49a

Managing PipelineJobs
---------------------

Jobs can also be managed using posted JSON documents. At present, **delete** is
the only action supported. To delete a ``PipelineJob``, a message in the
``PipelineJobDeleteAction`` is POSTED to a ``PipelineJobManager`` actor.
Here is an example that deletes job ``10715620-ae90-5b92-bf4e-fbd491c21e03``

.. code-block:: json

    {
      "uuid": "10715620-ae90-5b92-bf4e-fbd491c21e03",
      "action": "delete",
      "force": true,
      "token": "0dc73dc3ff39b49a"
    }

Integrating with PipelineJobsManager
------------------------------------

This is fairly straightforward: the target platform only needs to be able to
send a simple **event** payload to a ``PipelineJobManager`` webhook URL. That
payload must contain:

1. The UUID of the ``PipelineJob`` that is managing the integration
2. A short alphanumeric **token** authorizing updates to the job
3. Some expression of the job's status on the target platform

Optionally, the event payload can also contain an arbitrary JSON object
``data`` that will be attached to the event in the job's history. This can be \
useful for passing along metadata that isn't represented by the
``PipelineJobs`` schema but that is needed elsewhere.

Authentication
^^^^^^^^^^^^^^

All POSTs to a ``PipelineJobsManager`` must be authenticated. There are two mechanisms by which this can happen:

  1. Send a valid TACC.cloud Oauth2 Bearer token with the request
  2. Include a special URL parameter called a **nonce** with the HTTP request

.. code-block:: shell
   :caption: "Sending a Bearer Token"

    curl -XPOST -H "Authorization: Bearer 969d11396c43b0b810387e4da840cb37" \
        --data '{"uuid": "1073f4ff-c2b9-5190-bd9a-e6a406d9796a", \
        "token": "0dc73dc3ff39b49a",\
        "name": "finish"}' \
        https://<tenantUrl>/actors/v2/<actorId>/messages

.. code-block:: shell
   :caption: "Using a Nonce"

    curl -XPOST --data '{"arbitrary": "key value data"}' \
        https://<tenantUrl>/actors/v2/<actorId>/messages?uuid=1073f4ff-c2b9-5190-bd9a-e6a406d9796a&\
        name=finish&token=0dc73dc3ff39b49a&\
        x-nonce=TACC_XXXXxxxxYz
