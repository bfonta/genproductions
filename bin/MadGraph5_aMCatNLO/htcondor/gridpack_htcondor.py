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
out_dir = os.path.join(base_dir, FLAGS.out_dir + '/')

if not os.path.exists(out_dir):
    os.makedirs(out_dir)
else:
    mes = 'Folder {} already exists!'.format(out_dir)
    raise RuntimeError(mes)

endl = "\n"
outfile = "hello.$(Width).$(Mass)"

widths = ('narrow',)# '10pcts', '20pcts', '30pcts')
masses = ('250', '260', '270', '280', '300', '320', '350', '400',
          '450', '500', '550', '600', '650', '700', '750', '800',
          '850', '900', '1000', '1250', '1500', '1750', '2000', '2500', '3000')
loop_inside = ''
for w in widths:
    wstr = str(w)
    for m in masses:
        mstr = str(m)
        loop_inside += '    ' + wstr + ', ' + mstr
        if not (m==masses[-1] and w==widths[-1]):
            loop_inside += endl

m = ( #'universe = vanilla',
      'executable = ' + os.path.join(condor_dir, 'gridpack_htcondor.sh'),
      'arguments  = $(Width) $(Mass) {} {}'.format(out_dir, FLAGS.card_dir),
      'output     = ' + os.path.join(condor_dir, 'output/') + outfile + '.out',
      'error      = ' + os.path.join(condor_dir, 'error/')  + outfile + '.err',
      'log        = ' + os.path.join(condor_dir, 'log/')    + outfile + '.log',
      
      'getenv = true',
      '+JobBatchName="FiniteWidth"',
      '+JobFlavour = "longlunch"', # 2 hours (see https://batchdocs.web.cern.ch/local/submit.html)
      'RequestCpus = 1',
      
      'queue Width, Mass from (',
      loop_inside,
      ')'
     )

with open(os.path.join(condor_dir, 'gridpack_htcondor_' + FLAGS.out_dir + '.condor'), 'w') as file:
    file.write('\n'.join(m))
