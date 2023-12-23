
import os
import operator
import collections
from dataclasses import dataclass, field
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

def calc_edges(arr):
    """Assumes the array `arr` is sorted."""
    assert len(arr)>2
    ret = [arr[0] - (arr[1]-arr[0])/2]
    for l,r in zip(arr[:-1],arr[1:]):
        new_edge = l + (r-l)/2
        ret.append(new_edge)
    ret.append(arr[-1]+(arr[-1]-arr[-2])/2)
    return ret

def colormap_discretize(cmap):
    return [mcolors.rgb2hex(cmap(i)) for i in range(cmap.N)]

class Contour:
    """Class for storing labels of a single plot."""
    def __init__(self, mode, x, y, z, colors, linestyles,
                 levels, pattern='/', band_width=0.15, leglabels=[], side='+'):
        self.mode = mode
        self.x = x
        self.y = y
        self.z = z
        self.colors = colors
        self.linestyles = linestyles
        self.levels = levels
        self.pattern = pattern
        self.leglabels = leglabels
        
        self.hatch_levels = None
        if side in ('+', '-'):
            self.hatch_levels = self._hatch_levels(band_width=band_width, op=side)
        self.hatch_types  = self._hatch_types()
    
    def _fmt_gamma(self, x):
        Gamma = '\u0393'
        s = Gamma + f"/M={x:.1f}"
        if s.endswith("0"):
            s = Gamma + f"/$M_{{X}}$={x:.0f}"
        return rf"{s} \%" if plt.rcParams["text.usetex"] else f"{s} %"

    def _fmt_limit(self, x):
        #s = f"{x:.5f}"
        s = ""
        return s

    def fmt(self, x):
        if self.mode == 'gamma':
            return self._fmt_gamma(x)
        elif self.mode == 'limit':
            return None #self._fmt_limit(x)

    def _hatch_levels(self, band_width, op):
        """Produce hatch levels from contour levels."""
        ret = [None]*2*len(self.levels)
        if op=='+':
            sign = operator.add
            ret[::2] = self.levels
            ret[1::2] = [sign(1, band_width)*x for x in self.levels]
        elif op=='-':
            sign = operator.sub
            ret[1::2] = self.levels
            ret[::2] = [sign(1, band_width)*x for x in self.levels]            
        return ret

    def _hatch_types(self):
        """Produce hatch levels from contour levels."""
        ret = [None]*2*len(self.levels)
        ret[::2] = [5*self.pattern for _ in range(len(self.levels))]
        ret[1::2] = [None for _ in range(len(self.levels))]
        return ret

        
def create_dir(adir):
    if not os.path.exists(adir):
        os.makedirs(adir)

@dataclass
class Labels:
    """Class for storing labels of a single plot."""
    title: str
    out: str
    xlabel: str
    ylabel: str
    zlabel: str
    labelpad: int
    leglabels: list[str] = field(default_factory=list)
    legloc: str = "upper left"
        
def ntos(n):
    """Converts float to string"""
    assert isinstance(n, float)
    return '{0:.2f}'.format(n).replace('.', 'p').replace('-', 'm')

def pp(v):
    return str(v).replace('.','p').replace('-','m')
    
def recursive_dict():
    return collections.defaultdict(recursive_dict)
