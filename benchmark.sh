#!/bin/bash

ITERATIONS=1000
TMPFILE=$(mktemp)

echo "Outputting data to $TMPFILE"

for i in $(seq 1 $ITERATIONS); do
    if [[ $(($i % 10)) == "0" ]]; then
        echo "Iteration $i."
    fi
   ./run_loop.sh | wc -l >>$TMPFILE
done

awk '{ total += ($1 - 1) / 2; count++ } END { print total / count }' $TMPFILE
