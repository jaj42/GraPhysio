UIFILES=cycledetect_ui.py mainwindow_ui.py newplot_ui.py periodexport_ui.py

%.py: designer/%.ui
	pyuic4 $< > $@

all: $(UIFILES)
