#!/usr/bin/env bash

MASS=${1}
STHETA=${2}
LAMBDA112=${3}
KAPPA111=${4}
OUTDIR=${5}
CARDDIR=${6}

NAME=Singlet_hh_ST${STHETA}_L${LAMBDA112}_K${KAPPA111}_M${MASS}

cd /afs/cern.ch/work/${USER:0:1}/${USER}/genproductions/bin/MadGraph5_aMCatNLO

PYTHONPATH=$PYTHONPATH:/usr/lib64/python3.6/site-packages/; \
	./gridpack_generation.sh ${NAME} cards/production/13TeV/${CARDDIR}/${NAME}/

mv ${NAME} ${OUTDIR}
mv ${NAME}.log ${OUTDIR}
mv ${NAME}_slc7_amd64_gcc10_CMSSW_12_4_8_tarball.tar.xz ${OUTDIR} 

echo "Done!"
