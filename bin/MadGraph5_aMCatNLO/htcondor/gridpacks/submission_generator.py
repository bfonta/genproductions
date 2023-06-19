
import sys
import os
import argparse
import numpy as np
from dataclasses import dataclass

@dataclass
class ParScan:
    mas: list[float]
    sth: np.ndarray  # sine of theta mixing between the new scalar and the SM Higgs
    lbd: np.ndarray  # resonance coupling with two Higgses
    kap: tuple[float]

@dataclass
class Pathes:
    baselocal   : str
    basestorage : str
    condor      : str
    out         : str
    cards       : str

def create_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)
    else:
        mes = 'Folder {} already exists!\n'.format(d)
        mes += 'Deletion command: rm -r {}\n'.format(d)
        raise RuntimeError(mes)

def ntos(n, around=None):
    """Converts float to string"""
    if around is not None:
        n = np.round(n, around)
    return str(n).replace('.', 'p').replace('-', 'm')

def get_condor_submission_main_text(path, job_name, child):
    if child:
        outfile = job_name
        exe = 'move.sh'  
        args = '{} {} {}'.format(path.out, tag, job_name)
        mem = '1GB'
        disk = '1GB'
        flavour = 'expresso' # 20 minutes (see https://batchdocs.web.cern.ch/local/submit.html)
    else:
        outfile = "Singlet_T" + tag + "_M$(Mass)_ST$(Stheta)_L$(Lambda112)_K$(Kappa111)"
        exe = 'submission.sh'
        args = '$(Mass) $(Stheta) $(Lambda112) $(Kappa111) {} {} {}'.format(path.out, path.cards, tag)
        mem = '4GB'
        disk = '2GB'
        flavour = 'microcentury' # 1 hour (see https://batchdocs.web.cern.ch/local/submit.html)
        
    m = '\n'.join(('universe = vanilla',
                   'executable = ' + os.path.join(pathes.baselocal, exe),
                   'arguments  = ' + args,
                   'output     = ' + outfile + ('_child' if child else '') + '.out',
                   'error      = ' + outfile + ('_child' if child else '') + '.err',
                   
                   #'output_destination = root://eosuser.cern.ch/' + path.basestorage + '/$(Mass)_$(Stheta)_$(Lambda112)_$(Kappa111)/',
                   #'MY.XRDCP_CREATE_DIR = True',
                      
                   'getenv = true',
                   '+JobBatchName = "FW_{}'.format(tag) + ('_child' if child else '') + "\"",
                   '+JobFlavour   = "{}"'.format(flavour),
                   
                   'RequestCpus   = 1',
                   'RequestMemory = ' + mem,
                   'RequestDisk   = ' + disk,
                   
                   'max_materialize = 80'))
    if child:
        m += '\nqueue\n'
    else:
        m += '\nqueue Mass, Stheta, Lambda112, Kappa111 from (\n'
    return m

def write_condor_file(par, path, tag, child):
    """Write condor submission file."""
    for st in par.sth:
        for lbd in par.lbd:
            for kap in par.kap:
                for m in par.mas:
                    condor_name = ("Singlet_T" + tag + "_M" + ntos(m) + "_ST" + ntos(st,1) +
                                   "_L" + ntos(lbd) + "_K" + ntos(kap))
                    if child:
                        mes = get_condor_submission_main_text(path, condor_name, child=True)
                        with open(os.path.join(path.condor, tag, condor_name + '_child.condor'), 'w') as file:
                            file.write(mes)

                    mes = get_condor_submission_main_text(path, condor_name, child=False)
                    with open(os.path.join(path.condor, tag, condor_name + '.condor'), 'w') as file:
                        full = mes + '    ' + ntos(m) + ', ' + ntos(st, 1) + ', ' + ntos(lbd) + ', ' + ntos(kap) + '\n)'
                        file.write(full)

        
def write_dag_file(par, path, tag, child=True):
    """Write condor DAGMAN submission file."""
    file = open(os.path.join(path.baselocal, 'submission_' + tag + '.dag'), 'w')

    file.write('CONFIG {}/dag.config\n\n'.format(path.baselocal))
    
    for st in par.sth:
        for lbd in par.lbd:
            for kap in par.kap:
                for m in par.mas:
                    job_name = "Singlet_T" + tag + "_M" + ntos(m) + "_ST" + ntos(st,1) + "_L" + ntos(lbd) + "_K" + ntos(kap)
                    m = 'JOB {}_job {}/{}/{}.condor \n'.format(job_name, path.condor, tag, job_name)
                    if child:
                        m += 'JOB {}_child {}/{}/{}_child.condor \n'.format(job_name, path.condor, tag, job_name)
                        m += 'PARENT {j}_job CHILD {j}_child '.format(j=job_name) + '\n\n'
                    else:
                        move_args = ' '.join((path.out, tag, job_name))
                        m += 'SCRIPT POST {}_job {}/move.sh '.format(job_name, path.baselocal) + move_args + '\n\n'
                    file.write(m)
    file.close()
    
if __name__ == "__main__":
    major, minor, _, _, _ = sys.version_info
    if major < 3 or (major == 3 and minor < 9):
        m =  "This script requires at least Python 3.9\n"
        m += "Run `source /cvmfs/sft.cern.ch/lcg/views/LCG_103/x86_64-centos7-gcc11-opt/setup.sh`\n"
        raise Exception(m)
    
    example = 'python generateCards.py --out TestSinglet --template SingletModel/cards_templates/'
    parser = argparse.ArgumentParser(description='Plotter for finite width studies.\nExample: {} .'.format(example))
    parser.add_argument("--out_dir", required=True, help="Output directory. Its name must match the tag used for the datacards.",)
    parser.add_argument("--card_dir", required=True,
                        choices=('Singlet_resonly', 'Singlet_nores', 'Singlet_all'), 
                        help="Datacards subdirectory.",)
    parser.add_argument('--no_child', action='store_true')
    FLAGS = parser.parse_args()

    base_local = os.path.join('/afs/cern.ch/work/',
                              os.environ['USER'][0], os.environ['USER'],
                              'genproductions/bin/MadGraph5_aMCatNLO/htcondor/gridpacks/')
    base_storage = os.path.join('/eos/user/',
                                os.environ['USER'][0], os.environ['USER'], 'FiniteWidth')

    tag = FLAGS.out_dir

    condor_sub = os.path.join(base_local, "condor_sub")
    create_dir(os.path.join(condor_sub, tag))

    out_dir = os.path.join(base_storage, FLAGS.out_dir + '/')
    create_dir(out_dir)
    
    pars = ParScan(mas=('250', '270', '300', '350', '400',
                        '500', '600', '700', '800', '900', '1000'),
                   sth=np.arange(0.,1.001,.1),
                   lbd=np.arange(-300,301,100),
                   kap=(1.0,2.4,10.0))

    pathes = Pathes(baselocal=base_local,
                    basestorage=base_storage,
                    condor=condor_sub,
                    out=out_dir,
                    cards=FLAGS.card_dir)

    write_condor_file(pars, pathes, tag, not FLAGS.no_child)

    write_dag_file(pars, pathes, tag, not FLAGS.no_child)
