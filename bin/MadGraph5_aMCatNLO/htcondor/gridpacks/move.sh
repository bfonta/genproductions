#!/bin/sh 

OUTDIR=${1}
TAG=${2}
NAME=${3}

BASE="/afs/cern.ch/work/${USER:0:1}/${USER}/genproductions/bin/MadGraph5_aMCatNLO"

mkdir -p ${OUTDIR}

# mv ${BASE}/${NAME}/ ${OUTDIR}
# find ${BASE}/${NAME}/ -name "*" -delete

mv ${BASE}/${NAME}_slc7_amd64_gcc10_CMSSW_12_4_8_tarball.tar.xz ${OUTDIR} 
# rm -r ${BASE}/${NAME}_slc7_amd64_gcc10_CMSSW_12_4_8_tarball.tar.xz

mv ${BASE}/${NAME}.err ${OUTDIR}
mv ${BASE}/${NAME}.out ${OUTDIR}
mv ${BASE}/${NAME}.log ${OUTDIR}

# Cannot move its own stderr/out files...
# mv ${BASE}/${NAME}_child.err ${OUTDIR}
# mv ${BASE}/${NAME}_child.out ${OUTDIR}

echo "DAGMAN Post-script finished!"
