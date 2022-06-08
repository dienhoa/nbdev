# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/08_showdoc.ipynb.

# %% auto 0
__all__ = ['DocmentTbl', 'get_name', 'qual_name', 'ShowDocRenderer', 'BasicMarkdownRenderer', 'show_doc', 'BasicHtmlRenderer',
           'showdoc_nm']

# %% ../nbs/08_showdoc.ipynb 3
from fastcore.docments import *
from fastcore.utils import *
from importlib import import_module
from .doclinks import *
import inspect
from collections import OrderedDict
from dataclasses import dataclass, is_dataclass
from .read import get_config

# %% ../nbs/08_showdoc.ipynb 5
def _non_empty_keys(d:dict): return L([k for k,v in d.items() if v != inspect._empty])
def _bold(s): return f'**{s}**' if s.strip() else s

# %% ../nbs/08_showdoc.ipynb 6
def _maybe_nm(o): 
    if (o == inspect._empty): return ''
    else: return o.__name__ if hasattr(o, '__name__') else str(o)

# %% ../nbs/08_showdoc.ipynb 8
def _list2row(l:list): return '| '+' | '.join([_maybe_nm(o) for o in l]) + ' |'

# %% ../nbs/08_showdoc.ipynb 10
class DocmentTbl:
    # this is the column order we want these items to appear
    _map = OrderedDict({'anno':'Type', 'default':'Default', 'docment':'Details'})
    
    def __init__(self, obj, verbose=True, returns=True):
        "Compute the docment table string"
        self.verbose = verbose
        self.returns = False if isdataclass(obj) else returns
        self.params = L(inspect.signature(obj).parameters.keys())
        try: _dm = docments(obj, full=True, returns=returns)
        except: _dm = {}
        if 'self' in _dm: del _dm['self']
        for d in _dm.values(): d['docment'] = ifnone(d['docment'], inspect._empty)
        self.dm = _dm
    
    @property
    def _columns(self):
        "Compute the set of fields that have at least one non-empty value so we don't show tables empty columns"
        cols = set(flatten(L(self.dm.values()).filter().map(_non_empty_keys)))
        candidates = self._map if self.verbose else {'docment': 'Details'}
        return OrderedDict({k:v for k,v in candidates.items() if k in cols})
    
    @property
    def has_docment(self): return 'docment' in self._columns and self._row_list 

    @property
    def has_return(self): return self.returns and bool(_non_empty_keys(self.dm.get('return', {})))
    
    def _row(self, nm, props): 
        "unpack data for single row to correspond with column names."
        return [nm] + [props[c] for c in self._columns]
    
    @property
    def _row_list(self):
        "unpack data for all rows."
        ordered_params = [(p, self.dm[p]) for p in self.params if p != 'self']
        return L([self._row(nm, props) for nm,props in ordered_params])
    
    @property
    def _hdr_list(self): return ['  '] + [_bold(l) for l in L(self._columns.values())]

    @property
    def hdr_str(self):
        "The markdown string for the header portion of the table"
        md = _list2row(self._hdr_list)
        return md + '\n' + _list2row(['-' * len(l) for l in self._hdr_list])
    
    @property
    def params_str(self): 
        "The markdown string for the parameters portion of the table."
        return '\n'.join(self._row_list.map(_list2row))
    
    @property
    def return_str(self):
        "The markdown string for the returns portion of the table."
        return _list2row(['**Returns**']+[_bold(_maybe_nm(self.dm['return'][c])) for c in self._columns])
    
    def _repr_markdown_(self):
        if not self.has_docment: return ''
        _tbl = [self.hdr_str, self.params_str]
        if self.has_return: _tbl.append(self.return_str)
        return '\n'.join(_tbl)
    
    def __eq__(self,other): return self.__str__() == str(other).strip()

    def __str__(self): return self._repr_markdown_()

# %% ../nbs/08_showdoc.ipynb 29
def get_name(obj):
    "Get the name of `obj`"
    if hasattr(obj, '__name__'):       return obj.__name__
    elif getattr(obj, '_name', False): return obj._name
    elif hasattr(obj,'__origin__'):    return str(obj.__origin__).split('.')[-1] #for types
    elif type(obj)==property:          return _get_property_name(obj)
    else:                              return str(obj).split('.')[-1]

# %% ../nbs/08_showdoc.ipynb 30
def qual_name(obj):
    "Get the qualified name of `obj`"
    if hasattr(obj,'__qualname__'): return obj.__qualname__
    if inspect.ismethod(obj):       return f"{get_name(obj.__self__)}.{get_name(fn)}"
    return get_name(obj)

# %% ../nbs/08_showdoc.ipynb 31
class ShowDocRenderer:
    def __init__(self, sym, disp:bool=True):
        "Show documentation for `sym`"
        store_attr()
        self.nm = qual_name(sym)
        self.isfunc = inspect.isfunction(sym)
        self.sig = inspect.signature(sym)
        self.docs = docstring(sym)
        self.dm = DocmentTbl(sym)

# %% ../nbs/08_showdoc.ipynb 32
def _fmt_sig(sig):
    p = sig.parameters
    return "(" + ', '.join([str(p[k]) for k in p.keys() if k != 'self'])  + ")"

# %% ../nbs/08_showdoc.ipynb 33
class BasicMarkdownRenderer(ShowDocRenderer):
    def _repr_markdown_(self):
        doc = '---\n\n'
        if self.isfunc: doc += '#'
        doc += f'### {self.nm}\n\n> **`{self.nm}`**` {_fmt_sig(self.sig)}`'
        if self.docs: doc += f"\n\n{self.docs.splitlines()[0]}"
        if self.dm.has_docment: doc += f"\n\n{self.dm}"
        return doc

# %% ../nbs/08_showdoc.ipynb 34
def show_doc(sym, disp=True, renderer=None):
    if renderer is None: renderer = get_config().get('renderer', None)
    if renderer is None: renderer=BasicMarkdownRenderer
    elif isinstance(renderer,str):
        p,m = renderer.rsplit('.', 1)
        renderer = getattr(import_module(p), m)
    return renderer(sym or show_doc, disp=disp)

# %% ../nbs/08_showdoc.ipynb 46
class BasicHtmlRenderer(ShowDocRenderer):
    def _repr_html_(self):
        doc = '<hr/>\n'
        lvl = 4 if self.isfunc else 3
        doc += f'<h{lvl}>{self.nm}</h{lvl}>\n<blockquote><code>{self.nm}{self.sig}</code></blockquote>'
        if self.docs: doc += f"<p>{self.docs}</p>"
        return doc

# %% ../nbs/08_showdoc.ipynb 48
def showdoc_nm(tree):
    "Get the fully qualified name for showdoc."
    return ifnone(get_patch_name(tree), tree.name)
