.PHONY: .test_requirements test cov install dist upload example clean

RM = rm -rf
PYTHON = python3
PIP_UPGRADE = pip3 install --upgrade --upgrade-strategy eager --force-reinstall

# ┏━━━━━━━━━┓
# ┃ Testing ┃
# ┗━━━━━━━━━┛

PYTEST = pytest

# The ?= operator below assigns only if the variable isn't defined yet. This
# allows the caller to override them:
#
# PYTEST='./setup.py test' make test
#
PYTEST_COV ?= --cov=src --cov-report=term --no-cov-on-fail


# Probably needed again in the future:
#schema:
#	$(MAKE) -C alembic $@


testdep:
	pip3 install --quiet --upgrade --upgrade-strategy eager -e .[test] && echo 'OK' || echo 'FAILED'

test:
	$(PYTEST)

testcov:
	$(PYTEST) $(PYTEST_COV)


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
	@./examples/run.sh


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
