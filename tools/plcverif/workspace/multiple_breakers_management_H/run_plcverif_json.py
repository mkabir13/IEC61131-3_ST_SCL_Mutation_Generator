#!/usr/bin/env python3
"""
run_plcverif_json.py - generic PLCverif runner for JSON property datasets.

Usage
  python3 run_plcverif_json.py F_CollectInput_m.json            # one dataset
  python3 run_plcverif_json.py *.json                           # several
  python3 run_plcverif_json.py dataset_dir/ [--recursive]       # every *.json in a folder
  python3 run_plcverif_json.py X.json --dry-run                 # write VC3 + prepared source only

Each JSON is paired with the .scl/.st file of the same name (or a "source_file"
key in the JSON). Batch runs write batch_summary.csv next to the first input.

What the runner does to make arbitrary SCL verifiable with NuSMV/nuXmv
  1. Dynamic array indexing. PLCverif's NuSMV path enumerates arrays into
     scalars and cannot handle A[expr] with a variable index ("enumerate
     arrays" error). Every such read/write is rewritten into a CASE over the
     constant indices of the array's declared range. Writes outside the range
     set a static flag pv_oob (FBs only), so out-of-bounds accesses stay
     detectable: check  NOT instance.pv_oob  as an extra invariant.
  2. TIA-only integer types (USInt, SInt, UInt) are widened for Step7v55.
  Both happen in a copy (<json>_vc3/<name>.prepared.scl). The original file
  is never modified, and line numbers are preserved (generated code is put on
  the line of the statement it replaces), so PLCverif's line numbers still
  point at your original source.

Other behaviour
  * Backend algorithm validated: auto = Ic3 with nuXmv, Classic with NuSMV.
  * Entry block chosen per property from the variables it references; nested
    instance paths rewritten (instance.j -> instance.CollectInput.j).
  * Dataset "entry_point" is used when that block can see the variables.
  * Bool compared with 0/1 rewritten to FALSE/TRUE.
  * Assertion requirements (//#ASSERT) are run.
  * Unknown "property" keys are passed through as -job.req.<key>.
  * Result classified from PLCverif text output, never from the exit code.
"""

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from collections import deque, namedtuple
from dataclasses import dataclass, field
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PLCVERIF = SCRIPT_DIR.parent / "plcverif-cli"
NUSMV_ALGORITHMS = ("Classic", "Ic3", "Bmc")
EXIT_OK, EXIT_VIOLATED, EXIT_ERROR = 0, 1, 2
MAX_CASE_BRANCHES = 4096        # per rewritten access (product over dynamic dims)

# Keys datasets put in "property" that are metadata, not PLCverif settings
META_KEYS = ('pattern_description', 'description', 'comment', 'notes')


class SetupError(Exception):
    """A dataset could not be prepared (missing file, bad JSON, ...)."""


# ============================================================
# LEXING HELPERS
# ============================================================

def mask_code(text):
    """Same-length copy of text with comments, pragmas and strings blanked
    (newlines kept), so code can be scanned without tripping on them."""
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        if text.startswith('//', i):
            j = text.find('\n', i)
            j = n if j < 0 else j
        elif text.startswith('(*', i):
            j = text.find('*)', i + 2)
            j = n if j < 0 else j + 2
        elif text.startswith('/*', i):
            j = text.find('*/', i + 2)
            j = n if j < 0 else j + 2
        elif text[i] == '{':
            j = text.find('}', i)
            j = n if j < 0 else j + 1
        elif text[i] == "'":
            j = i + 1
            while j < n:
                if text[j] == "'":
                    if j + 1 < n and text[j + 1] == "'":
                        j += 2
                        continue
                    break
                j += 1
            j = min(j + 1, n)
        else:
            i += 1
            continue
        for k in range(i, j):
            if out[k] not in '\r\n':
                out[k] = ' '
        i = j
    return ''.join(out)


Tok = namedtuple('Tok', 'kind text start end')
TOKEN_RE = re.compile(r'''
   (?P<ws>\s+)
 | (?P<lit>[A-Za-z_]\w*\#[\w.:+\-]+)          # typed literal: T#5s, INT#3, 16#FF
 | (?P<id>\#?[A-Za-z_]\w*|"[^"\n]*")          # identifier, #local, "quoted"
 | (?P<num>\d[\w.]*(?:\#[\w.]+)?)             # 12, 1.5, 16#FF
 | (?P<op>:=|=>|\.\.|<=|>=|<>|\*\*|[-+*/=<>()\[\],;:.&^\#])
 | (?P<other>.)
''', re.X | re.S)


def tokenize(masked, start=0, end=None):
    end = len(masked) if end is None else end
    toks = []
    for m in TOKEN_RE.finditer(masked, start, end):
        if m.lastgroup == 'ws':
            continue
        toks.append(Tok(m.lastgroup, m.group(), m.start(), m.end()))
    return toks


def upper(tok):
    return tok.text.upper() if tok is not None and tok.kind == 'id' else (tok.text if tok else None)


def is_const_index(s):
    return re.fullmatch(r'\s*[+-]?\s*\d+\s*', s) is not None


# ============================================================
# SOURCE MODEL
# ============================================================

@dataclass
class Var:
    name: str
    type: str          # declared type text, quotes removed
    base_type: str     # element type for arrays (quotes removed), else same as type
    raw_base: str      # element type as written (quotes kept) - for declarations
    is_array: bool
    dims: list         # [(lo, hi), ...] for arrays with literal bounds, else None
    section: str


@dataclass
class Pou:
    kind: str
    name: str
    order: int
    vars: dict = field(default_factory=dict)
    has_assertions: bool = False


POU_RE = re.compile(
    r'\b(FUNCTION_BLOCK|PROGRAM|FUNCTION|ORGANIZATION_BLOCK)\s+'
    r'(?:"([^"]+)"|([A-Za-z_]\w*))'
    r'(.*?)\bEND_\1\b',
    re.S | re.I,
)
VAR_SECTION_RE = re.compile(
    r'\b(VAR(?:_INPUT|_OUTPUT|_IN_OUT|_TEMP|_STAT|_GLOBAL|_EXTERNAL)?)\b'
    r'((?:\s+(?:CONSTANT|RETAIN|NON_RETAIN|DB_SPECIFIC)\b)*)'
    r'(.*?)\bEND_VAR\b',
    re.S | re.I,
)
ASSERT_RE = re.compile(r'(//\s*#\s*ASSERT\b|\(\*\s*#\s*ASSERT\b)', re.I)
ARRAY_RE = re.compile(r'^ARRAY\s*\[(.*?)\]\s*OF\s+(.+)$', re.S | re.I)


def parse_declarations(body, section):
    body = re.sub(r'\bSTRUCT\b.*?\bEND_STRUCT\b', 'Struct', body, flags=re.S | re.I)
    out = []
    for decl in body.split(';'):
        decl = decl.strip()
        if not decl:
            continue
        m = re.match(r'^([A-Za-z_][\w\s,]*?)\s*(?:\bAT\b[^:]*)?:(?!=)\s*(.+)$', decl, re.S)
        if not m:
            continue
        names = [n.strip() for n in m.group(1).split(',') if n.strip()]
        raw = re.sub(r'\s+', ' ', re.split(r':=', m.group(2), maxsplit=1)[0].strip())
        am = ARRAY_RE.match(raw)
        dims = None
        if am:
            raw_base = am.group(2).strip()
            dims = []
            for part in am.group(1).split(','):
                bm = re.fullmatch(r'\s*([+-]?\d+)\s*\.\.\s*([+-]?\d+)\s*', part)
                if not bm:
                    dims = None
                    break
                dims.append((int(bm.group(1)), int(bm.group(2))))
        else:
            raw_base = raw
        for n in names:
            out.append(Var(n, raw.replace('"', ''), raw_base.replace('"', ''),
                           raw_base, bool(am), dims, section.upper()))
    return out


def parse_source_text(raw):
    masked = mask_code(raw)
    pous = {}
    for order, m in enumerate(POU_RE.finditer(masked)):
        kind = m.group(1).upper()
        name = m.group(2) or m.group(3)
        pou = Pou(kind=kind, name=name, order=order)
        pou.has_assertions = bool(ASSERT_RE.search(raw[m.start(4):m.end(4)]))
        body = masked[m.start(4):m.end(4)]
        for sm in VAR_SECTION_RE.finditer(body):
            for v in parse_declarations(sm.group(3), sm.group(1)):
                pou.vars.setdefault(v.name.lower(), v)
        pous[name.lower()] = pou
    return pous


def child_block(pous, var):
    if var.is_array:
        return None
    pou = pous.get(var.base_type.lower())
    return pou if pou and pou.kind == 'FUNCTION_BLOCK' else None


def top_level_blocks(pous):
    instantiated = {
        child_block(pous, v).name.lower()
        for p in pous.values() for v in p.vars.values()
        if child_block(pous, v)
    }
    tops = [p for p in pous.values() if p.name.lower() not in instantiated]
    return sorted(tops or pous.values(), key=lambda p: p.order)


def reachable_blocks(pous, start):
    seen, stack = set(), [start]
    while stack:
        p = stack.pop()
        if p.name.lower() in seen:
            continue
        seen.add(p.name.lower())
        stack.extend(c for c in (child_block(pous, v) for v in p.vars.values()) if c)
    return seen


def subtree_has_assertions(pous, pou):
    return any(pous[n].has_assertions for n in reachable_blocks(pous, pou))


def find_paths(pous, start, name, max_depth=8):
    found, best = [], None
    q = deque([(start, [])])
    while q:
        pou, path = q.popleft()
        if best is not None and len(path) > best:
            break
        if name.lower() in pou.vars:
            found.append(path)
            best = len(path)
            continue
        if len(path) >= max_depth:
            continue
        for v in pou.vars.values():
            c = child_block(pous, v)
            if c:
                q.append((c, path + [v.name]))
    return found


# ============================================================
# SOURCE PREPARATION 1: DYNAMIC ARRAY INDEXING -> CASE
# ============================================================

STMT_KEYWORDS = {'IF', 'CASE', 'FOR', 'WHILE', 'REPEAT', 'EXIT', 'CONTINUE',
                 'RETURN', 'GOTO'}


class StmtParser:
    """Small SCL statement parser over tokens. Nodes keep token index ranges."""

    def __init__(self, toks):
        self.t = toks
        self.i = 0

    def peek(self, k=0):
        j = self.i + k
        return self.t[j] if j < len(self.t) else None

    def scan_to(self, stops):
        """Advance to the first depth-0 token whose upper text is in stops."""
        depth = 0
        while self.i < len(self.t):
            tok = self.t[self.i]
            u = upper(tok)
            if depth == 0 and u in stops:
                return
            if tok.text in ('(', '['):
                depth += 1
            elif tok.text in (')', ']'):
                depth -= 1
            self.i += 1

    def skip_semicolon(self):
        if self.peek() is not None and self.peek().text == ';':
            self.i += 1

    def is_case_label(self):
        if upper(self.peek()) in STMT_KEYWORDS:
            return False
        depth = 0
        j = self.i
        while j < len(self.t):
            x = self.t[j].text
            if x in ('(', '['):
                depth += 1
            elif x in (')', ']'):
                depth -= 1
            elif depth == 0 and x in (':', ':=', ';'):
                return x == ':'
            j += 1
        return False

    def parse_block(self, stops, case_labels=False):
        out = []
        while self.i < len(self.t):
            u = upper(self.peek())
            if u in stops:
                break
            if case_labels and self.is_case_label():
                break
            before = self.i
            node = self.parse_statement()
            if node:
                out.append(node)
            if self.i == before:          # safety: never loop forever
                self.i += 1
        return out

    def parse_statement(self):
        tok = self.peek()
        u = upper(tok)
        start = self.i
        if tok.text == ';':
            self.i += 1
            return None
        if u == 'IF':
            self.i += 1
            conds, blocks = [], []
            c = self.i
            self.scan_to({'THEN'})
            conds.append((c, self.i))
            self.i += 1
            blocks.append(self.parse_block({'ELSIF', 'ELSE', 'END_IF'}))
            while upper(self.peek()) == 'ELSIF':
                self.i += 1
                c = self.i
                self.scan_to({'THEN'})
                conds.append((c, self.i))
                self.i += 1
                blocks.append(self.parse_block({'ELSIF', 'ELSE', 'END_IF'}))
            if upper(self.peek()) == 'ELSE':
                self.i += 1
                blocks.append(self.parse_block({'END_IF'}))
            self.i += 1
            self.skip_semicolon()
            return {'k': 'if', 'start': start, 'conds': conds, 'blocks': blocks}
        if u == 'CASE':
            self.i += 1
            s = self.i
            self.scan_to({'OF'})
            sel = (s, self.i)
            self.i += 1
            blocks = []
            while self.i < len(self.t) and upper(self.peek()) not in ('END_CASE',):
                if upper(self.peek()) == 'ELSE':
                    self.i += 1
                    blocks.append(self.parse_block({'END_CASE'}))
                    continue
                self.scan_to({':'})            # label list
                self.i += 1
                blocks.append(self.parse_block({'END_CASE', 'ELSE'}, case_labels=True))
            self.i += 1
            self.skip_semicolon()
            return {'k': 'case', 'start': start, 'sel': sel, 'blocks': blocks}
        if u == 'FOR':
            self.i += 1
            s = self.i
            self.scan_to({'DO'})
            bounds = (s, self.i)
            self.i += 1
            body = self.parse_block({'END_FOR'})
            self.i += 1
            self.skip_semicolon()
            return {'k': 'for', 'start': start, 'bounds': bounds, 'body': body}
        if u == 'WHILE':
            self.i += 1
            s = self.i
            self.scan_to({'DO'})
            cond = (s, self.i)
            self.i += 1
            body = self.parse_block({'END_WHILE'})
            end_tok = self.i
            self.i += 1
            self.skip_semicolon()
            return {'k': 'while', 'start': start, 'cond': cond, 'body': body, 'end_tok': end_tok}
        if u == 'REPEAT':
            self.i += 1
            body = self.parse_block({'UNTIL'})
            until_tok = self.i
            self.i += 1
            c = self.i
            self.scan_to({'END_REPEAT'})
            cond = (c, self.i)
            self.i += 1
            self.skip_semicolon()
            return {'k': 'repeat', 'start': start, 'body': body, 'cond': cond,
                    'until_tok': until_tok}
        # simple statement: assignment, call, EXIT, RETURN, ...
        self.scan_to({';', 'END_IF', 'ELSIF', 'ELSE', 'END_CASE', 'END_FOR',
                      'END_WHILE', 'UNTIL', 'END_REPEAT'})
        end = self.i
        self.skip_semicolon()
        if u in STMT_KEYWORDS:
            return None
        assign_at = None
        depth = 0
        for j in range(start, end):
            x = self.t[j].text
            if x in ('(', '['):
                depth += 1
            elif x in (')', ']'):
                depth -= 1
            elif depth == 0 and x == ':=':
                assign_at = j
                break
        if assign_at is not None:
            return {'k': 'assign', 'start': start, 'lhs': (start, assign_at),
                    'rhs': (assign_at + 1, end), 'end': self.i}
        if any(self.t[j].text == '(' for j in range(start, end)):
            return {'k': 'call', 'start': start, 'body': (start, end), 'end': self.i}
        return None


Ref = namedtuple('Ref', 'var name_start bracket_start end idx')


class ArrayRewriter:
    """Rewrites variable-indexed accesses of one POU's arrays into CASE dispatch."""

    def __init__(self, pou, text, masked, hash_style, notes, warnings):
        self.pou = pou
        self.arrays = {k: v for k, v in pou.vars.items() if v.is_array}
        self.text = text
        self.masked = masked
        self.h = '#' if hash_style else ''
        self.notes = notes
        self.warnings = warnings
        self.used = set(pou.vars)
        self.temps = []                 # (name, raw_type)
        self.need_oob = False
        self.oob = self._fresh('pv_oob')
        self.count = 0
        self.can_flag = pou.kind in ('FUNCTION_BLOCK', 'PROGRAM')

    def _fresh(self, base):
        name, n = base, 1
        while name.lower() in self.used:
            n += 1
            name = f'{base}{n}'
        self.used.add(name.lower())
        return name

    def new_temp(self, raw_type):
        name = self._fresh(f'pv_tmp{len(self.temps) + 1}')
        self.temps.append((name, raw_type))
        return self.h + name

    def line_of(self, pos):
        return self.text.count('\n', 0, pos) + 1

    # ---------- reference discovery in a text fragment ----------
    def find_refs(self, s):
        toks = tokenize(mask_code(s))
        refs = []
        for i, t in enumerate(toks):
            if t.kind != 'id':
                continue
            var = self.arrays.get(t.text.lstrip('#').lower())
            if var is None or (i > 0 and toks[i - 1].text == '.'):
                continue
            if i + 1 >= len(toks) or toks[i + 1].text != '[':
                continue
            depth, j, seg, dims = 0, i + 1, i + 2, []
            while j < len(toks):
                x = toks[j].text
                if x in ('(', '['):
                    depth += 1
                elif x in (')', ']'):
                    depth -= 1
                    if depth == 0:
                        break
                elif x == ',' and depth == 1:
                    dims.append((seg, j))
                    seg = j + 1
                j += 1
            if j >= len(toks):
                continue
            dims.append((seg, j))
            idx = [s[toks[a].start:toks[b - 1].end] if b > a else '' for a, b in dims]
            refs.append(Ref(var, t.start, toks[i + 1].start, toks[j].end, idx))
        return refs

    @staticmethod
    def dynamic(ref):
        return any(not is_const_index(d) for d in ref.idx)

    def supported(self, ref, where):
        v = ref.var
        if v.dims is None or len(v.dims) != len(ref.idx):
            self._warn(f"{where}: array '{v.name}' has non-literal bounds; access not rewritten")
            return False
        size = 1
        for d, (lo, hi) in zip(ref.idx, v.dims):
            if not is_const_index(d):
                size *= (hi - lo + 1)
        if size > MAX_CASE_BRANCHES:
            self._warn(f"{where}: access to '{v.name}' needs {size} CASE branches; not rewritten")
            return False
        return True

    def _warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)

    # ---------- code generation ----------
    def case_chain(self, ref, name_txt, make_stmt, else_stmt=None):
        def build(d, chosen):
            if d == len(ref.idx):
                return make_stmt(f"{name_txt}[{', '.join(chosen)}]")
            idx = ref.idx[d].strip()
            if is_const_index(idx):
                return build(d + 1, chosen + [re.sub(r'\s+', '', idx)])
            lo, hi = ref.var.dims[d]
            parts = [f'CASE {idx} OF']
            for c in range(lo, hi + 1):
                parts.append(f'{c}: {build(d + 1, chosen + [str(c)])}')
            if else_stmt:
                parts.append(f'ELSE {else_stmt}')
            parts.append('END_CASE;')
            return ' '.join(parts)
        return build(0, [])

    def rewrite_reads(self, s, where):
        """Hoist variable-indexed reads in s into temps. Returns (prefix, new_s)."""
        prefix = []
        while True:
            refs = [r for r in self.find_refs(s) if self.dynamic(r)]
            inner = [r for r in refs
                     if not any(self.dynamic(q) for d in r.idx for q in self.find_refs(d))
                     and self.supported(r, where)]
            if not inner:
                break
            r = inner[0]
            tmp = self.new_temp(r.var.raw_base)
            name_txt = s[r.name_start:r.bracket_start].strip()
            prefix.append(self.case_chain(r, name_txt, lambda acc: f'{tmp} := {acc};'))
            s = s[:r.name_start] + tmp + s[r.end:]
            self.count += 1
        return (' '.join(prefix) + ' ') if prefix else '', s

    def rewrite_assignment(self, lhs, rhs, where):
        pre, rhs2 = self.rewrite_reads(rhs, where)
        lead = len(lhs) - len(lhs.lstrip())
        target = next((r for r in self.find_refs(lhs) if r.name_start == lead), None)
        if target is None or not self.dynamic(target):
            p2, lhs2 = self.rewrite_reads(lhs, where)        # indices of other arrays
            return pre + p2, lhs2, rhs2, None
        new_idx = []
        for d in target.idx:
            p, nd = self.rewrite_reads(d, where)
            pre += p
            new_idx.append(nd)
        target = target._replace(idx=new_idx)
        name_txt = lhs[target.name_start:target.bracket_start].strip()
        rest = lhs[target.end:]
        if not self.dynamic(target):
            return pre, f"{name_txt}[{', '.join(i.strip() for i in new_idx)}]{rest}", rhs2, None
        if not self.supported(target, where):
            return pre, lhs, rhs2, None
        if re.search(r'\[[^\]]*[A-Za-z#]', mask_code(rest)):
            self._warn(f'{where}: nested variable index after {name_txt}[...] not rewritten')
        else_stmt = None
        if self.can_flag:
            self.need_oob = True
            else_stmt = f'{self.h}{self.oob} := TRUE;'
        self.count += 1
        if not rest.strip():
            tmp = self.new_temp(target.var.raw_base)
            code = f'{tmp} := {rhs2.strip()}; ' + self.case_chain(
                target, name_txt, lambda acc: f'{acc} := {tmp};', else_stmt)
        else:
            code = self.case_chain(
                target, name_txt, lambda acc: f'{acc}{rest} := {rhs2.strip()};', else_stmt)
        return pre, None, None, code

    # ---------- statement walk ----------
    def span(self, toks, a, b):
        if b <= a:
            return None
        return toks[a].start, toks[b - 1].end

    def process(self, nodes, toks, edits):
        for n in nodes:
            k = n['k']
            where = f"line {self.line_of(toks[n['start']].start)}"
            if k == 'assign':
                ls, le = self.span(toks, *n['lhs'])
                rs_e = self.span(toks, *n['rhs'])
                lhs = self.text[ls:le]
                rhs = self.text[rs_e[0]:rs_e[1]] if rs_e else ''
                pre, lhs2, rhs2, code = self.rewrite_assignment(lhs, rhs, where)
                end = toks[n['end'] - 1].end
                if code is not None:
                    edits.append((ls, end, pre + code))
                elif pre or lhs2 != lhs or rhs2 != rhs:
                    edits.append((ls, end, f'{pre}{lhs2} := {rhs2.strip()};'))
            elif k == 'call':
                s, e = self.span(toks, *n['body'])
                stmt = self.text[s:e]
                if re.search(r'=>\s*#?\w+\s*\[', mask_code(stmt)):
                    self._warn(f'{where}: array element used as call output (=>) not rewritten')
                pre, new = self.rewrite_reads(stmt, where)
                if pre:
                    edits.append((s, e, pre + new))
            elif k in ('if', 'case', 'for', 'while', 'repeat'):
                ranges = (n['conds'] if k == 'if' else
                          [n['sel']] if k == 'case' else
                          [n['bounds']] if k == 'for' else [n['cond']])
                prefix = ''
                for a, b in ranges:
                    sp = self.span(toks, a, b)
                    if not sp:
                        continue
                    pre, new = self.rewrite_reads(self.text[sp[0]:sp[1]], where)
                    if pre:
                        prefix += pre
                        edits.append((sp[0], sp[1], new))
                if prefix:
                    if k == 'repeat':
                        pos = toks[n['until_tok']].start
                        edits.append((pos, pos, prefix))
                    else:
                        pos = toks[n['start']].start
                        edits.append((pos, pos, prefix))
                        if k == 'while':          # condition is re-evaluated each pass
                            endpos = toks[n['end_tok']].start
                            edits.append((endpos, endpos, prefix))
                for block in (n.get('blocks') or [n.get('body') or []]):
                    self.process(block, toks, edits)


def apply_edits(text, edits):
    for s, e, rep in sorted(edits, key=lambda x: (x[0], x[1]), reverse=True):
        text = text[:s] + rep + text[e:]
    return text


def rewrite_dynamic_arrays(text, pous):
    """Returns (new_text, notes, warnings)."""
    masked = mask_code(text)
    edits, notes, warnings = [], [], []
    for m in POU_RE.finditer(masked):
        name = m.group(2) or m.group(3)
        pou = pous.get(name.lower())
        if pou is None or not any(v.is_array for v in pou.vars.values()):
            continue
        b0, b1 = m.start(4), m.end(4)
        bm = re.search(r'\bBEGIN\b', masked[b0:b1], re.I)
        if bm:
            code_start, decl_end = b0 + bm.end(), b0 + bm.start()
        else:                                   # classic SCL without BEGIN is rare
            continue
        hash_style = re.search(r'#[A-Za-z_]', masked[code_start:b1]) is not None
        rw = ArrayRewriter(pou, text, masked, hash_style, notes, warnings)
        toks = tokenize(masked, code_start, b1)
        rw.process(StmtParser(toks).parse_block(set()), toks, edits)
        if rw.count == 0:
            continue
        notes.append(f'{pou.name}: {rw.count} variable-indexed array access(es) '
                     f'rewritten to CASE over constant indices')
        # declarations, inserted inline so line numbers do not move
        sections = list(VAR_SECTION_RE.finditer(masked, b0, decl_end))
        if rw.temps:
            decl = ' '.join(f'{n} : {t};' for n, t in rw.temps) + ' '
            temp_sec = next((s for s in sections if s.group(1).upper() == 'VAR_TEMP'), None)
            if temp_sec:
                edits.append((temp_sec.end(3), temp_sec.end(3), decl))
            else:
                edits.append((decl_end, decl_end, f'VAR_TEMP {decl}END_VAR '))
        if rw.need_oob:
            decl = f'{rw.oob} : Bool := FALSE; '
            stat = next((s for s in sections if s.group(1).upper() in ('VAR', 'VAR_STAT')
                         and 'CONSTANT' not in s.group(2).upper()), None)
            if stat:
                edits.append((stat.end(3), stat.end(3), decl))
            else:
                edits.append((decl_end, decl_end, f'VAR {decl}END_VAR '))
            notes.append(f"{pou.name}: out-of-range writes set '{rw.oob}'; "
                         f"check 'NOT instance.{rw.oob}' to verify array bounds")
    return apply_edits(text, edits), notes, warnings


# ============================================================
# SOURCE PREPARATION 0: CLOSED TOP-LEVEL BLOCKS -> FREE INPUTS
# ============================================================
# PLCverif gives arbitrary values each cycle only to the entry block's
# inputs. An IEC "PROGRAM MAIN" ported to an SCL FUNCTION_BLOCK often keeps
# its I/O signals as plain VAR, so they stay at their initial value forever
# and every property is checked on a single, input-free run (vacuous).
# For top-level blocks WITHOUT any VAR_INPUT / VAR_IN_OUT, scalar statics
# that the block never writes and that have no non-default initial value
# are moved to VAR_INPUT in the prepared copy.

ELEMENTARY = {'bool', 'byte', 'word', 'dword', 'lword', 'sint', 'int', 'dint', 'lint',
              'usint', 'uint', 'udint', 'ulint', 'real', 'lreal', 'char', 'wchar',
              'time', 'ltime', 's5time', 'date', 'time_of_day', 'tod',
              'date_and_time', 'dt'}
DEFAULT_INIT_RE = re.compile(r'^\s*(FALSE|[+-]?0+(\.0*)?|T#0\w*|0\.0)\s*$', re.I)


def assigned_names(pou, pous, nodes, toks):
    """Lower-case names of variables written anywhere in the statement tree."""
    out = set()

    def walk(ns):
        for n in ns:
            k = n['k']
            if k == 'assign':
                out.add(toks[n['lhs'][0]].text.lstrip('#').strip('"').lower())
            elif k == 'call':
                a, b = n['body']
                head = toks[a].text.lstrip('#').strip('"').lower()
                v = pou.vars.get(head)
                callee = child_block(pous, v) if v else pous.get(head)
                depth = 0
                for j in range(a, b):
                    x = toks[j].text
                    if x in ('(', '['):
                        depth += 1
                    elif x in (')', ']'):
                        depth -= 1
                    elif (depth == 1 and toks[j].kind == 'id' and j + 2 < b
                          and toks[j + 1].text in (':=', '=>') and toks[j + 2].kind == 'id'):
                        formal = toks[j].text.lstrip('#').lower()
                        actual = toks[j + 2].text.lstrip('#').lower()
                        if toks[j + 1].text == '=>':
                            out.add(actual)
                        elif callee is None:
                            out.add(actual)                     # unknown callee: conservative
                        elif formal in callee.vars and callee.vars[formal].section == 'VAR_IN_OUT':
                            out.add(actual)
            elif k == 'for':
                out.add(toks[n['bounds'][0]].text.lstrip('#').lower())
            if k in ('if', 'case'):
                for block in n['blocks']:
                    walk(block)
            elif k in ('for', 'while', 'repeat'):
                walk(n['body'])
    walk(nodes)
    return out


def free_closed_inputs(text, pous):
    masked = mask_code(text)
    edits, notes, warnings = [], [], []
    tops = {p.name.lower() for p in top_level_blocks(pous)}
    for m in POU_RE.finditer(masked):
        name = m.group(2) or m.group(3)
        pou = pous.get(name.lower())
        if (pou is None or name.lower() not in tops
                or pou.kind not in ('FUNCTION_BLOCK', 'PROGRAM')
                or any(v.section in ('VAR_INPUT', 'VAR_IN_OUT') for v in pou.vars.values())):
            continue
        b0, b1 = m.start(4), m.end(4)
        bm = re.search(r'\bBEGIN\b', masked[b0:b1], re.I)
        if not bm:
            continue
        decl_end = b0 + bm.start()
        toks = tokenize(masked, b0 + bm.end(), b1)
        written = assigned_names(pou, pous, StmtParser(toks).parse_block(set()), toks)
        moved = []
        for sm in VAR_SECTION_RE.finditer(masked, b0, decl_end):
            if sm.group(1).upper() not in ('VAR', 'VAR_STAT') or 'CONSTANT' in sm.group(2).upper():
                continue
            sec_moved = []
            for dm in re.finditer(r'[^;]*;', masked[sm.start(3):sm.end(3)]):
                ds, de = sm.start(3) + dm.start(), sm.start(3) + dm.end()
                decl = masked[ds:de]
                pm = re.match(r'^\s*([A-Za-z_]\w*)\s*:(?!=)\s*([^:;]+?)\s*(?::=\s*([^;]*?))?\s*;\s*$',
                              decl, re.S)
                if not pm:
                    continue
                vname, vtype, init = pm.group(1), pm.group(2).strip(), pm.group(3)
                if (vtype.lower() not in ELEMENTARY or vname.lower() in written
                        or (init is not None and not DEFAULT_INIT_RE.match(init))):
                    continue
                sec_moved.append(re.sub(r'\s+', ' ', decl.strip()))
                edits.append((ds, de, ''.join(c if c in '\r\n' else ' ' for c in text[ds:de])))
                moved.append(vname)
            if sec_moved:
                pos = sm.start(1)
                edits.append((pos, pos, 'VAR_INPUT ' + ' '.join(sec_moved) + ' END_VAR '))
        if moved:
            notes.append(f"{pou.name}: block has no inputs; never-written statics {moved} "
                         f"declared as VAR_INPUT so they take arbitrary values each cycle "
                         f"(disable with --no-free-inputs)")
        else:
            warnings.append(f"{pou.name}: block has no inputs and nothing could be freed; "
                            f"with it as entry the model is deterministic")
    return apply_edits(text, edits), notes, warnings


# ============================================================
# SOURCE PREPARATION 2: TIA-ONLY TYPES FOR STEP7 V5.5
# ============================================================

STEP7V55_WIDENING = {'usint': 'Int', 'sint': 'Int', 'uint': 'DInt'}
STEP7V55_NO_SAFE_MAP = ('udint', 'lint', 'ulint', 'lreal', 'lword', 'wstring', 'wchar')


def widen_types(text):
    names = '|'.join(STEP7V55_WIDENING)
    masked = mask_code(text)
    changes, warnings, edits = [], [], []
    for m in re.finditer(rf'(:\s*|\bOF\s+)({names})\b(?!\s*#)', masked, re.I):
        new = STEP7V55_WIDENING[m.group(2).lower()]
        edits.append((m.start(2), m.end(2), new))
        changes.append(f'line {masked.count(chr(10), 0, m.start()) + 1}: {m.group(2)} -> {new}')
    for m in re.finditer(rf'\b({names})#', masked, re.I):
        edits.append((m.start(), m.end(), ''))
        changes.append(f'line {masked.count(chr(10), 0, m.start()) + 1}: typed literal '
                       f'{m.group(0)}... -> untyped')
    for t in STEP7V55_WIDENING:
        if re.search(rf'\b{t}_TO_|_TO_{t}\b', masked, re.I):
            warnings.append(f'conversion functions involving {t.upper()} remain; '
                            f'PLCverif may still reject them')
    for t in STEP7V55_NO_SAFE_MAP:
        if re.search(rf'(:\s*|\bOF\s+){t}\b', masked, re.I):
            warnings.append(f'type {t.upper()} has no lossless Step7v55 equivalent; left unchanged')
    return apply_edits(text, edits), changes, warnings


def prepare_source(source_file, out_dir, cfg, pous):
    """Returns (path_to_verify, notes, warnings)."""
    raw = source_file.read_bytes().decode('utf-8', errors='surrogateescape')
    text, notes, warnings = raw, [], []
    if not cfg.no_free_inputs:
        text, n, w = free_closed_inputs(text, pous)
        notes += n
        warnings += w
    if cfg.backend == 'nusmv' and not cfg.no_array_rewrite:
        text, n, w = rewrite_dynamic_arrays(text, pous)
        notes += n
        warnings += w
    if cfg.compiler.lower().startswith('step7v5') and not cfg.no_normalize:
        text, n, w = widen_types(text)
        notes += [f'type widening {c}' for c in n]
        warnings += w
        if n:
            notes.append('widened types keep every value of the original range; '
                         'only overflow wrap-around differs')
    if text == raw:
        return source_file, notes, warnings
    out = out_dir / f'{source_file.stem}.prepared{source_file.suffix}'
    out.write_bytes(text.encode('utf-8', errors='surrogateescape'))
    return out, notes, warnings


# ============================================================
# EXPRESSION HANDLING (requirements)
# ============================================================

REF_RE = re.compile(r'\binstance\.([A-Za-z_]\w*)')
PATH_CMP_RE = re.compile(
    r'(\binstance(?:\.[A-Za-z_]\w*(?:\[[^\]]*\])?)+)(\s*(?:=|<>)\s*)([01])(?![\w.])'
)
DYN_INDEX_IN_REQ_RE = re.compile(r'\[[^\]]*[A-Za-z_][^\]]*\]')


def collect_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from collect_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from collect_strings(v)


def map_strings(value, fn):
    if isinstance(value, str):
        return fn(value)
    if isinstance(value, dict):
        return {k: map_strings(v, fn) for k, v in value.items()}
    if isinstance(value, list):
        return [map_strings(v, fn) for v in value]
    return value


def leaf_var(pous, entry, path_text):
    segs = [re.sub(r'\[.*?\]', '', s) for s in path_text.split('.')[1:]]
    pou, var = entry, None
    for i, s in enumerate(segs):
        var = pou.vars.get(s.lower())
        if var is None:
            return None
        if i < len(segs) - 1:
            pou = child_block(pous, var)
            if pou is None:
                return None
    return var


def resolve_entry(pous, refs, forced_entry, notes, hint=None):
    def try_block(pou):
        mapping = {}
        for r in refs:
            if r.lower() in pou.vars:
                mapping[r.lower()] = []
                continue
            paths = find_paths(pous, pou, r)
            if not paths:
                return None
            if len(paths) > 1:
                notes.append(f"'{r}' is reachable via several instances "
                             f"({', '.join('.'.join(p) for p in paths)}); using {'.'.join(paths[0])}")
            mapping[r.lower()] = paths[0]
        return mapping

    if forced_entry:
        pou = pous.get(forced_entry.lower())
        if pou is None:
            raise ValueError(f"Entry block '{forced_entry}' not found in source "
                             f"(available: {', '.join(p.name for p in pous.values())})")
        mapping = try_block(pou)
        if mapping is None:
            missing = [r for r in refs if not find_paths(pous, pou, r)]
            raise ValueError(f"Variables {missing} are not reachable from entry '{pou.name}'")
        return pou, mapping

    if hint:
        pou = pous.get(str(hint).lower())
        mapping = try_block(pou) if pou else None
        if mapping is not None:
            return pou, mapping
        missing = [r for r in refs if not (pou and find_paths(pous, pou, r))]
        notes.append(f"dataset entry_point '{hint}' cannot see {missing}; choosing entry automatically")

    ordered = sorted(pous.values(), key=lambda p: p.order)
    fbs = [p for p in ordered if p.kind in ('FUNCTION_BLOCK', 'PROGRAM')] or ordered
    for pou in fbs:
        if all(r.lower() in pou.vars for r in refs):
            return pou, {r.lower(): [] for r in refs}
    for pou in top_level_blocks(pous) + fbs:
        mapping = try_block(pou)
        if mapping is not None:
            return pou, mapping
    unresolved = [r for r in refs if not any(r.lower() in p.vars for p in pous.values())]
    raise ValueError("No entry block can see all referenced variables "
                     f"{sorted(refs)}; not declared anywhere: {unresolved or 'none (no common entry)'}")


def rewrite_expression(expr, pous, entry, mapping, notes):
    def repl(m):
        prefix = mapping.get(m.group(1).lower())
        return 'instance.' + '.'.join(prefix + [m.group(1)]) if prefix else m.group(0)

    new = REF_RE.sub(repl, expr)

    def bool_fix(m):
        var = leaf_var(pous, entry, m.group(1))
        if var and var.base_type.lower() == 'bool':
            lit = 'TRUE' if m.group(3) == '1' else 'FALSE'
            notes.append(f"{m.group(1)} is Bool: '{m.group(3)}' rewritten to {lit}")
            return m.group(1) + m.group(2) + lit
        return m.group(0)

    new = PATH_CMP_RE.sub(bool_fix, new)
    if new != expr:
        notes.append(f"expression rewritten for entry '{entry.name}'")
    if DYN_INDEX_IN_REQ_RE.search(new):
        notes.append('requirement indexes an array with a variable; the NuSMV backend '
                     'may reject this (rewrite it with constant indices)')
    return new


# ============================================================
# VC3 GENERATION
# ============================================================

def escape_vc3(value):
    return (str(value).replace('\\', '\\\\').replace('"', '\\"')
            .replace('\n', ' ').replace('\r', ' '))


def fmt_value(value, force_quote=False):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)) and not force_quote:
        return str(value)
    s = str(value)
    if not force_quote and re.fullmatch(r'[A-Za-z0-9_.\-]+', s):
        return s
    return f'"{escape_vc3(s)}"'


def num_key(k):
    try:
        return (0, int(k))
    except (TypeError, ValueError):
        return (1, str(k))


def flatten(prefix, value, lines):
    quote = 'pattern_params' in prefix
    if isinstance(value, dict):
        for k in sorted(value, key=num_key):
            flatten(f'{prefix}.{k}', value[k], lines)
    elif isinstance(value, list):
        start = 1 if prefix.endswith('pattern_params') else 0
        for i, v in enumerate(value, start=start):
            flatten(f'{prefix}.{i}', v, lines)
    elif value is not None:
        lines.append(f'-{prefix} = {fmt_value(value, force_quote=quote)}')


def build_vc3(cfg, dataset_id, index, description, job_req, req_settings,
              entry_name, source_file, extra_settings, algorithm):
    safe_id = re.sub(r'[^A-Za-z0-9_]+', '_', dataset_id)
    lines = [
        f'-description = "{escape_vc3(description)}"',
        f'-id = verify_{safe_id}_property_{index}',
        '-job = verif',
        f'-job.backend = {cfg.backend}',
    ]
    if cfg.backend == 'nusmv':
        lines += [f'-job.backend.algorithm = {algorithm}',
                  f'-job.backend.binary_path = "{escape_vc3(cfg.solver)}"']
    lines += [f'-job.backend.timeout = {cfg.timeout}', f'-job.req = {job_req}']
    for key in sorted(req_settings, key=num_key):
        flatten(f'job.req.{key}', req_settings[key], lines)
    lines += [
        '-job.reporters.0 = plaintext',
        f'-lf = {cfg.frontend}',
        f'-lf.compiler = {cfg.compiler}',
        f'-lf.entry = {fmt_value(entry_name)}',
        f'-sourcefiles.0 = "{escape_vc3(source_file)}"',
    ]
    for key, value in extra_settings.items():
        lines.append(f'-{key.lstrip("-")} = {fmt_value(value)}')
    return '\n'.join(lines) + '\n'


# ============================================================
# RUN + CLASSIFY
# ============================================================

VERDICT_RES = [
    re.compile(r'requirement\s+(?:is\s+)?(not\s+satisfied|satisfied|violated|unknown|error)', re.I),
    re.compile(r'\bresult\s*[:=]\s*\**\s*(not\s+satisfied|satisfied|violated|unknown|error)', re.I),
]
ERROR_MARKERS = [
    re.compile(r'^\s*ERROR\b', re.M),
    re.compile(r'\b\w+Exception\b'),
    re.compile(r'error happened', re.I),
]
KNOWN_HINTS = [
    ('enumerate arrays', 'variable array index the rewriter could not handle; see WARNING lines '
                         'or try --backend theta'),
    ('is not supported in Step7v55', 'TIA-only type; check WARNING lines for unmapped types'),
    ('not in the set of acceptable values', 'invalid setting value; acceptable values listed above'),
]


def error_reason(output):
    stage_errors = list(dict.fromkeys(
        re.sub(r'\s+', ' ', m.group(1)).strip()
        for m in re.finditer(r'^Error:\s*(.+?)\s*(?:\[[^\]]*\])?\s*$', output, re.M)
    ))
    if stage_errors:
        more = len(stage_errors) - 1
        reason = stage_errors[0][:300] + (f' (+{more} more distinct errors)' if more else '')
    else:
        reason = None
        for pat in (r'PLCverif error\.\s*(.+)', r'Caused by:\s*[\w.$]+:\s*(.+)',
                    r'^\s*ERROR\s+\S+\s+(.+)$'):
            m = re.search(pat, output, re.M)
            if m:
                reason = m.group(1).strip()[:400]
                break
    for needle, hint in KNOWN_HINTS:
        if reason and needle.lower() in reason.lower():
            reason += f'  [hint: {hint}]'
            break
    return reason


def classify(output, algorithm):
    verdict = None
    for rx in VERDICT_RES:
        m = rx.search(output)
        if m:
            verdict = re.sub(r'\s+', ' ', m.group(1).lower())
            break
    if verdict == 'satisfied':
        return ('SATISFIED_BOUNDED' if algorithm == 'Bmc' else 'SATISFIED'), None
    if verdict in ('violated', 'not satisfied'):
        return 'VIOLATED', None
    if verdict == 'unknown':
        return 'UNKNOWN', error_reason(output) or 'backend returned unknown (timeout or incomplete)'
    if verdict == 'error' or any(rx.search(output) for rx in ERROR_MARKERS):
        reason = error_reason(output)
        acc = re.search(r'Acceptable values:\s*([^.)\n]+)', output)
        if acc and reason and 'Acceptable' not in reason:
            reason += f' [acceptable: {acc.group(1).strip()}]'
        return 'ERROR', reason
    return 'UNKNOWN', 'no verdict found in PLCverif output'


def run_plcverif(cfg, vc3_file, algorithm):
    cmd = [str(cfg.plcverif), str(vc3_file), '-data', '.', '-consoleLog']
    print('\n$ ' + ' '.join(cmd))
    try:
        proc = subprocess.run(cmd, cwd=SCRIPT_DIR, text=True, capture_output=True,
                              timeout=cfg.timeout + 120)
    except FileNotFoundError:
        return 'ERROR', f'PLCverif not found: {cfg.plcverif}', -1
    except subprocess.TimeoutExpired:
        return 'TIMEOUT', f'PLCverif did not finish within {cfg.timeout + 120}s', -1
    output = (proc.stdout or '') + ('\n' + proc.stderr if proc.stderr else '')
    status, reason = classify(output, algorithm)
    if not cfg.quiet:
        print(output)
    elif status not in ('SATISFIED', 'SATISFIED_BOUNDED'):
        print('\n'.join(l for l in output.splitlines()
                        if re.match(r'\s*(Error|Warning|ERROR|\*\*Result)', l))[-3000:])
    return status, reason, proc.returncode


# ============================================================
# DISCOVERY
# ============================================================

def find_solver(explicit):
    if explicit:
        p = Path(explicit).expanduser().resolve()
        return p if p.is_file() else None
    for env in ('NUXMV_PATH', 'NUSMV_PATH'):
        if os.environ.get(env) and Path(os.environ[env]).is_file():
            return Path(os.environ[env]).resolve()
    base = SCRIPT_DIR.parent
    for pat in ('nuXmv*/usr/local/bin/nuXmv', 'nuXmv/usr/local/bin/nuXmv',
                'tools/nuxmv/*/usr/local/bin/nuXmv', 'tools/*/usr/local/bin/nuXmv',
                'tools/**/bin/nuXmv', 'tools/**/bin/NuSMV'):
        for c in sorted(base.glob(pat)):
            if c.is_file():
                return c.resolve()
    for exe in ('nuXmv', 'NuSMV'):
        w = shutil.which(exe)
        if w:
            return Path(w).resolve()
    return None


def find_source(json_file, data, explicit):
    if explicit:
        p = Path(explicit).resolve()
        if not p.is_file():
            raise SetupError(f'source not found: {p}')
        return p
    for key in ('source_file', 'scl_file', 'st_file', 'file'):
        if isinstance(data.get(key), str):
            p = (json_file.parent / data[key]).resolve()
            if p.is_file():
                return p
    d, stem = json_file.parent, json_file.stem
    for ext in ('.scl', '.st', '.SCL', '.ST'):
        if (d / f'{stem}{ext}').exists():
            return d / f'{stem}{ext}'
    files = sorted(set(d.glob('*.scl')) | set(d.glob('*.st')))
    if len(files) == 1:
        return files[0]
    if not files:
        raise SetupError(f'no .scl/.st source next to {json_file.name}')
    raise SetupError(f'no source named {stem}.scl/.st and several others in the folder; '
                     f'add "source_file" to the JSON or pass --source')


def collect_inputs(paths, recursive):
    out = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            it = p.rglob('*.json') if recursive else p.glob('*.json')
            out += sorted(f for f in it if not f.name.endswith('_results.json')
                          and f.name != 'batch_summary.json')
        else:
            out.append(p)
    seen, unique = set(), []
    for f in out:
        r = f.resolve()
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique


# ============================================================
# ONE DATASET
# ============================================================

def run_dataset(json_file, cfg):
    bar = '=' * 75
    if not json_file.is_file() or json_file.suffix.lower() != '.json':
        raise SetupError(f'not a JSON file: {json_file}')
    try:
        data = json.loads(json_file.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        raise SetupError(f'invalid JSON: {e}')
    if not isinstance(data, dict):
        raise SetupError('JSON top level must be an object')

    source_file = find_source(json_file, data, cfg.source)
    raw = source_file.read_bytes().decode('utf-8', errors='surrogateescape')
    pous = parse_source_text(raw)
    if not pous:
        raise SetupError(f'no FUNCTION_BLOCK / PROGRAM / FUNCTION in {source_file.name}')

    properties = data.get('properties_to_be_validated', [])
    if not properties:
        raise SetupError("JSON contains no 'properties_to_be_validated'")

    global_extra = dict(data.get('extra_settings', {}))
    for item in cfg.set:
        k, v = item.split('=', 1)
        global_extra[k.strip()] = v.strip()
    global_entry = cfg.entry or data.get('entry')
    dataset_id = str(data.get('id', json_file.stem))

    out_dir = json_file.parent / f'{json_file.stem}_vc3'
    out_dir.mkdir(exist_ok=True)
    verif_source, prep_notes, prep_warnings = prepare_source(source_file, out_dir, cfg, pous)
    verif_text = verif_source.read_bytes().decode('utf-8', errors='surrogateescape')

    print(bar)
    print('PLCVERIF JSON RUNNER')
    print(bar)
    print(f'JSON file     : {json_file}')
    print(f'Source file   : {source_file}')
    print('Blocks        : ' + ', '.join(
        f'{p.name} ({p.kind}{", asserts" if p.has_assertions else ""})'
        for p in sorted(pous.values(), key=lambda p: p.order)))
    print(f'Dataset ID    : {dataset_id}')
    print(f'Properties    : {len(properties)}')
    print(f'Backend       : {cfg.backend}' +
          (f' / {cfg.algorithm}' if cfg.backend == 'nusmv' else '') +
          (f' (fallback on UNKNOWN: {", ".join(cfg.fallback)})' if cfg.fallback else '') +
          ('  (bounded: "satisfied" is NOT a proof)' if cfg.algorithm == 'Bmc' else ''))
    print(f'Frontend      : {cfg.frontend} / {cfg.compiler}')
    if verif_source != source_file:
        print(f'Verified copy : {verif_source}  (original untouched)')
    for n in prep_notes:
        print(f'  prepared: {n}')
    for w in prep_warnings:
        print(f'  WARNING : {w}')
    print(bar)

    results = []
    for index, item in enumerate(properties, start=1):
        if cfg.property and index not in cfg.property:
            continue
        print(f'\n{bar}\nPROPERTY {index}\n{bar}')
        description = item.get('property_description', f'Property {index}')
        print(description)
        prop = dict(item.get('property', {}))
        job_req = prop.pop('job_req', None)
        forced = prop.pop('entry', None) or item.get('entry') or global_entry
        entry_hint = prop.pop('entry_point', None) or item.get('entry_point')
        for meta in META_KEYS:
            prop.pop(meta, None)
        extra = {**global_extra, **item.get('extra_settings', {})}
        notes = []
        record = {'property': index, 'job_req': job_req, 'description': description}

        if not job_req:
            record.update(status='PROPERTY_ERROR', reason='missing job_req')
            results.append(record)
            print('STATUS: PROPERTY_ERROR (missing job_req)')
            continue

        try:
            if job_req == 'assertion':
                if forced:
                    entry = pous.get(forced.lower())
                    if entry is None:
                        raise ValueError(f"Entry block '{forced}' not found")
                elif entry_hint and str(entry_hint).lower() in pous and \
                        subtree_has_assertions(pous, pous[str(entry_hint).lower()]):
                    entry = pous[str(entry_hint).lower()]
                    seen = reachable_blocks(pous, entry)
                    skipped = [p.name for p in pous.values()
                               if p.has_assertions and p.name.lower() not in seen]
                    if skipped:
                        notes.append(f"dataset entry_point '{entry.name}' does not include the "
                                     f"assertions in {skipped}; use --entry to check them too")
                else:
                    cands = [p for p in top_level_blocks(pous) if subtree_has_assertions(pous, p)]
                    if not cands:
                        record.update(status='SKIPPED_NO_ASSERTIONS',
                                      reason='source contains no //#ASSERT annotations')
                        results.append(record)
                        print('STATUS: SKIPPED_NO_ASSERTIONS')
                        continue
                    entry = cands[0]
                req_settings = prop
            else:
                refs = sorted({m.group(1) for s in collect_strings(prop)
                               for m in REF_RE.finditer(s)}, key=str.lower)
                if refs:
                    entry, mapping = resolve_entry(pous, refs, forced, notes, entry_hint)
                else:
                    entry = pous[forced.lower()] if forced and forced.lower() in pous \
                        else sorted(pous.values(), key=lambda p: p.order)[0]
                    mapping = {}
                    notes.append("no 'instance.' references found in the requirement")
                req_settings = map_strings(
                    prop, lambda s: rewrite_expression(s, pous, entry, mapping, notes))
        except ValueError as e:
            record.update(status='PROPERTY_ERROR', reason=str(e))
            results.append(record)
            print(f'STATUS: PROPERTY_ERROR\nReason: {e}')
            continue

        for n in dict.fromkeys(notes):
            print(f'NOTE: {n}')

        if not any(v.section in ('VAR_INPUT', 'VAR_IN_OUT')
                   for v in parse_source_text(verif_text)[entry.name.lower()].vars.values()):
            notes.append(f"entry '{entry.name}' has no inputs in the verified copy: the model is "
                         f"deterministic, so a SATISFIED result covers only one execution")
            for n in notes[-1:]:
                print(f'NOTE: {n}')

        record.update(entry=entry.name, notes=list(dict.fromkeys(notes)), attempts=[])
        algorithms = [cfg.algorithm] + (cfg.fallback if cfg.backend == 'nusmv' else [])
        for attempt, alg in enumerate(algorithms):
            suffix = '' if attempt == 0 else f'_{alg.lower()}'
            vc3 = build_vc3(cfg, dataset_id, index, description, job_req, req_settings,
                            entry.name, verif_source, extra, alg)
            vc3_file = out_dir / f'{json_file.stem}_property_{index}{suffix}.vc3'
            vc3_file.write_text(vc3, encoding='utf-8')
            print(f'\nEntry block: {entry.name}   Algorithm: {alg}\nVC3: {vc3_file}')
            if not cfg.quiet:
                print(f'--- VC3 ---\n{vc3}--- END ---')
            record['vc3'] = str(vc3_file)
            if cfg.dry_run:
                record['status'] = 'GENERATED'
                break
            status, reason, rc = run_plcverif(cfg, vc3_file, alg)
            record['attempts'].append({'algorithm': alg, 'status': status})
            record.update(status=status, reason=reason, return_code=rc, algorithm=alg)
            print(f'\nRESULT ({alg}): {status}' + (f'\nReason: {reason}' if reason else ''))
            if status not in ('UNKNOWN', 'TIMEOUT') or attempt == len(algorithms) - 1:
                break
            print(f'Retrying with {algorithms[attempt + 1]} ...')
        results.append(record)

    print(f'\n{bar}\nSUMMARY  {json_file.name}\n{bar}')
    for r in results:
        line = f"Property {r['property']:>2} : {r['status']:<22}"
        if r.get('entry'):
            line += f" entry={r['entry']}"
        print(line)
        if r.get('reason') and r['status'] != 'SATISFIED':
            print(f"              {r['reason']}")

    overall = overall_status([r['status'] for r in results], cfg.dry_run)
    print(f'\nOVERALL: {overall}\n{bar}')
    results_file = json_file.parent / f'{json_file.stem}_results.json'
    results_file.write_text(json.dumps({
        'dataset_id': dataset_id, 'source': str(source_file),
        'verified_source': str(verif_source),
        'source_preparation': prep_notes, 'source_warnings': prep_warnings,
        'backend': cfg.backend, 'algorithm': cfg.algorithm,
        'overall': overall, 'properties': results,
    }, indent=2), encoding='utf-8')
    print(f'Results written to {results_file}')
    return {'dataset': json_file.name, 'id': dataset_id, 'source': source_file.name,
            'overall': overall, 'results': results, 'prepared': bool(prep_notes)}


def overall_status(statuses, dry_run):
    if any(s in ('ERROR', 'PROPERTY_ERROR', 'TIMEOUT', 'SETUP_ERROR') for s in statuses):
        return 'ERROR'
    if 'UNKNOWN' in statuses:
        return 'UNKNOWN'
    if 'VIOLATED' in statuses:
        return 'VIOLATED'
    if dry_run:
        return 'GENERATED'
    if 'SATISFIED_BOUNDED' in statuses:
        return 'SATISFIED_BOUNDED'
    return 'SATISFIED' if statuses else 'EMPTY'


# ============================================================
# MAIN
# ============================================================

def parse_args():
    ap = argparse.ArgumentParser(
        description='Run PLCverif on the properties of one or many JSON datasets.')
    ap.add_argument('inputs', nargs='+', help='JSON files and/or folders containing them')
    ap.add_argument('--recursive', action='store_true', help='search folders recursively')
    ap.add_argument('--backend', default='nusmv',
                    help='PLCverif backend (default nusmv; e.g. theta handles variable '
                         'array indices natively if installed)')
    ap.add_argument('--algorithm', default='auto', choices=('auto',) + NUSMV_ALGORITHMS)
    ap.add_argument('--timeout', type=int, default=60, help='backend timeout in seconds')
    ap.add_argument('--fallback', action='append', default=None, metavar='ALG',
                    help='algorithm(s) to retry with when a run ends UNKNOWN '
                         '(default: Classic after Ic3, Ic3 after Classic; "none" disables)')
    ap.add_argument('--no-free-inputs', action='store_true',
                    help='keep never-written statics of input-less top-level blocks as VAR')
    ap.add_argument('--frontend', default='step7')
    ap.add_argument('--compiler', default='Step7v55')
    ap.add_argument('--entry', help='force the entry block for every property')
    ap.add_argument('--source', help='source file (single dataset only)')
    ap.add_argument('--plcverif', default=str(DEFAULT_PLCVERIF))
    ap.add_argument('--solver', help='path to nuXmv / NuSMV binary')
    ap.add_argument('--set', action='append', default=[], metavar='KEY=VALUE',
                    help='extra VC3 setting, e.g. --set job.backend.bmc_bound=20')
    ap.add_argument('--property', action='append', type=int, default=[],
                    help='run only this property number (repeatable)')
    ap.add_argument('--no-normalize', action='store_true',
                    help='do not widen TIA-only types for Step7v55')
    ap.add_argument('--no-array-rewrite', action='store_true',
                    help='do not rewrite variable array indices')
    ap.add_argument('--summary', help='batch summary CSV path (default: batch_summary.csv '
                                      'next to the first input)')
    ap.add_argument('--dry-run', action='store_true', help='generate files only, do not run')
    ap.add_argument('--quiet', action='store_true', help='short PLCverif output')
    ap.add_argument('--verbose', action='store_true', help='full output even in batch mode')
    return ap.parse_args()


def main():
    cfg = parse_args()
    for item in cfg.set:
        if '=' not in item:
            sys.exit(f'ERROR: --set expects KEY=VALUE, got {item!r}')

    inputs = collect_inputs(cfg.inputs, cfg.recursive)
    if not inputs:
        sys.exit('ERROR: no JSON datasets found')
    batch = len(inputs) > 1
    if batch and cfg.source:
        sys.exit('ERROR: --source only works with a single dataset')
    if batch and not cfg.verbose:
        cfg.quiet = True

    cfg.plcverif = Path(cfg.plcverif).resolve()
    if not cfg.dry_run and not cfg.plcverif.is_file():
        sys.exit(f'ERROR: PLCverif executable not found: {cfg.plcverif}')
    cfg.algorithm = cfg.algorithm if cfg.backend == 'nusmv' else 'n/a'
    if cfg.backend == 'nusmv':
        solver = find_solver(cfg.solver)
        if solver is None and not cfg.dry_run:
            sys.exit('ERROR: nuXmv/NuSMV not found; pass --solver or set NUXMV_PATH')
        cfg.solver = str(solver) if solver else 'nuXmv'
        is_nuxmv = 'nuxmv' in Path(cfg.solver).name.lower()
        if cfg.algorithm == 'auto':
            cfg.algorithm = 'Ic3' if is_nuxmv else 'Classic'
        elif cfg.algorithm == 'Ic3' and not is_nuxmv:
            print('WARNING: Ic3 needs nuXmv; the configured binary looks like NuSMV.')
        if cfg.fallback is None:
            cfg.fallback = ['Classic'] if cfg.algorithm != 'Classic' else (['Ic3'] if is_nuxmv else [])
        elif [a.lower() for a in cfg.fallback] == ['none']:
            cfg.fallback = []
        else:
            canon = {a.lower(): a for a in NUSMV_ALGORITHMS}
            bad = [a for a in cfg.fallback if a.lower() not in canon]
            if bad:
                sys.exit(f'ERROR: unknown fallback algorithm(s) {bad}; use {NUSMV_ALGORITHMS}')
            cfg.fallback = [canon[a.lower()] for a in cfg.fallback if canon[a.lower()] != cfg.algorithm]
    else:
        cfg.fallback = []

    summaries = []
    for json_file in inputs:
        try:
            summaries.append(run_dataset(json_file, cfg))
        except SetupError as e:
            print(f'\nSETUP ERROR in {json_file.name}: {e}')
            summaries.append({'dataset': json_file.name, 'id': '', 'source': '',
                              'overall': 'SETUP_ERROR', 'results': [], 'error': str(e)})
        except Exception as e:                       # keep a batch going
            print(f'\nINTERNAL ERROR in {json_file.name}: {type(e).__name__}: {e}')
            summaries.append({'dataset': json_file.name, 'id': '', 'source': '',
                              'overall': 'SETUP_ERROR', 'results': [],
                              'error': f'{type(e).__name__}: {e}'})

    if batch:
        bar = '=' * 75
        print(f'\n{bar}\nBATCH SUMMARY ({len(summaries)} datasets)\n{bar}')
        counts = {}
        for s in summaries:
            st = [r['status'] for r in s['results']]
            c = {k: st.count(k) for k in dict.fromkeys(st)}
            detail = ', '.join(f'{k}={v}' for k, v in c.items()) or s.get('error', '')
            print(f"{s['dataset']:<40} {s['overall']:<12} {detail}")
            counts[s['overall']] = counts.get(s['overall'], 0) + 1
        print(bar)
        print('  '.join(f'{k}: {v}' for k, v in counts.items()))
        summary_path = Path(cfg.summary) if cfg.summary else inputs[0].parent / 'batch_summary.csv'
        with open(summary_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['dataset', 'dataset_id', 'source', 'overall', 'property',
                        'job_req', 'entry', 'status', 'reason'])
            for s in summaries:
                if not s['results']:
                    w.writerow([s['dataset'], s['id'], s['source'], s['overall'],
                                '', '', '', s['overall'], s.get('error', '')])
                for r in s['results']:
                    w.writerow([s['dataset'], s['id'], s['source'], s['overall'],
                                r['property'], r.get('job_req', ''), r.get('entry', ''),
                                r['status'], r.get('reason') or ''])
        print(f'Batch summary written to {summary_path}')

    overall = [s['overall'] for s in summaries]
    if any(o in ('ERROR', 'SETUP_ERROR', 'UNKNOWN') for o in overall):
        sys.exit(EXIT_ERROR)
    if 'VIOLATED' in overall:
        sys.exit(EXIT_VIOLATED)
    sys.exit(EXIT_OK)


if __name__ == '__main__':
    main()

