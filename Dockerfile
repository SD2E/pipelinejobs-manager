FROM sd2e/reactors:python3-edge

ARG DATACATALOG_BRANCH=agave_proxy
RUN pip uninstall --yes datacatalog || true
RUN pip3 install --upgrade --no-cache-dir \
    git+https://github.com/SD2E/python-datacatalog.git@${DATACATALOG_BRANCH}

COPY schemas /schemas

WORKDIR /mnt/ephemeral-01
