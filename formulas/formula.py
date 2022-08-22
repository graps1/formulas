from dataclasses import replace
from .parser import OPERATIONS, PRECEDENCE, ASSOCIATIVE, parse
from functools import cached_property
from typing import Union
import copy

SIMP_RULES = [
    ("~0", "1"),
    ("~1", "0"),
    ("~~A", "A"),

    ("~A & A", "0"),
    ("A & ~A", "0"),
    ("A & A", "A"),
    ("1 & A", "A"),
    ("A & 1", "A"),
    ("0 & A", "0"),
    ("A & 0", "0"),

    ("A | ~A", "1"),
    ("~A | A", "1"),
    ("A | A", "A"),
    ("0 | A", "A"),
    ("A | 0", "A"),
    ("1 | A", "1"),
    ("A | 1", "1"),

    ("A ^ A", "0"),
    ("A ^ ~A", "1"),
    ("~A ^ A", "1"),
    ("0 ^ A", "A"),
    ("A ^ 0", "A"),
    ("1 ^ A", "~A"),
    ("A ^ 1", "~A"),

    ("A -> ~A", "~A"),
    ("~A -> A", "A"),
    ("A -> A", "1"),
    ("0 -> A", "1"),
    ("A -> 0", "~A"),
    ("1 -> A", "A"),
    ("A -> 1", "1"),

    ("A <- ~A", "A"),
    ("~A <- A", "~A"),
    ("A <- A", "1"),
    ("0 <- A", "~A"),
    ("A <- 0", "1"),
    ("1 <- A", "1"),
    ("A <- 1", "A"),

    ("A <-> A", "1"),
    ("A <-> ~A", "0"),
    ("~A <-> A", "0"),
    ("0 <-> A", "~A"),
    ("A <-> 0", "~A"),
    ("1 <-> A", "A"),
    ("A <-> 1", "A"),
]

class Formula:
    def __init__(self, op=None, *children):

        assert op in ["C","V"] or op in OPERATIONS

        if op in ["C", "V"]: assert len(children)==1 and isinstance(children[0], str)
        else: assert all(isinstance(c,Formula) for c in children)

        if op == "~": assert len(children)==1
        elif op in ["->", "<-", "<->"]: assert len(children) == 2
        elif op in ["|", "&", "^"]: assert len(children) >= 2

        self.__op = op 
        self.__children = tuple(children)
        self.__c1 = children[0]
        self.__str_repr = None

    def __eq__(self, other) -> bool: 
        return  isinstance(other, Formula) and \
                self.op == other.op and \
                all(c1 == c2 for c1,c2 in zip(self.children, other.children))

    def __len__(self) -> int:
        if self.op in ["V", "C"]: return 1
        elif len(self.children) == 1:
            return 1 + len(self.c1)
        else:
            return (len(self.children) - 1) + sum(map(len, self.children))

    def treestr(self, indent=0) -> str:
        ind = "  "*indent
        if self.op in ["C", "V"]: return ind + self.c1
        else: return ind + self.op + "\n" +\
                     "\n".join(c.treestr(indent+1) for c in self.children)

    @property
    def is_constant(self) -> bool: return self.op == "C"

    @property
    def is_variable(self) -> bool: return self.op == "V"

    @property
    def op(self) -> str: return self.__op

    @property
    def c1(self) -> Union["Formula", str]: return self.__c1

    @property 
    def children(self) -> list[Union["Formula", str]]: return self.__children

    @classmethod
    def parse(self, formula: str) -> "Formula":
        def rec(tree):
            op, children = tree[0], tree[1:]
            if op in ["C", "V"]: return Formula(op, *children)
            else: return Formula(op, *map(rec, children) )
        return rec(parse(formula))

    def __repr__(self):
        if self.__str_repr is not None:
            return self.__str_repr

        if self.is_variable or self.is_constant: 
            self.__str_repr = self.c1
        elif self.op == "~": 
            if self.c1.is_variable or self.c1.is_constant: 
                self.__str_repr = "~" + str(self.c1)
            else: self.__str_repr = "~(" + str(self.c1) + ")"
        else:
            child_strings = []
            for c in self.children: 
                if PRECEDENCE[c.op] >= PRECEDENCE[self.op]:
                    child_strings.append( "(" + str(c) + ")" )
                else:
                    child_strings.append(str(c))
            self.__str_repr = f"{self.op}".join(child_strings)
        return str(self)

    def is_applicable(self, template: "Formula") -> dict[str, "Formula"]:
        def rec(formula: "Formula", temp: "Formula", replacement: dict):
            if temp.op == "V": 
                if temp.c1 not in replacement:
                    replacement[temp.c1] = formula 
                return replacement[temp.c1] == formula
            elif temp.op == "C":
                return temp.c1 == formula.c1
            else:
                return temp.op == formula.op and \
                       len(formula.children) == len(temp.children) and \
                       all( rec(f, t, replacement) for f,t in zip(formula.children, temp.children) )
        replacement = {}
        result = rec(self, template, replacement)
        if result: return replacement 
        else: return None

    def simplify(self) -> "Formula":
        if self.op in ["C", "V"]: 
            return self
        else:
            self_simplified = Formula(self.op, *(c.simplify() for c in self.children))
            while True:
                rule_applicable = False
                for rule, result in SIMP_RULES:
                    if (replacement := self_simplified.is_applicable(rule)) is not None:
                        self_simplified = result.replace(replacement)                    
                        rule_applicable = True 
                        break
                if not rule_applicable: break
            return self_simplified 

    def cofactor(self, var : str, val : bool) -> "Formula":
        if self.op == "V" and self.c1 == var: return Formula.one if val else Formula.zero
        elif self.op in ["V", "C"]: return copy.copy(self)
        else: return Formula(self.op, *(c.cofactor(var, val) for c in self.children))
         
    def __and__(self, other : "Formula") -> "Formula": return Formula("&", self, other)
    def __or__(self, other : "Formula") -> "Formula": return Formula("|", self, other)
    def __xor__(self, other : "Formula") -> "Formula": return Formula("^", self, other)
    def __invert__(self) -> "Formula": return Formula("~", self)
    def __rshift__(self, other) -> "Formula": return Formula("->", self, other) 
    def __lshift__(self, other) -> "Formula": return Formula("<-", self, other) 
    def biimp(self, other) -> "Formula": return Formula("<->", self, other)
    def ite(self, o1, o2) -> "Formula": return (self & o1) | (~self & o2)

    @cached_property
    def vars(self) -> set[str]:
        if self.op == "V": return { self.c1 }
        elif self.op == "C": return set()
        else: 
            ret = set()
            for c in self.children: ret |= c.vars
            return ret

    def flip(self, var : str) -> "Formula":
        if self.op == "V" and self.c1 == var: return Formula("~", self)
        elif self.op in ["V", "C"]: return copy.copy(self)
        else: return Formula(self.op, *(c.flip(var) for c in self.children))
    
    def replace(self, d: dict[str, Union["Formula", str]]):
        if self.op == "V" and self.c1 in d: 
            repl = d[self.c1]
            if isinstance(repl, str): 
                repl = Formula.parse(repl)
            return copy.copy(repl)
        elif self.op in ["V", "C"]: return copy.copy(self)
        else: return Formula(self.op, *(c.replace(d) for c in self.children))

    def __copy__(self) -> "Formula":
        return Formula(self.op, *(copy.copy(c) for c in self.children))

    def __hash__(self) -> int:
        return self.__repr__().__hash__()

    def tseitin(self) -> tuple[list[set], dict["Formula", int]]:
        formula = self.simplify()
        if formula == Formula.zero or formula == Formula.one: 
            return [], {}

        stack = [formula]
        sub2idx = set()
        subs = set()
        while len(stack) > 0:
            top = stack.pop()
            if top.op == "C": raise Exception(f"formula cannot contain 0s or 1s")
            # add sub-formula
            sub2idx.add(top)
            if top.op != "V": # recurse if top is not a variable
                children = top.children
                if len(top.children) > 2:
                    children = (top.children[0], Formula(top.op, *top.children[1:]) )
                subs.add((top, children))
                stack += list(children)
        sub2idx = {k: v for v,k in enumerate(sub2idx, start=1)}

        # src: https://en.wikipedia.org/wiki/Tseytin_transformation
        cnf = [ { sub2idx[formula] } ]
        for sub, children in subs:
            C = sub2idx[sub]
            A = sub2idx[children[0]] # 1 or 2-ary operation
            if sub.op == "~": # negation
                cnf += [{-C, -A}, {C, A}]
            else: # 2-ary operation
                B = sub2idx[children[1]]
                if sub.op == "<->":
                    cnf += [{-A, -B, C}, {A, B, C}, {A, -B, -C}, {-A, B, -C}]
                elif sub.op == "<-":
                    cnf += [{A, -B, -C}, {-A, C}, {B, C}]
                elif sub.op == "->":
                    cnf += [{-A, B, -C}, {A, C}, {-B, C}]
                elif sub.op == "^":
                    cnf += [{-C, -A, -B}, {-C, A, B}, {C, -A, B}, {C, A, -B}]
                elif sub.op == "&":
                    cnf += [{-A, -B, C}, {A, -C}, {B, -C}]
                elif sub.op == "|":
                    cnf += [{A, B, -C}, {-A, C}, {-B, C}]
                else:
                    raise Exception(f"operation {sub.op} unknown!")
        return cnf, sub2idx


SIMP_RULES = [ (Formula.parse(left), Formula.parse(right)) for left,right in SIMP_RULES ]
Formula.one = Formula.parse("1")
Formula.zero = Formula.parse("0")