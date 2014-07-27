#!/usr/bin/env bash

DATADIR=/home/rayder441/sandbox/data/mt/ptm/uist14/full
#DRYRUN=--dry-run
DRYRUN=

# Fr-En setup
FREN=$DATADIR/fren/analysis/translations/appraise
python import_wmt14_xml.py $DRYRUN $FREN/block0.hits
python import_wmt14_xml.py $DRYRUN $FREN/block1.hits
python import_wmt14_xml.py $DRYRUN $FREN/block2.hits

if [ -z "$DRYRUN" ]; then
    echo "Creating invites"
    python create_wmt14_invites.py -block 0 fra2eng 3 2>&1 > fren.invites.txt
fi

# En-De setup
ENDE=$DATADIR/ende/analysis/translations/appraise
python import_wmt14_xml.py $DRYRUN $ENDE/block0.hits
python import_wmt14_xml.py $DRYRUN $ENDE/block1.hits
python import_wmt14_xml.py $DRYRUN $ENDE/block2.hits

if [ -z "$DRYRUN" ]; then
    echo Creating invites
    python create_wmt14_invites.py -block 0 eng2deu 3 2>&1 > ende.invites.txt
fi