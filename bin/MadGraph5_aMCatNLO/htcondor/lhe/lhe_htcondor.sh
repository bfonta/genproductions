#!/usr/bin/env bash

MASS=${1}
STHETA=${2}
LAMBDA=${3}
KAPPA=${4}
MODE=${5}
INDIR=${6}
NEVENTS=${7}

NAME="Singlet_TManual_${MODE}_M${MASS}_ST${STHETA}_L${LAMBDA}_K${KAPPA}"
cd ${INDIR}/
echo "Moving to folder ${INDIR}."

UNTARDIR=${NAME}_untar
if [ ! -d ${UNTARDIR} ]; then
	mkdir ${UNTARDIR}
	mv ${NAME}_slc7_amd64_gcc10_CMSSW_12_4_8_tarball.tar.xz ${UNTARDIR}
fi
cd ${UNTARDIR}

# TARNAME="${NAME}_slc7_amd64_gcc10_CMSSW_12_4_8_tarball.tar.xz"
# tar -xavf ${TARNAME}

nprocs=8
seed=${RANDOM}
./runcmsgrid.sh ${NEVENTS} ${seed} ${nprocs}

LHENAME="${NAME}_cmsgrid_final.lhe"
mv cmsgrid_final.lhe ${LHENAME}

echo "Run runcmsgrid.sh with ${NEVENTS} events, ${nprocs} cores and seed=${seed}."
echo "LHE file stored under '${INDIR}/${UNTARDIR}/${LHENAME}'."
