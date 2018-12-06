CONTAINER_IMAGE=$(shell bash scripts/container_image.sh)
PYTHON ?= "python3"
PYTEST_OPTS ?= "-s -vvv"
PYTEST_DIR ?= "tests"
ABACO_DEPLOY_OPTS ?= "-p"
SCRIPT_DIR ?= "scripts"
PREF_SHELL ?= "bash"
ACTOR_ID ?=
GITREF=$(shell git rev-parse --short HEAD)

TEST_JOB_UUID ?= "1073f4ff-c2b9-5190-bd9a-e6a406d9796a"
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

tests: tests-pytest tests-local

tests-integration:
	true

tests-pytest:
	bash $(SCRIPT_DIR)/run_container_process.sh $(PYTHON) -m "pytest" $(PYTEST_DIR) $(PYTEST_OPTS)

tests-local: tests-local-create tests-local-run tests-local-agave-run tests-local-finish tests-local-delete tests-local-force-delete

tests-local-create:
	bash $(SCRIPT_DIR)/run_container_message.sh tests/data/1-local-create-tacobot.json

tests-local-run:
	bash $(SCRIPT_DIR)/run_container_message.sh tests/data/2-local-event-tacobot-run.json

tests-local-fail:
	bash $(SCRIPT_DIR)/run_container_message.sh tests/data/3-local-event-tacobot-fail.json

tests-local-callback:
	DOCKER_ENVS_SET="${DOCKER_NETWORK} -e status=$(TEST_JOB_STATUS) -e uuid=$(TEST_JOB_UUID) -e token=$(TEST_JOB_TOKEN)" bash $(SCRIPT_DIR)/run_container_message.sh tests/data/2-local-event-tacobot-agave-update.json

tests-local-finish:
	bash $(SCRIPT_DIR)/run_container_message.sh tests/data/3-local-event-tacobot-finish.json

tests-local-delete:
	bash $(SCRIPT_DIR)/run_container_message.sh tests/data/4-local-event-tacobot-delete.json

tests-local-force-delete:
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
