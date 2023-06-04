
import os
import argparse
import numpy as np
import itertools
import collections
import re
import pickle

# select a palette
from bokeh.palettes import Dark2_5 as palette

import matplotlib
import matplotlib.pyplot as plt
import mplhep as hep
plt.style.use(hep.style.ROOT)

from dataclasses import dataclass

class ScanParameters:
    """Stores all parameters to be scanned."""
    def __init__(self, masses: list[int], sthetas: list[float],
                 lambdas112: list[float], kappas111: list[float]):
        self.m = masses
        self.s = sthetas
        self.l = lambdas112
        self.k = kappas111
        
        self.me = self.calc_bin_edges(self.m)
        self.se = self.calc_bin_edges(self.s)
        self.le = self.calc_bin_edges(self.l)
        self.ke = self.calc_bin_edges(self.k)
        
    # calculates the edges of the bins
    def calc_bin_edges(self, arr):
        try:
            centers = np.concatenate((arr, np.array(arr[-1]+(arr[-1]-arr[-2]))), axis=None)
            edges = np.array(arr) - np.diff(centers)/2
            edges = np.concatenate((edges, np.array(edges[-1]+(edges[-1]-edges[-2]))), axis=None)
            assert len(edges) == len(arr) + 1
            assert len(edges) == len(centers)
            return edges
        except IndexError:
            return None
    
def ntos(n, around=None):
    """Converts float to string"""
    if around is not None:
        n = np.round(n, around)
    return str(n).replace('.', 'p').replace('-', 'm')

def recursive_dict():
    return collections.defaultdict(recursive_dict)

def save_data(args, procs, pars):
    values = {k:recursive_dict() for k in procs}
    errors = {k:recursive_dict() for k in procs}

    pattern_line = re.compile("     Cross-section : .*")
    pattern_floats = re.compile(r"[+-]?\d+(?:\.\d+)?")

    for ifile, afile in enumerate(procs):
        #base = "Singlet_" + afile + "/"
        base = "TrilinearScan/"

        for m in pars.m:
            for st in pars.s:
                for lbd in pars.l:
                    for kap in pars.k:
                        found = False
                        fname = 'Singlet_hh_ST' + ntos(st) + '_L' + ntos(lbd) + '_K' + ntos(kap) + '_M' + ntos(m) + '.log'
                        for i, line in enumerate(open(base+fname)):
                            for match in re.finditer(pattern_line, line):
                               tmp = pattern_floats.findall(line)

                               # three conditions to deal with the decimal point
                               if len(tmp) == 4:
                                   val = float(tmp[0] + 'e' + tmp[1])
                                   err = float(tmp[2] + 'e' + tmp[3])
                               elif len(tmp) == 3:
                                   val = float(tmp[0])
                                   err = float(tmp[1] + 'e' + tmp[2])
                               elif len(tmp) == 2:
                                   val = float(tmp[0])
                                   err = float(tmp[1])

                               values[procs[ifile]][m][st][lbd][kap] = val
                               errors[procs[ifile]][m][st][lbd][kap] = err
                               found = True
                            
                            if found:
                               break

    for ip,proc in enumerate(procs):
        with open('values_' + proc + '.p', 'wb') as fp:
            pickle.dump(values[proc], fp, protocol=pickle.HIGHEST_PROTOCOL)
        with open('errors_' + proc + '.p', 'wb') as fp:
            pickle.dump(errors[proc], fp, protocol=pickle.HIGHEST_PROTOCOL)

    return values, errors

def plot_bokeh(hf5, out):
    """Plot using the Bokeh package"""
    from bokeh.models import ColumnDataSource, Whisker
    from bokeh.plotting import figure, save, output_file

    p = figure(height=600, width=1200, background_fill_color="#efefef", title="Cross-sections")
    p.xgrid.grid_line_color = None
    for par,c in zip(sthetas, colors):
        y = np.array([values[masses[0]][par][lambdas112[0]][k] for k in kappas111])
        e = np.array([errors[masses[0]][par][lambdas112[0]][k] for k in kappas111])
        upper = y + e/2
        lower = y - e/2
        source = ColumnDataSource(data=dict(xscan=kappas111, values=y, upper=upper, lower=lower))
        p.circle(x='xscan', y='values', source=source, legend_label=ntos(par), color=c, size=10)
     
        # whisk = Whisker(base="xscan", upper="upper", lower="lower", source=source,
        #                 level="annotation", line_width=8, line_color=c)
        # whisk.upper_head.size=8
        # whisk.lower_head.size=8
        # p.add_layout(whisk)
     
    output_file(out+'.html')
    save(p)

def plot_mpl(x, y, z, yerr, labels, out, mode='2d'):
    """
    Matplotlib plots. If mode=='2d', `x` and `y` are bin edges.
    """
    colors = itertools.cycle(palette)
    if mode=='1d':
        assert z is None

    fig = plt.figure()
    if mode == '1d':
        plt.title('SM (no resonance)')
        plt.xlabel(r'$k_{\lambda}$')
        plt.ylabel(r'$\sigma$ [pb]')
        for yval,yerr,label,c in zip(y, yerr, labels, colors):
            plt.plot(x, yval, "-o", color=c, label=label)

    elif mode == '2d':
        plt.title('Cross-section without resonance')
        plt.xlabel(r'$k_{\lambda}$')
        plt.ylabel(r'$\sigma$ [pb]')
        hep.hist2dplot(z, x, y)

    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(out+'_' + mode + '.png')

def read_hpair():
    import csv
    rows = []
    with open('plots/results.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            rows.append([float(x) for x in row])
    assert len(rows)==4
    return rows
                     
def main(args, p):
    base_out = "/eos/user/b/bfontana/www/FiniteWidth/"
    #processes = ('resonly', 'nores', 'all')
    processes = ('nores',)
    
    if args.save:
        values, errors = save_data(args, processes, p)
    else:
        values = [[] for _ in range(len(processes))]
        errors = [[] for _ in range(len(processes))]
        for ip,proc in enumerate(processes):
            with open('values_' + proc + '.p', 'wb') as fp:
                values[ip] = pickle.load(fp)
            with open('errors_' + proc + '.p', 'wb') as fp:
                errors[ip] = pickle.load(fp)
    
    born, born_errors, nlo, nlo_errors = read_hpair()

    # M vs stheta vs xsecs
    zvals1  = [values['nores'][p.m[0]][p.s[0]][p.l[0]][k] for k in p.k]
    errors1 = [errors['nores'][p.m[0]][p.s[0]][p.l[0]][k] for k in p.k]

    # M vs lambda112 vs xsecs
    # zvals2  = [[values['nores'][m][p.s[0]][lbd][p.k[0]] for lbd in p.l] for m in p.m]
    # errors2 = [[errors['nores'][m][p.s[0]][lbd][p.k[0]] for lbd in p.l] for m in p.m]

    if args.lib == 'bokeh':
        plot_bokeh(hf5, out)

    elif args.lib == 'mpl':
        plot_mpl(x=p.k, y=[zvals1, born, nlo], z=None, yerr=[errors1, born_errors, nlo_errors],
                 out=base_out+'xsecs_1', mode='1d',
                 labels=[r"$MadGraph (s_{\theta}$=0)", "HPAIR $\sigma_{BORN}$", "HPAIR $\sigma_{NLO}$"])
        #plot_mpl(x=p.m, y=p.l, z=zvals2, yerr=errors2, out=base_out+'xsecs_2.png', mode='1d')

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Plotter for finite width studies.')
    parser.add_argument('--save', action='store_true', help='Read input data before plotting.')
    parser.add_argument('--lib', default='mpl', choices=('mpl', 'bokeh'), help="Plotting library.")
    FLAGS = parser.parse_args()
    
    mass_points = (250,)
    stheta_points = np.arange(0.,1.) #np.arange(0.,1.1,.2) # sine of theta mixing between the new scalar and the SM Higgs
    l112_points = (0.,) #np.arange(-300,301,100) # resonance coupling with two Higgses
    lambda111_sm = np.round(125**2 / (2*246.), 6) # tri-linear Higgs coupling
    k111_points = np.arange(-7,12) #np.arange(-7,12) # tri-linear kappa

    scan_pars = ScanParameters(masses=mass_points, sthetas=stheta_points,
                               lambdas112=l112_points, kappas111=k111_points)    
    main(FLAGS, scan_pars)
