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
VERSION := $(shell grep __version__ pyemf.py|head -n1|cut -d \" -f 2)

srcdir = .
top_srcdir = .
top_builddir = .

distdir := $(PACKAGE)-$(VERSION)
top_distdir := $(distdir)

DISTFILES = pyemf.py setup.py README LICENSE
DISTFILE_TESTS = test?.py


.SUFFIXES:      .html.in .pre.in .html

.html.in.html: template.html.in mainmenu.html.in
	./Makedoc.py -o $*.html -n mainMenu mainmenu.html.in -n htmlBody $*.html.in -t template.html.in

.pre.in.html: template.html.in mainmenu.html.in
	./Makedoc.py -o $*.html -n mainMenu mainmenu.html.in -n preBody $*.pre.in -t template.html.in





all: html doc

api/index.html: pyemf.py
	epydoc -o api -u 'http://pyemf.sourceforge.net' pyemf.py

README: README.pre.in
	./Makedoc.py -o README README.pre.in

index.html: index.html.in template.html.in mainmenu.html.in

screenshots.html: screenshots.html.in template.html.in mainmenu.html.in

roadmap.html: roadmap.html.in template.html.in mainmenu.html.in

README.html: README.pre.in template.html.in mainmenu.html.in




doc: README

html: api/index.html $(HTML) $(PRE)

install_html: html
	rsync -avuz $(WEBSITE) api robm@pyemf.sourceforge.net:/home/groups/p/py/pyemf/htdocs




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
	cp -r api $(distdir)/website
	mkdir $(distdir)/examples
	cp $(DISTFILE_TESTS) $(distdir)/examples




clean:
	rm -rf *~ *.o *.exe build api README README.html index.html screenshots.html $(distdir)

.PHONY: print-% clean install_html html doc

print-%: ; @ echo $* = $($*)

