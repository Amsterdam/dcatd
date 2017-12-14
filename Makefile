.PHONY: _test_requirements test cov install dist upload clean

RM = rm -rf
PYTHON = python3
PIP_UPGRADE = pip install --upgrade --upgrade-strategy eager --force-reinstall

# ┏━━━━━━━━━┓
# ┃ Testing ┃
# ┗━━━━━━━━━┛

# `pytest` and `python -m pytest` are equivalent, except that the latter will
# add the current working directory to sys.path. We don't want that; we want
# to test against the _installed_ package(s), not against any python sources
# that are (accidentally) in our CWD.
#PYTEST = pytest --loop uvloop --verbose -p no:cacheprovider --exitfirst --capture=no
PYTEST = pytest --loop uvloop --verbose -p no:cacheprovider --exitfirst

# The ?= operator below assigns only if the variable isn't defined yet. This
# allows the caller to override them:
#
# TESTS_DIR=other_tests make test
#
PYTEST_COV ?= $(PYTEST_OPTS) --cov=src --cov-report=term --no-cov-on-fail
TESTS_DIR ?= tests


# Probably needed again in the future:
#schema:
#	$(MAKE) -C alembic $@


_test_requirements:
	pip install --upgrade --upgrade-strategy eager -e .[test]

test: _test_requirements
	$(PYTEST)               $(TESTS_DIR)

cov: _test_requirements
	$(PYTEST) $(PYTEST_COV) $(TESTS_DIR)


# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ Installing, building, running ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

install:
	pip install --upgrade --upgrade-strategy eager -e .[dev]

dist:
	$(PYTHON) setup.py sdist

upload:
	$(PYTHON) setup.py sdist upload

example:
	@echo -n Installing dependencies...
	@pip install --upgrade --upgrade-strategy eager -e . >/dev/null 2>&1 && echo ' OK' || echo ' FAILED'
	@echo Starting example server:
	@./examples/run.sh


# ┏━━━━━━━━━━━━━┓
# ┃ Cleaning up ┃
# ┗━━━━━━━━━━━━━┛

clean:
	@# From running pytest with coverage:
	$(RM) .coverage

	@# From `pip install -e .`:
	-pip uninstall -y datacatalog-core && $(RM) src/datacatalog_core.egg-info

	@# From `setup.py sdist`:
	$(RM) dist
