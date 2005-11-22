# Documentation builder stuff

HTML = index.html screenshots.html roadmap.html
PRE = README.html
CSS = layout.css colors.css
IMAGES = ooimpress.png ooimpress-matplotlib.png
WEBSITE = $(CSS) $(HTML) $(PRE) $(IMAGES)

# Distribution stuff
TAR = tar
GZIP = gzip -f

PACKAGE := pyemf
VERSION := $(shell grep __version__ $(PACKAGE).py|head -n1|cut -d \" -f 2)

srcdir = .
top_srcdir = .
top_builddir = .

distdir := $(PACKAGE)-$(VERSION)
top_distdir := $(distdir)

DISTFILES = pyemf.py setup.py README LICENSE PyRTF-0.45-EMF-patch.diff matplotlib-0.85-EMF-patch.diff
DISTFILE_TESTS = test-*.py


.SUFFIXES:      .html.in .pre.in .html

.html.in.html: template.html.in mainmenu.html.in
	./Makedoc.py -o $*.html -n mainMenu mainmenu.html.in -n htmlBody $*.html.in -t template.html.in

.pre.in.html: template.html.in mainmenu.html.in
	./Makedoc.py -o $*.html -n mainMenu mainmenu.html.in -n preBody $*.pre.in -t template.html.in





all: html doc api

api/index.html: pyemf.py
	epydoc -o api --no-private -u 'http://pyemf.sourceforge.net' pyemf.py

README: README.pre.in
	./Makedoc.py -o README README.pre.in

index.html: index.html.in template.html.in mainmenu.html.in

screenshots.html: screenshots.html.in template.html.in mainmenu.html.in

roadmap.html: roadmap.html.in template.html.in mainmenu.html.in

README.html: README.pre.in template.html.in mainmenu.html.in




doc: README

html: $(HTML) $(PRE)

publish_html: html
	rsync -avuz $(WEBSITE) robm@pyemf.sourceforge.net:/home/groups/p/py/pyemf/htdocs

api: api/index.html

publish_api: api
	rsync -avuz api robm@pyemf.sourceforge.net:/home/groups/p/py/pyemf/htdocs

publish: publish_api publish_html


release: dist
	-mkdir -p archive
	cp $(distdir).tar.gz archive

dist: distdir
	-chmod -R a+r $(distdir)
	$(TAR) cvf $(distdir).tar $(distdir)
	$(GZIP) $(distdir).tar
	-rm -rf $(distdir)

distdir: $(DISTFILES)
	-rm -rf $(distdir)
	mkdir $(distdir)
	-chmod 777 $(distdir)
	distdir=`cd $(distdir) && pwd`
	@for file in $(DISTFILES); do \
	  d=$(srcdir); \
	  if test -d $$d/$$file; then \
	    cp -pr $$d/$$file $(distdir)/$$file; \
	  else \
	    test -f $(distdir)/$$file \
	    || ln $$d/$$file $(distdir)/$$file 2> /dev/null \
	    || cp -p $$d/$$file $(distdir)/$$file || :; \
	  fi; \
	done
	mkdir $(distdir)/website
	cp $(WEBSITE) $(distdir)/website
	epydoc -o $(distdir)/website/api --no-private -u '../index.html' pyemf.py
	mkdir $(distdir)/examples
	cp $(DISTFILE_TESTS) $(distdir)/examples




clean:
	rm -rf *~ *.o *.exe build api README README.html index.html screenshots.html $(distdir)

.PHONY: print-% clean html publish_html api publish_api publish release dist distdir

print-%: ; @ echo $* = $($*)

