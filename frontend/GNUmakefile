UIFILES=mainwindow_ui.py newplot_ui.py

%_ui.py: designer/%.ui
	pyuic4 $< > $@

all: $(UIFILES)
