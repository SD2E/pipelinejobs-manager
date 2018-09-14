FROM sd2e/reactors:python3-edge

# reactor.py, config.yml, and message.jsonschema will be automatically
# added to the container when you run docker build or abaco deploy
COPY datacatalog /datacatalog

COPY agavejobs.jsonschema /schemas/agavejobs.jsonschema
COPY delete.jsonschema /schemas/delete.jsonschema
COPY event.jsonschema /schemas/event.jsonschema
COPY message.jsonschema /schemas/create.jsonschema
