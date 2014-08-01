#!/usr/bin/env bash

DATADIR=/home/rayder441/sandbox/data/mt/ptm/uist14/full
#DRYRUN=--dry-run
DRYRUN=

# Fr-En setup
FREN=$DATADIR/fren/analysis/translations/appraise
for file in $(ls $FREN/block*_*hits); do
    echo $file
    python import_wmt14_xml.py $DRYRUN $file
done

# En-De setup
ENDE=$DATADIR/ende/analysis/translations/appraise
for file in $(ls $ENDE/block*_*hits); do
    echo $file
    python import_wmt14_xml.py $DRYRUN $file
done

