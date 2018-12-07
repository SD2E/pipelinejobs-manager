CONTAINER_IMAGE=$(shell bash scripts/container_image.sh)
PYTHON ?= "python3"
PYTEST_OPTS ?= ""
PYTEST_DIR ?= "tests"
ABACO_DEPLOY_OPTS ?= "-p"
SCRIPT_DIR ?= "scripts"
PREF_SHELL ?= "bash"
ACTOR_ID ?=
GITREF=$(shell git rev-parse --short HEAD)

TEST_JOB_UUID ?= "10766b61-49f0-524d-a17f-f4bd42bdfce7"
TEST_JOB_TOKEN ?= "c2f338f3e79e4f86"
TEST_JOB_STATUS ?= "RUNNING"
DOCKER_NETWORK ?= --network docker_mongotest

.PHONY: tests container tests-local tests-reactor tests-deployed datacatalog formats
.SILENT: tests container tests-local tests-reactor tests-deployed datacatalog formats

all: image

datacatalog: formats
	if [ -d ../python-datacatalog ]; then rm -rf python-datacatalog; cp -R ../python-datacatalog .; fi

image:
	abaco deploy -R -t $(GITREF) $(ABACO_DEPLOY_OPTS)

shell:
	bash $(SCRIPT_DIR)/run_container_process.sh bash

init: init-pipeline init-job

init-pipeline:
	python3 tests/install_pipeline.py --filename tests/data/pipeline02.json

init-job:
	python3 tests/install_job.py --filename tests/data/1-local-create-tacobot.json

tests: tests-pytest tests-local

tests-integration:
	true

tests-pytest:
	bash $(SCRIPT_DIR)/run_container_process.sh $(PYTHON) -m "pytest" $(PYTEST_DIR) $(PYTEST_OPTS)

tests-local: tests-local-callback

tests-local-callback: tests-local-callback-run-finish tests-local-callback-run-fail

tests-local-callback-run-finish: init tests-local-callback-run tests-local-callback-finish
tests-local-callback-run-fail: init tests-local-callback-run tests-local-callback-fail

tests-local-callback-run:
	DOCKER_ENVS_SET="${DOCKER_NETWORK} -e status=$(TEST_JOB_STATUS) -e uuid=$(TEST_JOB_UUID) -e token=$(TEST_JOB_TOKEN)" bash $(SCRIPT_DIR)/run_container_message.sh tests/data/2-local-event-tacobot-agave-running.json

tests-local-callback-finish:
	DOCKER_ENVS_SET="${DOCKER_NETWORK} -e status=$(TEST_JOB_STATUS) -e uuid=$(TEST_JOB_UUID) -e token=$(TEST_JOB_TOKEN)" bash $(SCRIPT_DIR)/run_container_message.sh tests/data/2-local-event-tacobot-agave-finished.json

tests-local-callback-fail:
	DOCKER_ENVS_SET="${DOCKER_NETWORK} -e status=$(TEST_JOB_STATUS) -e uuid=$(TEST_JOB_UUID) -e token=$(TEST_JOB_TOKEN)" bash $(SCRIPT_DIR)/run_container_message.sh tests/data/2-local-event-tacobot-agave-failed.json

tests-local-event: tests-local-event-create tests-local-event-run tests-local-event-finish

tests-local-event-create:
	bash $(SCRIPT_DIR)/run_container_message.sh tests/data/1-local-create-tacobot.json

tests-local-event-run:
	bash $(SCRIPT_DIR)/run_container_message.sh tests/data/2-local-event-tacobot-run.json

tests-local-event-fail:
	bash $(SCRIPT_DIR)/run_container_message.sh tests/data/3-local-event-tacobot-fail.json

tests-local-event-finish:
	bash $(SCRIPT_DIR)/run_container_message.sh tests/data/3-local-event-tacobot-finish.json

tests-local-action-delete:
	bash $(SCRIPT_DIR)/run_container_message.sh tests/data/4-local-event-tacobot-delete.json

tests-local-action-force-delete:
	bash $(SCRIPT_DIR)/run_container_message.sh tests/data/5-local-event-tacobot-force-delete.json

tests-deployed:
	echo "not implemented"

clean: clean-image clean-tests

clean-image:
	docker rmi -f $(CONTAINER_IMAGE)

clean-tests:
	rm -rf .hypothesis .pytest_cache __pycache__ */__pycache__ tmp.* *junit.xml

deploy:
	abaco deploy -t $(GITREF) $(ABACO_DEPLOY_OPTS) -U $(ACTOR_ID)

postdeploy:
	bash tests/run_after_deploy.sh

nonce:
	bash scripts/nonces-new.sh

nonces:
	bash scripts/nonces-list.sh
