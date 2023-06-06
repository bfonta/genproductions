#!/usr/bin/env bash

MASS=${1}
STHETA=${2}
LAMBDA112=${3}
KAPPA111=${4}
OUTDIR=${5}
CARDDIR=${6}
SERVER=${7}

if [[ ${SERVER} == "llr" ]]; then
	BASE="/home/llr/cms/alves/genproductions/bin/MadGraph5_aMCatNLO"
	STORAGE="/data_CMS/llr/cms/alves/FiniteWidth/"
elif [[ ${SERVER} == "lxplus" ]]; then
	BASE="/afs/cern.ch/work/${USER:0:1}/${USER}/genproductions/bin/MadGraph5_aMCatNLO"
	STORAGE="/eos/user/${USER:0:1}/${USER}/FiniteWidth/"
else
	echo "Server error."
	exit 1
fi

PARS="ST${STHETA}_L${LAMBDA112}_K${KAPPA111}_M${MASS}"
NAME="Singlet_hh_${PARS}"

JOBDIR=${PWD}

cd ${BASE}

PYTHONPATH=$PYTHONPATH:/usr/lib64/python3.6/site-packages/; \
	./gridpack_generation.sh ${NAME} cards/production/13TeV/${CARDDIR}/${NAME}/ ${JOBDIR} ${SERVER}

# mv ${STORAGE}/${NAME} ${OUTDIR}
# mv ${NAME}.log ${OUTDIR}
# mv ${NAME}_slc7_amd64_gcc10_CMSSW_12_4_8_tarball.tar.xz ${OUTDIR} 

# mv ${JOBDIR}/"${NAME}_job.err" ${OUTDIR}/${NAME}
# mv ${JOBDIR}/"${NAME}_job.out" ${OUTDIR}/${NAME}
# mv ${JOBDIR}/"${NAME}.log" ${OUTDIR}/${NAME}

echo "Done!"
