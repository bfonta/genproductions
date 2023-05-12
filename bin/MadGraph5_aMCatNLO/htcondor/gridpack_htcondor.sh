#!/usr/bin/env bash

WIDTH=${1}
MASS=${2}
OUTDIR=${3}
CARDDIR=${4}

cd /afs/cern.ch/work/${USER:0:1}/${USER}/genproductions/bin/MadGraph5_aMCatNLO

PYTHONPATH=$PYTHONPATH:/usr/lib64/python3.6/site-packages/; \
	./gridpack_generation.sh Singlet_hh_${WIDTH}_M${MASS} cards/production/13TeV/${CARDDIR}/Singlet_hh_${WIDTH}_M${MASS}/

mv Singlet_hh_${WIDTH}_M${MASS} ${OUTDIR}
mv Singlet_hh_${WIDTH}_M${MASS}.log ${OUTDIR}
