#!/usr/bin/env bash

MASS=${1}
STHETA=${2}
KAP=${3}
OUTDIR=${4}
INDIR=${5}
NEVENTS=${6}

cd ${INDIR}/Singlet_hh_ST${STHETA}_K${KAP}_M${MASS}/Singlet_hh_ST${STHETA}_K${KAP}_M${MASS}_gridpack/work/

tar -xavf ${INDIR}/Singlet_hh_ST${STHETA}_K${KAP}_M${MASS}_slc7_amd64_gcc10_CMSSW_12_4_8_tarball.tar.xz

nprocs=`nproc`
seed=${RANDOM}
./runcmsgrid.sh ${NEVENTS} ${seed} ${nprocs}

mv cmsgrid_final.lhe ${OUTDIR}/Singlet_hh_ST${STHETA}_K${KAP}_M${MASS}.lhe

echo "Run runcmsgrid.sh with ${NEVENTS} events, ${nprocs} cores and seed=${seed}."
echo "LHE file stored under '${OUTDIR}/Singlet_hh_ST${STHETA}_K${KAP}_M${MASS}.lhe'."       
