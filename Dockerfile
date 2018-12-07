FROM sd2e/reactors:python3-edge

# Comment out if not actively developing python-datacatalog
RUN pip uninstall --yes datacatalog || true
# COPY python-datacatalog /tmp/python-datacatalog
# WORKDIR /tmp/python-datacatalog
# RUN python3 setup.py install
# Install from Repo
RUN pip3 install --upgrade git+https://github.com/SD2E/python-datacatalog.git@composed_schema

COPY schemas /schemas

WORKDIR /mnt/ephemeral-01
