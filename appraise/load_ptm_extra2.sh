#!/usr/bin/env bash

DATADIR=/home/rayder441/sandbox/data/mt/ptm/uist14/full
#DRYRUN=--dry-run
DRYRUN=

# Fr-En setup
ENDE=$DATADIR/ende/analysis/translations/appraise
for file in $(ls $ENDE/*extra.hits); do
    echo $file
    python import_wmt14_xml.py $DRYRUN $file
done


