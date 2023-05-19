#!/usr/bin/env bash

MASS=${1}
STHETA=${2}
KAP=${3}
OUTDIR=${4}
INDIR=${5}
NEVENTS=${6}

cd ${INDIR}/Singlet_hh_narrow_M250/Singlet_hh_ST${STHETA}_K${KAP}_M${MASS}_gridpack/work/

tar -xavf ${INDIR}/Singlet_hh_ST${STHETA}_K${KAP}_M${MASS}_${SCRAM_ARCH}_${CMSSW_VERSION}_tarball.tar.xz

nprocs=$((`nproc`-1))
seed=${RANDOM}
./runcmsgrid.sh ${NEVENTS} ${seed} ${nprocs}

echo "Run runcmsgrid.sh with ${nevents} events, ${nprocs} cores and seed=${seed}."
       
