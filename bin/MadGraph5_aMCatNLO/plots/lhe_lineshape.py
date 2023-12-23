
import os
import argparse
import re
import pylhe 
import numpy as np 
import hist
import ROOT
import pickle
import warnings
#warnings.filterwarnings("error")
import time
import gc

import matplotlib
from matplotlib import pyplot as plt
import mplhep as hep
plt.style.use(hep.style.ROOT)

import utils

def pt(p):
    px = p.px
    py = p.py
    pt = np.sqrt(px*px + py*py)
    return pt

def load(name):
    #with open(os.path.join("/home/bruno/genproductions/bin/MadGraph5_aMCatNLO/histos/", name), 'rb') as f:
    with open(os.path.join("/afs/cern.ch/work/b/bfontana/genproductions/bin/MadGraph5_aMCatNLO/histos/", name), 'rb') as f:        
        ret = pickle.load(f)
    return ret

def save(obj, name):
    #with open(os.path.join("/home/bruno/genproductions/bin/MadGraph5_aMCatNLO/histos/", name), 'wb') as f:
    with open(os.path.join("/afs/cern.ch/work/b/bfontana/genproductions/bin/MadGraph5_aMCatNLO/histos/", name), 'wb') as f:
        pickle.dump(obj, f)
        
def plot(hists, out, interf, max_events, log=False, ratio=False, diff=False, verbose=True):
    """Matplotlib lineshape plots."""
    #assert not (ratio and diff)
    palette = plt.get_cmap('Set1') #matplotlib.colormaps['Set1']
    colors = iter(utils.colormap_discretize(palette))

    labels = {'all'     : r"$\sigma_{full}$",
              'nores'   : r"$\sigma_{nores}$",
              'resonly' : r"$\sigma_{res}$"}
    ratios = [3.,1.] if ratio else [1.,0.]

    fig, (ax1, ax2) = plt.subplots(2, sharex=True, gridspec_kw={'height_ratios': ratios})
    figtop, figleft = 0.95, 0.2 if diff else 0.15
    fig.subplots_adjust(hspace=0., wspace=0., left=figleft, right=.99, top=figtop)
    if not ratio:
        ax2.set_yticks([])

    hep.cms.text('Simulation', fontsize=20, ax=ax1)
    title = re.findall(".*_M(.+)_ST(.+)_L(.+)_K(.+)_cmsgrid_final", out)[0]
    title = [float(t.replace('m', '-').replace('p', '.')) for t in title]
    title = r"$M_{{X}}={}\;GeV, \sin\alpha={}, \lambda_{{HHX}}={}\;GeV, k_{{\lambda}}={}$".format(*title)
    plt.figtext(0.96, figtop-0.04, title, fontsize=20, color="black", horizontalalignment='right')

    ax1.set_ylabel(r"$d \sigma / d m_{HH}\:\: [pb/GeV]$")
    if log:
        ax1.set_yscale('log')
    # axes = plt.gca()
    # axes.set_xlim([-0.3,1.])

    if diff:
        ax1.errorbar(hists['all'].axes[0].centers, hists['all'].values()-hists['nores'].values(),
                     yerr=np.sqrt(hists['all'].variances() + hists['nores'].variances()),
                     fmt="-o", color=next(colors),
                     label=labels['all'] + ' - ' + labels['nores'])
        ax1.errorbar(hists['resonly'].axes[0].centers, hists['resonly'].values(), yerr=np.sqrt(hists['resonly'].variances()),
                     fmt="-o", color=next(colors), label=labels['resonly'])
    else:
        for k, v in hists.items():
            ax1.errorbar(v.axes[0].centers, v.values(), yerr=np.sqrt(v.variances()),
                         fmt="-o", color=next(colors), label=labels[k])

    if ratio:
        # warnings.filterwarnings("error")
        # try:
        #     yvals = y['all'].values() / (y['resonly'].values() + y['nores'].values())
        # except RuntimeWarning:
        #     yvals[np.isnan(yvals)] = 0.
        # warnings.resetwarnings()
        if diff:
            yvals = (hists['all'].values()-hists['nores'].values()) / hists['resonly'].values()
        else:
            yvals = hists['all'].values() / (hists['resonly'].values() + hists['nores'].values())
        yvals[np.isnan(yvals)] = 0.
            
        try:
            if diff:
                var_ratio = yvals**2 * ( (hists['all'].variances()+hists['nores'].variances()) /
                                         (hists['all'].values()-hists['nores'].values())**2 +
                                         (hists['resonly'].variances()) / (hists['resonly'].values())**2 )

            else:
                var_ratio = yvals**2 * ( hists['all'].variances() / hists['all'].values()**2 +
                                         (hists['nores'].variances()+hists['resonly'].variances()) /
                                         (hists['nores'].values()+hists['resonly'].values())**2 )
            var_ratio[np.isnan(var_ratio)] = 0.
        except RuntimeWarning:
            var_ratio = 0.

        ax2.errorbar(hists['all'].axes[0].centers, yvals, yerr=np.sqrt(var_ratio),
                     fmt="-o", color=next(colors))
        if diff:
            ax2.set_ylabel(r"$(\sigma_{full} - \sigma_{nores})\; / \;\sigma_{res}$", fontsize=18)
        else:
            ax2.set_ylabel(r"$\sigma_{full}\; / \;(\sigma_{res}+\sigma_{nores})$", fontsize=18)
        ax2.set_xlabel(r"$m_{HH}\: [GeV]$")
        ax2.axhline(1., linestyle='--', color='gray')
        
    inner_top_space_percentage, axis_dist = 1.1, ax1.get_ylim()[1] - ax1.get_ylim()[0]
    ax1.set_ylim(bottom=ax1.get_ylim()[0],
                 top=ax1.get_ylim()[1] + inner_top_space_percentage * axis_dist)

    ax1.legend(bbox_to_anchor=(0.78, 0.91), loc="upper left", borderaxespad=0)
    xstart = 0.71 if diff else 0.79
    figtext_dict = dict(fontsize=15, color ="black",
                        style="italic",
                        wrap=True,
                        horizontalalignment ="right",
                        bbox ={'facecolor':'grey', 
                               'alpha':0.3, 'pad':5})
    plt.figtext(xstart, figtop-0.10, "Interference ratio: " + str(int(interf*100)) + '%',
                **figtext_dict)
    Gamma = '\u0393'
    plt.figtext(xstart, figtop-0.15, Gamma + "/M=5%", **figtext_dict)

    if log:
        out += '_log'
    if diff:
        out += '_diff'
    out += "_NEVENTS" + str(max_events) if max_events != -1 else "all"
    for ext in ('.png', '.pdf'):
        save_name = 'histplots/' + out + ext
        if verbose:
            print('Saving plot under {}'.format(save_name))
        plt.savefig(save_name)

    plt.close()

def print_event_info(p):
    d = dict(flush=True)
    print("", **d)
    print("pdgId:"    , p.id, **d)
    print("mass:"     , p.m, **d)
    print("mother1:"  , p.mother1, **d)
    print("mother2:"  , p.mother2, **d)
    print("color1:"   , p.color1, **d)
    print("color2:"   , p.color2, **d)                
    print("status:"   , p.status, **d)
    print("lifetime:" , p.lifetime, **d)  
    print("px:"       , p.px, **d)  
    print("py:"       , p.py, **d)  
    print("pz:"       , p.pz, **d)  
    print("spin:"     , p.spin, **d)

def default(args, files, xsecs):
    max_events_str = str(args.max_events) if args.max_events != -1 else "all"
    
    hh_hist = {}
    for fkey in files:
        hh_hist[fkey] = {}
        print('File key: ', fkey, flush=True)

        for atype,afile in files[fkey].items():
            histoname = os.path.basename(afile).replace('.lhe', '')
            
            if not os.path.isfile(afile):
                print("[WARNING] File {} was not found!".format(afile), flush=True)
                continue

            if args.process:
                # if afile != '/eos/user/b/bfontana/FiniteWidth/ManualV3_nores/Singlet_TManualV3_nores_M280p00_ST0p14_Lm462p96_K1p00_untar/Singlet_TManualV3_nores_M280p00_ST0p14_Lm462p96_K1p00_cmsgrid_final.lhe':
                # if 'M500p00' not in afile:
                #     continue
                #print("Event counts for type {}: {}".format(atype, pylhe.read_num_events(afile)), flush=True)
                
                hh_hist[fkey][atype] = hist.Hist(hist.axis.Regular(60, 230, 1150, name="mass"),
                                                 storage=hist.storage.Weight())

                # loop on lhe content
                atime = time.time()
                for ievt, evt in enumerate(pylhe.read_lhe(afile)): #pylhe.read_lhe_with_attributes
                    if ievt%5000==0 and args.verbose:
                        print(time.time() - atime, ' - {} events processed'.format(ievt))
                        atime = time.time()
                        gc.collect()
             
                    if ievt==args.max_events:
                        print('stopping at {} events'.format(ievt), flush=True)
                        break
         
                    particles = evt.particles
                    higgses, gluons = ([] for _ in range(2))
                    
                    for ip,p in enumerate(particles):
                        pdg_id = p.id
         
                        if args.more_verbose:
                            print_event_info(p)
         
                        if pdg_id == 25: # Higgs
                            higgses.append(ip)
                        elif pdg_id == 21: # gluons
                            gluons.append(ip)
         
                    if len(higgses)!=2 or len(gluons)!=2:
                        breakpoint()
         
                    h1, h2 = particles[higgses[0]], particles[higgses[1]]
                    h1_v = ROOT.Math.PxPyPzMVector(h1.px, h1.py, h1.pz, h1.m)
                    h2_v = ROOT.Math.PxPyPzMVector(h2.px, h2.py, h2.pz, h2.m)
                    hh_v = h1_v + h2_v
                    hh_hist[fkey][atype].fill(mass=hh_v.M(), weight=xsecs[fkey][atype][0])

                gc.collect()
                save(hh_hist[fkey][atype], histoname + "_" + max_events_str + ".pkl")
     
            else:
                hh_hist[fkey][atype] = load(histoname + "_" + max_events_str + ".pkl")
                
    return hh_hist

def parallel_func():
    max_events_str = str(args.max_events) if args.max_events != -1 else "all"
    
    hh_hist[fkey] = {}
    print('File key: ', fkey, flush=True)

    for atype,afile in files[fkey].items():
        histoname = os.path.basename(afile).replace('.lhe', '')
        
        if not os.path.isfile(afile):
            print("[WARNING] File {} was not found!".format(afile), flush=True)
            continue

        if args.process:
            #print("Event counts for type {}: {}".format(atype, pylhe.read_num_events(afile)), flush=True)
            
            hh_hist[fkey][atype] = hist.Hist(hist.axis.Regular(60, 230, 1150, name="mass"),)

            # loop on lhe content
            atime = time.time()
            for ievt, evt in enumerate(pylhe.read_lhe(afile)): #pylhe.read_lhe_with_attributes
                if ievt%500==0 and args.verbose:
                    print(time.time() - atime, flush=True)
                    atime = time.time()
                    print(' - {} events processed'.format(ievt), flush=True)
                    gc.collect()
         
                if ievt==args.max_events:
                    print('stopping at {} events'.format(ievt), flush=True)
                    break
     
                particles = evt.particles
                higgses, gluons = ([] for _ in range(2))
                
                for ip,p in enumerate(particles):
                    pdg_id = p.id
     
                    if args.more_verbose:
                        print_event_info(p)
     
                    if pdg_id == 25: # Higgs
                        higgses.append(ip)
                    elif pdg_id == 21: # gluons
                        gluons.append(ip)
     
                if len(higgses)!=2 or len(gluons)!=2:
                    breakpoint()
     
                h1, h2 = particles[higgses[0]], particles[higgses[1]]
                h1_v = ROOT.Math.PxPyPzMVector(h1.px, h1.py, h1.pz, h1.m)
                h2_v = ROOT.Math.PxPyPzMVector(h2.px, h2.py, h2.pz, h2.m)
                hh_v = h1_v + h2_v
                hh_hist[fkey][atype].fill(mass = hh_v.M())

            hh_hist[fkey][atype] = hh_hist[fkey][atype] * xsecs[fkey][atype] / hh_hist[fkey][atype].sum()
            save(hh_hist[fkey][atype], histoname + "_" + max_events_str + ".pkl")
 
        else:
            hh_hist[fkey][atype] = load(histoname + "_" + max_events_str + ".pkl")
    return hh_hist

def parallel(args, files, xsecs):
    assert len(files) == len(xsecs)
    with Pool(len(files)) as pool:
        pool_out = pool.starmap(parallel_func, zip(files.values(), xsecs.values()))
        
    hh_hist = {}
    for k in files:
        hh_hist[k] = pool_out[ik]
    for fkey in files:
        pass

def lineshape(args, files, xsecs):
    if args.parallel:
        hh_hist = parallel()
    else:
        hh_hist = default(args, files, xsecs)

    for fkey in files:
        if len(hh_hist[fkey].keys()) == 0:
            print("[WARNING] Key {} cannot be used for plotting!".format(fkey), flush=True)
            continue

        histoname = os.path.basename(files[fkey]['all']).replace('.lhe', '')

        # remove the first bin, which tends to be zero everywhere and ruins the ratio
        for kk in hh_hist[fkey]:
            hh_hist[fkey][kk] = hh_hist[fkey][kk][1:]

        plot(hists=hh_hist[fkey], out=histoname,
             interf=xsecs[fkey]['interf_ratio'], log=args.log,
             ratio=args.ratio, diff=args.diff, max_events=args.max_events,
             verbose=args.verbose)

        
if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Plotter for finite width studies.')
    parser.add_argument('--max_events', default=-1, type=int,
                        help="Number of events to process. -1 stands for all events."),
    parser.add_argument('-v', '--verbose', action='store_true', help='Print information.')
    parser.add_argument('-vv', '--more_verbose', action='store_true', help='Print additional information.')
    parser.add_argument('--process', action='store_true', help='Rerun the event processing step.')
    parser.add_argument('--log',     action='store_true', help='Produce all plots with logarithmic vertical scale.')
    parser.add_argument('--ratio',   action='store_true', help='Plot the cross-section ratio full/(res+nonres).')
    parser.add_argument('--diff',    action='store_true', help='Plot the (full - nonres) vs. res cross-sections.')
    parser.add_argument('--parallel', action='store_true', help='Parallellize LHE file processing.')
    FLAGS = parser.parse_args()

    # npoints = 8
    # mass_points = (280.00, 280.00, 280.00, 280.00, 500.00, 500.00, 500.00, 500.00,)
    # stheta_points = (0.13567098371723735, 0.2894854650837087, 0.2856288516305749, 0.1382831521414572,
    #                  0.26584438206608024, 0.6230475388128988, 0.623047342987846, 0.2703843950062829)
    # l112_points = (463.04669073123836,  456.07996812710076, -456.28973821658485, -462.9614416165804,
    #                -540.9740053286384, -15.723140044075462, 15.72786607510946, 539.0584734716218)
    # k111_points = (1.0,)*npoints # ... tri-linear kappa                                                                                 
    npoints = 8
    mass_points = (280.00, 280.00, 280.00, 280.00, 500.00, 500.00, 500.00, 500.00,)
    stheta_points = (0.13567098371723735, 0.2894854650837087, 0.2856288516305749, 0.1382831521414572,
                     0.26584438206608024, 0.033, 0.033, 0.2703843950062829)
    l112_points = (463.04669073123836,  456.07996812710076, -456.28973821658485, -462.9614416165804,
                   -540.9740053286384, -600.00, 600.00, 539.0584734716218)
    k111_points = (1.0,)*npoints # ... tri-linear kappa                                                                                 
    assert all(len(x) == npoints for x in (mass_points, stheta_points, l112_points, k111_points))

    # cross-section in pb units
    # xs_all       = (0.05733, 0.2453, 0.2922, 0.0883,
    #                 0.08295, 0.003499, 0.005133, 0.1262)
    # xs_nores     = (0.01249, 0.01057, 0.01064, 0.01247,
    #                 0.01094, 0.003887, 0.003887, 0.01087)
    # xs_resonly   = (0.05929, 0.2617, 0.2548, 0.06143,
    #                 0.09211, 0.0004301, 0.00042, 0.09446)
    # interfratios = (-0.20, -0.10, +0.10, +0.20,
    #                 -0.20, -0.10, +0.10, +0.20)
    xs_all       = ((0.05733, 5.569e-05), (0.2453,   0.0004106),  (0.2922,   0.0008045),  (0.0883,  0.0002845),
                    (0.08295, 0.0002813), (0.01175,  1.925E-5),   (0.01784,  4.751E-5),   (0.1262,  0.0008491))
    xs_nores     = ((0.01249, 1.285e-05), (0.01057,  1.101e-05),  (0.01064,  1.107e-05),  (0.01247, 1.283e-05),
                    (0.01094, 1.137e-05), (0.01303,  1.343E-5),   (0.01303,  1.343E-5),   (0.01087, 1.13e-05))
    xs_resonly   = ((0.05929, 0.0001383), (0.2617,   0.0006083),  (0.2548,   0.0005884),  (0.06143, 0.0001414),
                    (0.09211, 0.0004947), (0.001742, 9.459E-6),   (0.001723, 9.004E-6),   (0.09446, 0.0005022))
    interfratios = (-0.20, -0.10, +0.10, +0.20,
                    -0.20, -0.10, +0.10, +0.20)
    
    tag = "ManualV3" # "LowSin"
    base  = "/eos/user/b/bfontana/FiniteWidth/" + tag + "_"
    files, xsecs = {}, {}
    for mp,sp,lp,kp,xall,xres,xnores,ir in zip(mass_points,stheta_points,l112_points,k111_points,xs_all,xs_resonly,xs_nores,interfratios):
        nameid = "M" + format(mp, ".2f") + "_ST" + format(sp, ".2f") + "_L" + format(lp, ".2f") + "_K" + format(kp, ".2f")
        nameid = nameid.replace('.', 'p').replace('-','m')
        final = "_cmsgrid_final.lhe"
        files[nameid] = {
            'all'     : base + "all/Singlet_T" + tag + "_all_" + nameid + "_untar/Singlet_T" + tag + "_all_" + nameid + final,
            'resonly' : base + "resonly/Singlet_T" + tag + "_resonly_" + nameid + "_untar/Singlet_T" + tag + "_resonly_" + nameid + final,
            'nores'   : base + "nores/Singlet_T" + tag + "_nores_" + nameid + "_untar/Singlet_T" + tag + "_nores_" + nameid + final,
        }
        xsecs[nameid] = {'all': xall, 'resonly': xres, 'nores': xnores, 'interf_ratio': ir}

    assert xsecs.keys() == files.keys()
    # for k in xsecs:
    #     assert xsecs[k]['all'] >= xsecs[k]['nores']
    #     assert xsecs[k]['all'] >= xsecs[k]['resonly']

    lineshape(FLAGS, files, xsecs)
