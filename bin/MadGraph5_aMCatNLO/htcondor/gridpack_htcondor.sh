#!/usr/bin/env bash

MASS=${1}
STHETA=${2}
KAP=${3}
OUTDIR=${4}
CARDDIR=${5}

cd /afs/cern.ch/work/${USER:0:1}/${USER}/genproductions/bin/MadGraph5_aMCatNLO

PYTHONPATH=$PYTHONPATH:/usr/lib64/python3.6/site-packages/; \
	./gridpack_generation.sh Singlet_hh_ST${STHETA}_K${KAP}_M${MASS} cards/production/13TeV/${CARDDIR}/Singlet_hh_ST${STHETA}_K${KAP}_M${MASS}/

mv Singlet_hh_ST${STHETA}_K${KAP}_M${MASS} ${OUTDIR}
mv Singlet_hh_ST${STHETA}_K${KAP}_M${MASS}.log ${OUTDIR}
mv Singlet_hh_ST${STHETA}_K${KAP}_M${MASS}_${SCRAM_ARCH}_${CMSSW_VERSION}_tarball.tar.xz ${OUTDIR} 

echo "Done!"
