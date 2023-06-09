
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
    def __init__(self, masses, sthetas, lambdas112, kappas111):
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
        base = "/eos/user/b/bfontana/FiniteWidth/HomeScan/"

        for m in pars.m:
            for st in pars.s:
                for lbd in pars.l:
                    for kap in pars.k:
                        found = False
                        fname = "log_M" + ntos(m) + "_ST" + ntos(st) + "_L" + ntos(lbd) + "_K" + ntos(kap) + ".log"
                        try:
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

                        except FileNotFoundError:
                            values[procs[ifile]][m][st][lbd][kap] = -0.01
                            errors[procs[ifile]][m][st][lbd][kap] = 0.
                            

    for ip,proc in enumerate(procs):
        with open('plots/values_' + proc + '.p', 'wb') as fp:
            pickle.dump(values[proc], fp, protocol=pickle.HIGHEST_PROTOCOL)
        with open('plots/errors_' + proc + '.p', 'wb') as fp:
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

def plot_mpl(x, y, z, yerr, title, xlabel, ylabel, zlabel, labels, out, labelpad=0, mode='2d'):
    """
    Matplotlib plots. If mode=='2d', `x` and `y` are bin edges.
    """
    colors = itertools.cycle(palette)
    if mode=='1d':
        assert z is None
    elif mode=='2d':
        assert yerr is None

    fig = plt.figure()
    if mode == '1d':
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        for yval,yerr,label,c in zip(y, yerr, labels, colors):
            plt.plot(x, yval, "-o", color=c, label=label)
        plt.legend(loc="upper right")
        
    elif mode == '2d':
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        cbar = hep.hist2dplot(z, x, y, flow=None)
        cbar.cbar.ax.set_ylabel(zlabel, rotation=0, labelpad=labelpad)
        cbar.cbar.ax.tick_params(axis='y', labelrotation=0)

    plt.tight_layout()
    #hep.cms.text('Simulation')
    hep.cms.lumitext(title)
    for ext in ('.png', '.pdf'):
        plt.savefig(out+'_' + mode + ext)

def read_hpair():
    import csv
    rows = []
    with open('plots/hpair_results.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            rows.append([float(x) for x in row])
    assert len(rows)==4
    return rows
                     
def main(args, p):
    base_out = "/eos/user/b/bfontana/www/FiniteWidth/"
    #processes = ('resonly', 'nores', 'all')
    processes = ('all',)
    
    if args.save:
        values, errors = save_data(args, processes, p)
    else:
        values = {k:recursive_dict() for k in processes}
        errors = {k:recursive_dict() for k in processes}
        for ip,proc in enumerate(processes):
            with open('plots/values_' + proc + '.p', 'rb') as fp:
                values[proc] = pickle.load(fp)
            with open('plots/errors_' + proc + '.p', 'rb') as fp:
                errors[proc] = pickle.load(fp)

    # born, born_errors, nlo, nlo_errors = read_hpair()

    ### stheta vs sigma
    # for lbd in p.l:
    #     zvals, zerrs = ([] for _ in range(2))
    #     for mass in p.m:
    #         zvals.append([values['all'][mass][x][lbd][p.k[0]] for x in p.s])
    #         zerrs.append([errors['all'][mass][x][lbd][p.k[0]] for x in p.s])
             
    #     plot_mpl(x=p.s, y=zvals, z=None, yerr=zerrs,
    #              title=r"$\lambda_{{112}}={}GeV$".format(lbd),
    #              xlabel=r'$\sin(\theta)$', ylabel=r'$\sigma [pb]$',
    #              out=base_out+'homescan_lbd{}'.format(lbd), mode='1d',
    #              labels=[r"$M_{{X}}={}$".format(x) for x in p.m])

    ### lambda vs sigma
    # for st in p.s:
    #     zvals, zerrs = ([] for _ in range(2))
    #     for mass in p.m:
    #         zvals.append([values['all'][mass][st][x][p.k[0]] for x in p.l])
    #         zerrs.append([errors['all'][mass][st][x][p.k[0]] for x in p.l])
             
    #     plot_mpl(x=p.l, y=zvals, z=None, yerr=zerrs,
    #              title=r"$\sin(\theta)={}$".format(st),
    #              xlabel=r'$\lambda_{{112}}\:[GeV]$', ylabel=r'$\sigma [pb]$',
    #              out=base_out+'homescan_st{}'.format(st), mode='1d',
    #              labels=[r"$M_{{X}}={}$".format(x) for x in p.m])

    ### stheta vs lambda vs sigma (2D)
    theta_edges = p.s - (abs(p.s[1]-p.s[0])/2)
    theta_edges = np.append(theta_edges, p.s[-1] + (abs(p.s[-1]-p.s[-2])/2))
    lambda_edges = p.l - (abs(p.l[1]-p.l[0])/2)
    lambda_edges = np.append(lambda_edges, p.l[-1] + (abs(p.l[-1]-p.l[-2])/2))

    for mx in p.m:
        zvals = [[values['all'][mx][st][x][p.k[0]] for x in p.l] for st in p.s]
        plot_mpl(x=theta_edges, y=lambda_edges, z=zvals, yerr=None,
                 title=r"$M_{{X}}={}\:GeV$".format(mx),
                 xlabel=r"$\sin(\theta)$", ylabel='$\lambda_{{112}}\:[GeV]$', zlabel=r'$\sigma [pb]$',
                 out=base_out+'homescan_m{}'.format(mx), mode='2d',
                 labels=[r"$M_{{X}}={}$".format(x) for x in p.m],
                 labelpad=18 if mx==300 else 0)
    

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Plotter for finite width studies.')
    parser.add_argument('--save', action='store_true', help='Read input data before plotting.')
    parser.add_argument('--lib', default='mpl', choices=('mpl', 'bokeh'), help="Plotting library.")
    FLAGS = parser.parse_args()
    
    mass_points = (300, 600, 1000)
    stheta_points = np.round(np.arange(0.,1.,.1),2) # sine of theta mixing between the new scalar and the SM Higgs
    l112_points = np.arange(-300,301,100) # resonance coupling with two Higgses
    lambda111_sm = np.round(125**2 / (2*246.), 6) # tri-linear Higgs coupling
    k111_points = (1,) #np.arange(-7,12) # tri-linear kappa

    scan_pars = ScanParameters(masses=mass_points, sthetas=stheta_points,
                               lambdas112=l112_points, kappas111=k111_points)    
    main(FLAGS, scan_pars)
