
import os
import argparse
import numpy as np
import itertools
import collections
import re
import pickle

# select a palette
from bokeh.palettes import Dark2_5 as palette

from dataclasses import dataclass

class ScanParameters:
    """Stores all parameters to be scanned."""
    def __init__(self, mass: list[int], stheta: list[float], lambda112: list[float], kappa111: list[float]):
        self.m = mass
        self.s = stheta
        self.l = lambda112
        self.k = kappa111

        self.me = calc_bin_edges(self.mass)
        self.se = calc_bin_edges(self.stheta)
        self.le = calc_bin_edges(self.lambda112)
        self.ke = calc_bin_edges(self.kappa111)
        
    # calculates the edges of the bins
    def calc_bin_edges(self, arr):
        centers = np.concatenate((arr, np.array(arr[-1]+(arr[-1]-arr[-2]))), axis=None)
        edges = np.concatenate(centers - np.diff(centers)/2
        assert len(edges) == len(arr) - 1
        assert len(edges) == len(centers)
        return edges
    
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
        base = "Singlet_" + afile + "/"
            
        for m in pars.mass:
            for st in pars.stheta:
                for lbd in pars.lambda112:
                    for kap in pars.kappa111:
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
                                
                               values[ifile][m][st][lbd][kap] = val
                               errors[ifile][m][st][lbd][kap] = err
                               found = True
                               #print(m, st, lbd, kap)
                               #print(val, err)
                            
                            if found:
                               break

    for ip,proc in enumerate(procs):
        with open('values_' + proc + '.p', 'wb') as fp:
            pickle.dump(values[ip], fp, protocol=pickle.HIGHEST_PROTOCOL)
        with open('errors_' + proc + '.p', 'wb') as fp:
            pickle.dump(errors[ip], fp, protocol=pickle.HIGHEST_PROTOCOL)

    return values, errors

def plot_bokeh(hf5, out):
    """Plot using the Bokeh package"""
    from bokeh.models import ColumnDataSource, Whisker
    from bokeh.plotting import figure, save, output_file

    p = figure(height=600, width=1200, background_fill_color="#efefef", title="Cross-sections")
    p.xgrid.grid_line_color = None
    for par,c in zip(sthetas, colors):
        y = np.array([values[masses[0]][par][lambdas112[0]][k for k in kappas111])
        e = np.array([errors[masses[0]][par][lambdas112[0]][k for k in kappas111])
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

def plot_mpl(x, y, z=None, yerr, h5f, out, mode='2d'):
    """
    Matplotlib plots. If mode=='2d', `x` and `y` are bin edges.
    """
    if mode=='1d':
        assert z is None

    import matplotlib
    import matplotlib.pyplot as plt
    import mplhep as hep
    plt.style.use(hep.style.ROOT)

    fig = plt.figure()
    if mode == '1d':
        plt.title('Cross-section without resonance')
        plt.xlabel(r'$k_{\lambda}$')
        plt.ylabel(r'$\sigma$ [pb]')
        for par,c in zip(sthetas, colors):
            plt.errorbar(x, y, yerr, color=c, fmt='o')
            plt.plot(x, y, yerr, color=c, label=r"$s_{\theta}$="+str(par), fmt='-o')

    elif mode == '2d':
        plt.title('Cross-section without resonance')
        plt.xlabel(r'$k_{\lambda}$')
        plt.ylabel(r'$\sigma$ [pb]')
        hep.hist2dplot(z, x, y)

    plt.legend(loc="upper right")
    plt.tight_layout()
    plt.savefig(out+'_' + mode + '.png')
                     
def main(args, p):
    colors = itertools.cycle(palette)  
    base_out = "/eos/user/b/bfontana/www/FiniteWidth/"
    processes = ('resonly', 'nores', 'all')
    
    if args.save:
        values, errors = save_data(args, processes, p)
    else:
        values = [[] for _ in range(len(processes))]
        errors = [[] for _ in range(len(processes))]
        for ip,proc in enumerate(procs):
            with open('values_' + proc + '.p', 'wb') as fp:
                values[ip] = pickle.load(fp)
            with open('errors_' + proc + '.p', 'wb') as fp:
                errors[ip] = pickle.load(fp)
    
    # M vs stheta vs xsecs
    zvals1 = [[values[0][m][st][p.l[0]][p.k[0]] for st in p.s] for m in p.m]

    # M vs lambda112 vs xsecs
    zvals2 = [[values[0][m][p.s[0]][lbd][p.k[0]] for lbd in p.l] for m in p.m]

    if args.lib == 'bokeh':
        plot_bokeh(hf5, out)

    elif args.lib == 'mpl':
        plot_mpl(x=p.m, y=p.s, z=zvals1, out=base_out+'xsecs_1.png', mode='2d')
        plot_mpl(x=p.m, y=p.l, z=zvals2, out=base_out+'xsecs_2.png', mode='2d')

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Plotter for finite width studies.')
    parser.add_argument('--save', action='store_true', help='Read input data before plotting.')
    parser.add_argument('--lib', default='mpl', choices=('mpl', 'bokeh'), help="Plotting library.")
    FLAGS = parser.parse_args()
    
    mass_points = (250, 350, 450, 550, 650, 750, 850, 950)
    stheta_points = np.arange(0.,1.1,.2) # sine of theta mixing between the new scalar and the SM Higgs
    l112_points = np.arange(-300,301,100) # resonance coupling with two Higgses
    lambda111_sm = np.round(125**2 / (2*246.), 6) # tri-linear Higgs coupling
    k111_points = (1.,) #np.arange(-7,12) # tri-linear kappa

    scan_pars = ScanParameters(masses=mass_points, sthetas=stheta_points,
                               lambdas112=l112_points, kappas111=k111_points)    
    main(FLAGS, scan_pars)
