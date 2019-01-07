TESTS_IMAGE := plan_b-tests:latest
TESTS_IMAGE_APK_DEPENDENCIES := build-base libffi-dev postgresql-dev

test:
	docker build . \
	-t $(TESTS_IMAGE) \
	-f Dockerfile.tests \
	--build-arg TESTS_IMAGE_APK_DEPENDENCIES="$(TESTS_IMAGE_APK_DEPENDENCIES)"

	TESTS_IMAGE=$(TESTS_IMAGE) \
	docker-compose up --abort-on-container-exit

	TESTS_IMAGE=$(TESTS_IMAGE) \
	docker-compose ps -q tests | \
	xargs docker inspect -f '{{ .State.ExitCode }}' | \
	grep -cv "^0$$" | \
	grep -q "^0$$"

develop:
	virtualenv env -p python3.6
	env/bin/pip install -Ue ".[develop]"
