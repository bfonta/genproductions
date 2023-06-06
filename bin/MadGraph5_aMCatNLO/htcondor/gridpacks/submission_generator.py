import os
import argparse
import numpy as np

def ntos(n, around=None):
    """Converts float to string"""
    if around is not None:
        n = np.round(n, around)
    return str(n).replace('.', 'p').replace('-', 'm')

example = 'python generateCards.py --out TestSinglet --template SingletModel/cards_templates/'
parser = argparse.ArgumentParser(description='Plotter for finite width studies.\nExample: {} .'.format(example))
parser.add_argument("--out_dir", required=True, help="Output directory.",)
parser.add_argument("--card_dir", required=True,
                    choices=('Singlet_resonly', 'Singlet_nores', 'Singlet_all'), 
                    help="Datacards subdirectory.",)
parser.add_argument("--server", default='llr', choices=('llr', 'lxplus'),
                    help="Server where the script is running.",)
FLAGS = parser.parse_args()

base_local = 'genproductions/bin/MadGraph5_aMCatNLO/htcondor/gridpacks/'
if FLAGS.server == 'llr':
    base_local = os.path.join('/home/llr/cms/alves/', base_local)
    base_storage = os.path.join('/data_CMS/cms/alves/FiniteWidth/')
elif FLAGS.server == 'lxplus':
    base_local = os.path.join('/afs/cern.ch/work/',
                              os.environ['USER'][0], os.environ['USER'], base_local)
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

# masses = ('250', '260', '270', '280', '300', '320', '350', '400',
#           '450', '500', '550', '600', '650', '700', '750', '800',
#           '850', '900', '1000', '1250', '1500', '1750', '2000', '2500', '3000')    
mass_points = (250, 350, 450, 550, 650, 750, 850, 950)
stheta_points = np.arange(0.,1.1,.2) # sine of theta mixing between the new scalar and the SM Higgs
l112_points = np.arange(-300,301,100) # resonance coupling with two Higgses
k111_points = (1.,) #np.arange(-7,12) # tri-linear kappa

def add_new_line(m, st, lbd, kap, s):
    if not (m==mass_points[-1] and st==stheta_points[-1] and lbd==l112_points[-1] and kap==k111_points[-1]):
        return s + "\n"
    else:
        return s

loop_inside = ''
for st in stheta_points:
    for lbd in l112_points:
        for kap in k111_points:
            for m in mass_points:
                loop_inside += '    ' + ntos(m) + ', ' + ntos(st, 1) + ', ' + ntos(lbd) + ', ' + ntos(kap)
                loop_inside = add_new_line(m, st, lbd, kap, loop_inside)

outfile = "Singlet_hh_ST$(Stheta)_L$(Lambda112)_K$(Kappa111)_M$(Mass)"
m = ( 'universe = vanilla',
      'executable = ' + os.path.join(base_local, 'submission.sh'),
      'arguments  = $(Mass) $(Stheta) $(Lambda112) $(Kappa111) {} {} {}'.format(out_dir, FLAGS.card_dir, FLAGS.server),
      'output     = ' + outfile + '_job.out',
      'error      = ' + outfile + '_job.err',
      #'log        = ' + outfile + '_job.log',
      
      'getenv = true',
      '+JobBatchName = "FW_{}"'.format(FLAGS.out_dir),
      '+JobFlavour   = "microcentury"', # 1 hour (see https://batchdocs.web.cern.ch/local/submit.html)

      'RequestCpus   = 1',
      'RequestMemory = 1GB',
      'RequestDisk   = 512MB',
      
      'queue Mass, Stheta, Lambda112, Kappa111 from (',
      loop_inside,
      ')'
     )

with open(os.path.join(base_local, 'submission_' + FLAGS.out_dir + '.condor'), 'w') as file:
    file.write('\n'.join(m))
