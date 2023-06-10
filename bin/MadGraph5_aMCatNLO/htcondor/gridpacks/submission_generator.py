import os
import argparse
import numpy as np

def ntos(n, around=None):
    """Converts float to string"""
    if around is not None:
        n = np.round(n, around)
    return str(n).replace('.', 'p').replace('-', 'm')

example = 'python generateCards.py --out TestSinglet --template SingletModel/cards_templates/ --tag FullScanV1'
parser = argparse.ArgumentParser(description='Plotter for finite width studies.\nExample: {} .'.format(example))
parser.add_argument("--out_dir", required=True, help="Output directory.",)
parser.add_argument("--tag", required=True, help="Identifier. Needs to match the datacards' tag.")
parser.add_argument("--card_dir", required=True,
                    choices=('Singlet_resonly', 'Singlet_nores', 'Singlet_all'), 
                    help="Datacards subdirectory.",)
FLAGS = parser.parse_args()

base_local = os.path.join('/afs/cern.ch/work/',
                          os.environ['USER'][0], os.environ['USER'],
                          'genproductions/bin/MadGraph5_aMCatNLO/htcondor/gridpacks/')
base_storage = os.path.join('/eos/user/',
                            os.environ['USER'][0], os.environ['USER'], 'FiniteWidth')

out_dir = os.path.join(base_storage, FLAGS.out_dir + '/')

for d in (out_dir,):
    if not os.path.exists(d):
        os.makedirs(d)
    else:
        mes = 'Folder {} already exists!\n'.format(d)
        mes += 'Deletion command: rm -r {}\n'.format(d)
        raise RuntimeError(mes)

# masses = ('250', '270', '300', '350', '400',
#           '450', '500', '600', '700', '800', '900', '1000')
masses = ('250',)
sthetas = np.arange(0.,1.0001,.5) # sine of theta mixing between the new scalar and the SM Higgs
lambdas = np.arange(-300,301,300) # resonance coupling with two Higgses
kappas = (1.0,)# 2.4, 10.0)

def add_new_line(m, st, lbd, kap, s):
    if not (m==masses[-1] and st==sthetas[-1] and lbd==lambdas[-1] and kap==kappas[-1]):
        return s + "\n"
    else:
        return s

loop_inside = ''
for st in sthetas:
    for lbd in lambdas:
        for kap in kappas:
            for m in masses:
                loop_inside += '    ' + ntos(m) + ', ' + ntos(st, 1) + ', ' + ntos(lbd) + ', ' + ntos(kap)
                loop_inside = add_new_line(m, st, lbd, kap, loop_inside)

outfile = "Singlet_" + FLAGS.tag + "_M$(Mass)_ST$(Stheta)_L$(Lambda112)_K$(Kappa111)"
m = ( 'universe = vanilla',
      'executable = ' + os.path.join(base_local, 'submission.sh'),
      'arguments  = $(Mass) $(Stheta) $(Lambda112) $(Kappa111) {} {}'.format(out_dir, FLAGS.card_dir),
      'output     = ' + outfile + '_job.out',
      'error      = ' + outfile + '_job.err',
      #'log        = ' + outfile + '_job.log',
      
      'getenv = true',
      '+JobBatchName = "FW_{}"'.format(FLAGS.out_dir),
      '+JobFlavour   = "microcentury"', # 1 hour (see https://batchdocs.web.cern.ch/local/submit.html)

      'RequestCpus   = 1',
      'RequestMemory = 4GB',
      'RequestDisk   = 2GB',

      'max_materialize = 50',
      
      'queue Mass, Stheta, Lambda112, Kappa111 from (',
      loop_inside,
      ')'
     )

with open(os.path.join(base_local, 'submission_' + FLAGS.out_dir + '.condor'), 'w') as file:
    file.write('\n'.join(m))
