.PHONY: .test_requirements test cov install dist upload example clean

RM = rm -rf
PYTHON = python3


# ┏━━━━━━━━━━━┓
# ┃ DB schema ┃
# ┗━━━━━━━━━━━┛

schema schema_jenkins schema_acc:
	$(MAKE) -C alembic $@


# ┏━━━━━━━━━┓
# ┃ Testing ┃
# ┗━━━━━━━━━┛

PYTEST = $(PYTHON) setup.py test
PYTEST_COV_OPTS ?= --cov=src --cov-report=term --no-cov-on-fail


test: schema
	$(PYTEST)


cov: schema
	$(PYTEST) $(PYTEST_COV_OPTS)


testdep:
	pip3 install --quiet --upgrade --upgrade-strategy eager -e .[test] && echo 'OK' || echo 'FAILED'


testclean:
	@$(RM) .cache .coverage


# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ Installing, building, running ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

install:
	@echo -n 'Installing... '
	@pip3 install --quiet --upgrade --upgrade-strategy eager -e . && echo 'OK' || echo 'FAILED'

dist:
	$(PYTHON) setup.py sdist

upload:
	$(PYTHON) setup.py sdist upload

example:
	@echo Starting example server:
	@docker-compose up api


# ┏━━━━━━━━━━━━━┓
# ┃ Cleaning up ┃
# ┗━━━━━━━━━━━━━┛

clean:
	@# From running pytest:
	$(RM) .coverage .cache

	@# From `pip3 install -e .`:
	-pip3 uninstall -y datacatalog-core && $(RM) src/datacatalog_core.egg-info

	@# From `setup.py sdist`:
	$(RM) dist
