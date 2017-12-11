.PHONY: build run test jenkinstest cov testclean distclean clean

RM = rm -rf

# `pytest` and `python -m pytest` are equivalent, except that the latter will
# add the current working directory to sys.path. We don't want that; we want
# to test against the _installed_ package(s), not against any python sources
# that are (accidentally) in our CWD.
PYTEST = pytest

# The ?= operator below assigns only if the variable isn't defined yet. This
# allows the caller to override them::
#
#     TESTS=other_tests make test
#
#PYTEST_OPTS ?= --loop uvloop -p no:cacheprovider --verbose --exitfirst --capture=no --cov=src --cov-report=term --no-cov-on-fail
PYTEST_OPTS ?= --loop uvloop -p no:cacheprovider --verbose --exitfirst
PYTEST_COV_OPTS ?= --loop uvloop -p no:cacheprovider --verbose --cov=src --cov-report=term --no-cov-on-fail
TESTS ?= tests

YAML2JSON = python -c 'import json, sys, yaml; json.dump(yaml.load(sys.stdin), sys.stdout, indent="  ")'
JSON2YAML = python -c 'import json, sys, yaml; yaml.dump(json.load(sys.stdin), sys.stdout, default_flow_style=False)'
CONFIG = 'config'
SCHEMA = 'web/datacatalog/config_schema'

json:
	$(YAML2JSON) <$(CONFIG).yml >$(CONFIG).json
	$(YAML2JSON) <$(SCHEMA).yml >$(SCHEMA).json

yaml:
	$(JSON2YAML) <$(CONFIG).json >$(CONFIG).yml
	$(JSON2YAML) <$(SCHEMA).json >$(SCHEMA).yml

run:
	cp -af $(OPENAPI_PATH) \
	       swagger-ui/dist/openapi.yml && \
	authz_admin


schema schema_jenkins schema_acc:
	$(MAKE) -C alembic $@


test: schema
	$(PYTEST) $(PYTEST_OPTS) $(TESTS)


jenkinstest: schema_jenkins
	$(PYTEST) $(PYTEST_OPTS) $(TESTS)


cov: schema
	$(PYTEST) $(PYTEST_COV_OPTS) $(TESTS)


testclean:
	@$(RM) .cache .coverage


# @evert waar komt dit eigenlijk vandaan? [--PvB]
distclean:
	@$(RM) \
		dist/ \
		bin/ \
		develop-eggs/ \
		eggs/ \
		parts/ \
		MANIFEST \
		htmlcov/ \
		.installed.cfg

clean: testclean distclean
	@$(RM) build *.egg-info .eggs dist
	@find . -not -path "./.venv/*" -and \( \
		-name "*.pyc" -or \
		-name "__pycache__" -or \
		-name "*.pyo" -or \
		-name "*.so" -or \
		-name "*.o" -or \
		-name "*~" -or \
		-name "._*" -or \
		-name "*.swp" -or \
		-name "Desktop.ini" -or \
		-name "Thumbs.db" -or \
		-name "__MACOSX__" -or \
		-name ".DS_Store" \
	\) -delete
