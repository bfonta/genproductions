
import os
import argparse
import numpy as np
import itertools
import collections

from bokeh.models import ColumnDataSource, Whisker
from bokeh.plotting import figure, save, output_file
# select a palette
from bokeh.palettes import Dark2_5 as palette
# itertools handles the cycling

def ntos(n):
    """Converts float to string"""
    return str(n).replace('.', 'p').replace('-', 'm')

import re
pattern_line = re.compile("     Cross-section : .*")
pattern_floats = re.compile(r"[+-]?\d+(?:\.\d+)?")

parser = argparse.ArgumentParser(description='Plotter for finite width studies.')
parser.add_argument("--out_dir", required=True, help="Output directory.",)
FLAGS = parser.parse_args()

# widths = ('narrow', '10pcts', '20pcts', '30pcts')
# masses = ('250', '260', '270', '280', '300', '320', '350', '400',
#           '450', '500', '550', '600', '650', '700', '750', '800',
#           '850', '900', '1000', '1250', '1500', '1750', '2000', '2500', '3000')
masses = (250,)
sthetas = (0., 1.) #(0.2, 0.5, 0.8)
lambdas112 = (0.,)
kappas111 = np.arange(-7,12) # tri-linear kappa

name = "Singlet_hh_ST${STHETA}_L${LAMBDA112}_K${KAPPA111}_M${MASS}"

def recursive_dict():
    return collections.defaultdict(recursive_dict)
values, errors = (recursive_dict() for _ in range(2))

for m in masses:
    for st in sthetas:
        for lbd in lambdas112:
            values[m][st][lbd], errors[m][st][lbd] = ([] for _ in range(2))

            for kap in kappas111:
                found = False
                fname = 'Singlet_hh_ST' + ntos(st) + '_L' + ntos(lbd) + '_K' + ntos(kap) + '_M' + ntos(m) + '.log'
        
                for i, line in enumerate(open(os.path.join(FLAGS.out_dir, fname))):
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
                            
                        values[m][st][lbd].append(val)
                        errors[m][st][lbd].append(err)
                        found = True
                        #print(m, st, lbd, kap)
                        #print(val, err)
                        
                    if found:
                        break

varscan = np.array(kappas111).astype(float)
colors = itertools.cycle(palette)  
out = "/eos/user/b/bfontana/www/FiniteWidth/xsec"

### Draw graph, plotting multiple curves of `varscan` for different parameters `par`

# p = figure(height=600, width=1200, background_fill_color="#efefef", title="Cross-sections")
# p.xgrid.grid_line_color = None
# for par,c in zip(sthetas, colors):
#     y = np.array(values[masses[0]][par][lambdas112[0]])
#     e = np.array(errors[masses[0]][par][lambdas112[0]])
#     upper = y + e/2
#     lower = y - e/2
#     source = ColumnDataSource(data=dict(xscan=kappas111, values=y, upper=upper, lower=lower))
#     p.circle(x='xscan', y='values', source=source, legend_label=ntos(par), color=c, size=10)

#     # whisk = Whisker(base="xscan", upper="upper", lower="lower", source=source,
#     #                 level="annotation", line_width=8, line_color=c)
#     # whisk.upper_head.size=8
#     # whisk.lower_head.size=8
#     # p.add_layout(whisk)

# output_file(out+'.html')
# save(p)

import matplotlib
import matplotlib.pyplot as plt
import mplhep as hep
plt.style.use(hep.style.ROOT)
    
fig = plt.figure()
plt.title('Cross-section without resonance')
plt.xlabel(r'$k_{\lambda}$')
plt.ylabel(r'$\sigma$ [pb]')
for par,c in zip(sthetas, colors):
    plt.scatter(varscan, values[masses[0]][par][lambdas112[0]], 
                color=c, label=r"$s_{\theta}$="+str(par))
    plt.errorbar(varscan, values[masses[0]][par][lambdas112[0]], 
                 yerr=errors[masses[0]][par][lambdas112[0]], 
                 color=c, fmt='o')
    plt.plot(varscan, values[masses[0]][par][lambdas112[0]], 
             color=c)
plt.legend(loc="upper right")
plt.tight_layout()
plt.savefig(out+'1.png')

fig = plt.figure()
plt.title('Cross-section without resonance')
plt.xlabel(r'$k_{\lambda}$')
plt.ylabel(r'$\sigma$ [pb]')
for par,c in zip(lambdas112, colors):
    plt.scatter(varscan, values[masses[0]][sthetas[0]][par],
                color=c, label=r"$\lambda_{112}$="+str(par))
    plt.errorbar(varscan, values[masses[0]][sthetas[0]][par], 
                 yerr=errors[masses[0]][sthetas[0]][par], 
                 color=c, fmt='o')
    plt.plot(varscan, values[masses[0]][sthetas[0]][par], 
             color=c)
plt.legend(loc="upper right")
plt.tight_layout()
plt.savefig(out+'2.png')
