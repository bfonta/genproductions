
import sys
import os
import argparse
import numpy as np

class ScanParameters:
    class dot(dict):
        """dot.notation access to dictionary attributes"""
        __getattr__ = dict.get
        __setattr__ = dict.__setitem__
        __delattr__ = dict.__delitem__

    def __init__(self, masses, sthetas, lambdas, kappas):
        self.masses  = masses
        self.sthetas = sthetas
        self.lambdas = lambdas
        self.kappas  = kappas

class Pathes:
    def __init__(self, baselocal, basestorage, condor, out, cards):
        self.baselocal = baselocal 
        self.basestorage = basestorage
        self.condor = condor
        self.out = out
        self.cards = cards

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

def write_condor_file(par, path, tag, manual, child=True):
    """Write condor submission file."""
    def single(st, lbd, kap, m):
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

    if manual:
        for m,st,kap,lbd in zip(par.masses,par.sthetas,par.kappas,par.lambdas):
            single(st, lbd, kap, m)
    else:            
        for st in par.sthetas:
            for lbd in par.lambdas:
                for kap in par.kappas:
                    for m in par.masses:
                        single(st, lbd, kap, m)

        
def write_dag_file(par, path, tag, manual, child=True):
    """Write condor DAGMAN submission file."""
    def single(st, lbd, kap, m):
        job_name = "Singlet_T" + tag + "_M" + ntos(m) + "_ST" + ntos(st,1) + "_L" + ntos(lbd) + "_K" + ntos(kap)
        m = 'JOB {}_job {}/{}/{}.condor \n'.format(job_name, path.condor, tag, job_name)
        if child:
            m += 'JOB {}_child {}/{}/{}_child.condor \n'.format(job_name, path.condor, tag, job_name)
            m += 'PARENT {j}_job CHILD {j}_child '.format(j=job_name) + '\n\n'
        else:
            move_args = ' '.join((path.out, tag, job_name))
            m += 'SCRIPT POST {}_job {}/move.sh '.format(job_name, path.baselocal) + move_args + '\n\n'
        file.write(m)

    file = open(os.path.join(path.baselocal, 'submission_' + tag + '.dag'), 'w')
    file.write('CONFIG {}/dag.config\n\n'.format(path.baselocal))
    
    if manual:
        for m,st,kap,lbd in zip(par.masses,par.sthetas,par.kappas,par.lambdas):
            single(st, lbd, kap, m)
    else:            
        for st in par.sthetas:
            for lbd in par.lambdas:
                for kap in par.kappas:
                    for m in par.masses:
                        single(st, lbd, kap, m)

    file.close()

if __name__ == "__main__":
    major, minor, _, _, _ = sys.version_info
    if major < 3:
        m =  "This script requires Python 3\n"
        m += "Run `source /cvmfs/sft.cern.ch/lcg/views/LCG_103/x86_64-centos7-gcc11-opt/setup.sh`\n"
        raise Exception(m)
    
    example = 'python generateCards.py --out TestSinglet --template SingletModel/cards_templates/'
    parser = argparse.ArgumentParser(description='Plotter for finite width studies.\nExample: {} .'.format(example))
    parser.add_argument("--out_dir", required=True, help="Output directory. Its name must match the tag used for the datacards.",)
    parser.add_argument("--card_dir", required=True,
                        choices=('Singlet_resonly', 'Singlet_nores', 'Singlet_all'), 
                        help="Datacards subdirectory.",)
    parser.add_argument('--no_child', action='store_true')
    manual_help = "Produce data points as individually specified (no scan across all combinations)."
    parser.add_argument("--manual", action="store_true", help=manual_help)
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

    if FLAGS.manual:
        mass_points = (300.00, 300.00, 600.00, 600.00, 1000.00, 1000.00)             
        stheta_points = (0.3, 0.1, 0.8, 0.1, 0.4, 0.3)
        l112_points = (-500.00, -400.00, 600.00, 300.00, 100.00, 300.00)
        k111_points = (1.0,)*6 # + (2.4,)*6 + ... tri-linear kappa
    else:
        mass_points = (280.00, 300.00, 400.00, 500.00, 600.00, 700.00, 800.00, 900.00, 1000.00)
        stheta_points = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99) # sine of theta mixing between the new scalar and the SM Higgs
        l112_points = (-600.00, -500.00, -400.00, -300.00, -200.00, -100.00, -50.00,
                       0.00, 50.00, 100.00, 200.00, 300.00, 400.00, 500.00, 600.00) # resonance coupling with two Higgses
        k111_points = (-1.0, 1.0, 2.4, 6.0) # tri-linear kappa

    pars = ScanParameters(masses=mass_points, sthetas=stheta_points,
                          lambdas=l112_points, kappas=k111_points)

    pathes = Pathes(baselocal=base_local,
                    basestorage=base_storage,
                    condor=condor_sub,
                    out=out_dir,
                    cards=FLAGS.card_dir)

    write_condor_file(pars, pathes, tag, not FLAGS.no_child)

    write_dag_file(pars, pathes, tag, not FLAGS.no_child)
