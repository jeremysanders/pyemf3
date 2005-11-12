all: html

api/index.html: pyemf.py
	epydoc -o api -u 'http://pyemf.sourceforge.net' pyemf.py

README:
	./Makedoc.py README.in

index.html: index.html.in template.html.in mainmenu.html.in
	./Makedoc.py -o index.html -n mainMenu mainmenu.html.in -n htmlBody index.html.in -t template.html.in

screenshots.html: screenshots.html.in template.html.in mainmenu.html.in
	./Makedoc.py -o screenshots.html -n mainMenu mainmenu.html.in -n htmlBody screenshots.html.in -t template.html.in

README.html: README.in template.html.in mainmenu.html.in
	./Makedoc.py -o README.html -n mainMenu mainmenu.html.in -n preBody README.in -t template.html.in

html: api/index.html index.html screenshots.html README.html

install_html: html
	rsync -avuz layout.css colors.css index.html screenshots.html README.html ooimpress.png ooimpress-matplotlib.png api robm@pyemf.sourceforge.net:/home/groups/p/py/pyemf/htdocs

clean:
	rm -rf *~ *.o *.exe build api README README.html index.html screenshots.html

.PHONY: print-%
print-%: ; @ echo $* = $($*)

