#!/bin/sh

CONV=pyuic5

for f in `ls *.ui`
do
	bn=$(basename "${f}" .ui)
	of="${bn}.py"
	${CONV} -o "${of}" "${f}"
	sed -i 's/from PyQt5 import/from pyqtgraph import/' "${of}"
done
