#!/bin/sh

file="$1"
wc=$(cat "$file" | wc -l)
size=$(stat -f '%z' "$file")
echo "$size/$wc" | bc
