FROM sd2e/reactors:python3-edge

# reactor.py, config.yml, and message.jsonschema will be automatically
# added to the container when you run docker build or abaco deploy
# COPY datacatalog /datacatalog
# Comment out if not actively developing python-datacatalog
RUN pip uninstall --yes datacatalog || true
# COPY datacatalog /datacatalog

# Install from Repo
RUN pip3 install --upgrade git+https://github.com/SD2E/python-datacatalog.git@develop

COPY agavejobs.jsonschema /schemas/agavejobs.jsonschema
COPY delete.jsonschema /schemas/delete.jsonschema
COPY event.jsonschema /schemas/event.jsonschema
COPY message.jsonschema /schemas/create.jsonschema
