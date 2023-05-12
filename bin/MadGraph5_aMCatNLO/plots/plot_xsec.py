import numpy as np
from bokeh.models import ColumnDataSource, Whisker
from bokeh.plotting import figure, save, output_file
# select a palette
from bokeh.palettes import Dark2_5 as palette
# itertools handles the cycling
import itertools 

import re
pattern_line = re.compile("     Cross-section : .*")
pattern_floats = re.compile(r"[+-]?\d+(?:\.\d+)?")

widths = ('narrow', '10pcts', '20pcts', '30pcts')
masses = ('250', '260', '270', '280', '300', '320', '350', '400',
          '450', '500', '550', '600', '650', '700', '750', '800',
          '850', '900', '1000', '1250', '1500', '1750', '2000', '2500', '3000')

values, errors = ({} for _ in range(2))
for w in widths:
    values[w], errors[w] = ([] for _ in range(2))
    wstr = str(w)
    for m in masses:
        found = False
        mstr = str(m)
        fname = 'Singlet_hh_' + wstr + '_M' + mstr + '.log'
        
        for i, line in enumerate(open(fname)):
            for match in re.finditer(pattern_line, line):
                tmp = pattern_floats.findall(line)
                if len(tmp) == 4:
                    val = float(tmp[0] + 'e' + tmp[1])
                    err = float(tmp[2] + 'e' + tmp[3])
                elif len(tmp) == 3:
                    val = float(tmp[0])
                    err = float(tmp[1] + 'e' + tmp[2])
                elif len(tmp) == 2:
                    val = float(tmp[0])
                    err = float(tmp[1])
                values[w].append(val)
                errors[w].append(err)
                found = True
                print(w, m)
                print(val, err)                
            if found:
                break

p = figure(height=600, width=1200, background_fill_color="#efefef", title="Cross-sections")
p.xgrid.grid_line_color = None

masses = np.array(masses).astype(float)
colors = itertools.cycle(palette)  

for w,c in zip(widths, colors):
    y = np.array(values[w])
    e = np.array(errors[w])
    upper = y + e/2
    lower = y - e/2
    source = ColumnDataSource(data=dict(masses=masses, values=y, upper=upper, lower=lower))
    p.circle(x='masses', y='values', source=source, legend_label=w, color=c, size=10)
    whisk = Whisker(base="masses", upper="upper", lower="lower", source=source,
                    level="annotation", line_width=8, line_color=c)
    whisk.upper_head.size=8
    whisk.lower_head.size=8
    #p.add_layout(whisk)

output_file("plot_xsec.html")
save(p)
