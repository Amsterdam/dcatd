.PHONY: schema test cov testclean distclean clean

RM = rm -rf

# `pytest` and `python -m pytest` are equivalent, except that the latter will
# add the current working directory to sys.path. We don't want that; we want
# to test against the _installed_ package(s), not against any python sources
# that are (accidentally) in our CWD.
#PYTEST = pytest --loop uvloop --verbose -p no:cacheprovider --exitfirst --capture=no
PYTEST = pytest --loop uvloop --verbose -p no:cacheprovider --exitfirst

# The ?= operator below assigns only if the variable isn't defined yet. This
# allows the caller to override them:
#
#     TESTS_DIR=other_tests make test
#
PYTEST_COV ?= $(PYTEST_OPTS) --cov=src --cov-report=term --no-cov-on-fail
TESTS_DIR ?= tests


# Probably needed again in the future:
#schema:
#	$(MAKE) -C alembic $@


test:
	$(PYTEST) $(PYTEST_OPTS)     $(TESTS_DIR)


cov:
	$(PYTEST) $(PYTEST_COV_OPTS) $(TESTS_DIR)


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
