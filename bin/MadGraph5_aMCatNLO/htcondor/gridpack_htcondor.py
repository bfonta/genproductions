import os
import argparse

parser = argparse.ArgumentParser(description='Plotter for finite width studies.')
parser.add_argument("--out_dir", required=True, help="Output directory.",)
parser.add_argument("--card_dir", required=True, choices=('Singlet_resonly', 'Singlet_nores'), 
                    help="Datacards subdirectory.",)
FLAGS = parser.parse_args()

base_dir = os.path.join('/afs/cern.ch/work/', os.environ['USER'][0], os.environ['USER'],
                        'genproductions/bin/MadGraph5_aMCatNLO/')
condor_dir = os.path.join(base_dir, 'htcondor/')
condor_out = os.path.join(condor_dir, 'out_gridpack_{}/'.format(FLAGS.out_dir))
out_dir = os.path.join(base_dir, FLAGS.out_dir + '/')

for d in (out_dir, condor_out):
    if not os.path.exists(d):
        os.makedirs(d)
    else:
        mes = 'Folder {} already exists!\n'.format(d)
        mes += 'Deletion command: rm -r {}\n'.format(d)
        raise RuntimeError(mes)
            
endl = "\n"
outfile = "ST$(Stheta)_K$(Kappa)_M$(Mass)"

# masses = ('250', '260', '270', '280', '300', '320', '350', '400',
#           '450', '500', '550', '600', '650', '700', '750', '800',
#           '850', '900', '1000', '1250', '1500', '1750', '2000', '2500', '3000')
masses = ('250',)
sthetas = (0.2, 0.5, 0.8)
kaps = (1., 2., 3.)

loop_inside = ''
for st in sthetas:
    ststr = str(st).replace('.', 'p')
    for kap in kaps:
        kstr = str(kap).replace('.', 'p')
        for m in masses:
            mstr = str(m)
            loop_inside += '    ' + mstr + ', ' + ststr + ', ' + kstr
            if not (m==masses[-1] and kap==kaps[-1] and st==sthetas[-1]):
                loop_inside += endl

m = ( 'universe = vanilla',
      'executable = ' + os.path.join(condor_dir, 'gridpack_htcondor.sh'),
      'arguments  = $(Mass) $(Stheta) $(Kappa) {} {}'.format(out_dir, FLAGS.card_dir),
      'output     = ' + condor_out + outfile + '.out',
      'error      = ' + condor_out + outfile + '.err',
      'log        = ' + condor_out + outfile + '.log',
      
      'getenv = true',
      '+JobBatchName ="FW_{}"'.format(FLAGS.out_dir),
      '+JobFlavour   = "longlunch"', # 2 hours (see https://batchdocs.web.cern.ch/local/submit.html)
      'RequestCpus   = 1',
      
      'queue Mass, Stheta, Kappa from (',
      loop_inside,
      ')'
     )

with open(os.path.join(condor_dir, 'gridpack_htcondor_' + FLAGS.out_dir + '.condor'), 'w') as file:
    file.write('\n'.join(m))
