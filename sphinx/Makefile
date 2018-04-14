.PHONY: docs server clean invclean gh-pages

RM            := rm -rf
SPHINXOPTS    := -d .doctrees
SPHINXBUILD   := sphinx-build
SPHINXAPIDOC  := sphinx-apidoc
AUTOBUILD     := sphinx-autobuild
SOURCEDIR     := .
BUILDDIR      := ../docs
GITORIGIN     = "$$(git remote show -n origin | grep 'Fetch URL:' | grep -o 'git@.*')"
GITBRANCH     = "$$(git branch | grep '^\* ' | sed 's/^\* //')"


apidoc:
	$(SPHINXAPIDOC) --force --module-first --no-toc --private -o "$(SOURCEDIR)/apidoc" ../src/datacatalog


docs: apidoc
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)
	touch $(BUILDDIR)/.nojekyll

server: apidoc
	@$(AUTOBUILD) "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) --watch ../src --watch ./


clean:
	@$(RM) $(BUILDDIR) .doctrees apidoc


invclean:
	@$(RM) *.inv *.inv.txt


gh-pages: docs
	[ -d gh-pages ] || git clone --branch gh-pages --single-branch $(GITORIGIN) gh-pages
	cd gh-pages && { [ "`echo *`" = '*' ] || git rm -rf *; }
	cd ../docs && cp -a * ../sphinx/gh-pages
	cd gh-pages && \
	  git add * && \
	  git commit -m 'Update from branch $(GITBRANCH)' && \
	  git push
