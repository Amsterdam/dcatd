RM            = rm -rf
SPHINXOPTS    = -d .doctrees
SPHINXBUILD   = sphinx-build
AUTOBUILD     = sphinx-autobuild
SOURCEDIR     = .
BUILDDIR      = ../docs

.PHONY = docs server clean invclean

docs:
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)
	touch $(BUILDDIR)/.nojekyll


server:
	@$(AUTOBUILD) "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) --watch ../web


clean:
	@$(RM) $(BUILDDIR) .doctrees


invclean:
	@$(RM) *.inv *.inv.txt
