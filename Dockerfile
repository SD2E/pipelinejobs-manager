FROM sd2e/reactors:python3-edge

ARG DATACATALOG_BRANCH=v2.0.0
# RUN pip uninstall --yes datacatalog || true
RUN pip3 install --upgrade --no-cache-dir \
    git+https://github.com/SD2E/python-datacatalog.git@${DATACATALOG_BRANCH}

COPY schemas /schemas

ENV CATALOG_ADMIN_TOKEN_KEY=ErWcK75St2CUetMn7pzh8EwzAhn9sHHK54nA
ENV CATALOG_ADMIN_TOKEN_LIFETIME=3600
ENV CATALOG_RECORDS_SOURCE=jobs-manager
ENV CATALOG_STORAGE_SYSTEM=data-sd2e-community
