.PHONY: .test_requirements test cov install dist upload example clean

RM = rm -rf
PYTHON = python3


# ┏━━━━━━━━━┓
# ┃ Testing ┃
# ┗━━━━━━━━━┛

PYTEST = $(PYTHON) setup.py test
PYTEST_COV_OPTS ?= --cov=src --cov-report=term --no-cov-on-fail


test: cleanpy
	$(PYTEST)


cov: cleanpy
	$(PYTEST) --addopts "$(PYTEST_COV_OPTS)"


testclean: cleanpy
	@$(RM) .cache .coverage


# ┏━━━━━━━━━━━━━━━━━━━┓
# ┃ Building, running ┃
# ┗━━━━━━━━━━━━━━━━━━━┛

dist: cleanpy
	$(PYTHON) setup.py sdist


upload: cleanpy
	$(PYTHON) setup.py sdist upload


example: cleanpy
	@echo Starting example server
	@CONFIG_PATH=./examples/running/config.yml python -m datacatalog.main


# ┏━━━━━━━━━━━━━━┓
# ┃ Dependencies ┃
# ┗━━━━━━━━━━━━━━┛

rundeps: cleanpy
	@echo -n 'Installing... '
	@pip3 install --quiet --upgrade --upgrade-strategy eager -e . && echo 'OK' || echo 'FAILED'


testdeps:
	@echo -n 'Installing with test dependencies... '
	@pip3 install --quiet --upgrade --upgrade-strategy eager -e .[test] && echo 'OK' || echo 'FAILED'


alldeps:
	@echo -n 'Installing with all dependencies... '
	@pip3 install --quiet --upgrade --upgrade-strategy eager -e .[dev,docs,test] && echo 'OK' || echo 'FAILED'


# ┏━━━━━━━━━━━━━┓
# ┃ Cleaning up ┃
# ┗━━━━━━━━━━━━━┛

cleanpy:
	@echo Removing pyc and pyo files
	@find . -type f -name '*.py[co]' -exec rm {} \;


clean: cleanpy
	@# From running pytest:
	$(RM) .coverage .cache

	@# From `pip3 install -e .`:
	-pip3 uninstall -y datacatalog-core && $(RM) src/datacatalog_core.egg-info

	@# From `setup.py sdist`:
	$(RM) dist
