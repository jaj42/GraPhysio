#!/bin/sh

CONV=pyside6-uic

for f in `ls *.ui`
do
	bn=$(basename "${f}" .ui)
	of="${bn}.py"
	${CONV} -o "${of}" "${f}"
done
