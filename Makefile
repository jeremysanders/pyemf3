# Documentation builder stuff

HTML = index.html screenshots.html roadmap.html
PRE = README.html
CSS = layout.css colors.css
IMAGES = ooimpress.png ooimpress-matplotlib.png


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
	rsync -avuz $(CSS) $(HTML) $(PRE) $(IMAGES) api robm@pyemf.sourceforge.net:/home/groups/p/py/pyemf/htdocs




clean:
	rm -rf *~ *.o *.exe build api README README.html index.html screenshots.html

.PHONY: print-% clean install_html html doc

print-%: ; @ echo $* = $($*)

