#!/bin/sh

CONV=pyuic6

for f in `ls *.ui`
do
	bn=$(basename "${f}" .ui)
	of="${bn}.py"
	${CONV} -o "${of}" "${f}"
	sed -i 's/from PyQt6 import/from pyqtgraph import/' "${of}"
done
