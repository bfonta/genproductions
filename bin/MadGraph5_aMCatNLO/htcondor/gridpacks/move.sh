#!/usr/bin/env bash

OUTDIR=${1}
TAG=${2}
NAME=${3}

BASE="/afs/cern.ch/work/${USER:0:1}/${USER}/genproductions/bin/MadGraph5_aMCatNLO"

mv ${BASE}/${NAME}/ ${OUTDIR}
mv ${NAME}_slc7_amd64_gcc10_CMSSW_12_4_8_tarball.tar.xz ${OUTDIR} 
mv ${NAME}.err ${OUTDIR}
mv ${NAME}.out ${OUTDIR}
mv ${NAME}.log ${OUTDIR}

echo "DAGMAN Post-script finished!"
