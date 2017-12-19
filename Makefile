.PHONY: .test_requirements test cov install dist upload clean

RM = rm -rf
PYTHON = python3
PIP_UPGRADE = pip3 install --upgrade --upgrade-strategy eager --force-reinstall

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


testdep:
	pip3 install --quiet --upgrade --upgrade-strategy eager -e .[test] && echo 'OK' || echo 'FAILED'

test:
	CONFIG_PATH=$(TESTS_DIR)/config.yml $(PYTEST)               $(TESTS_DIR)

testcov:
	CONFIG_PATH=$(TESTS_DIR)/config.yml $(PYTEST) $(PYTEST_COV) $(TESTS_DIR)


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

example: install
	@echo Starting example server:
	@./examples/run.sh


# ┏━━━━━━━━━━━━━┓
# ┃ Cleaning up ┃
# ┗━━━━━━━━━━━━━┛

clean:
	@# From running pytest with coverage:
	$(RM) .coverage

	@# From `pip3 install -e .`:
	-pip3 uninstall -y datacatalog-core && $(RM) src/datacatalog_core.egg-info

	@# From `setup.py sdist`:
	$(RM) dist
