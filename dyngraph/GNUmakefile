UIFILES=mainwindow_ui.py newplot_ui.py physiodbexport_ui.py

%_ui.py: designer/%.ui
	pyuic4 $< > $@

all: $(UIFILES)
