from .parser import OPERATIONS, PRECEDENCE, ASSOCIATIVE, parse
from functools import cached_property
from typing import Union
import copy

SIMPLIFICATION_RULES = [
    ("1 & x", "x")
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
            if op in ASSOCIATIVE:
                while True:
                    break_idx = None
                    for idx, c in enumerate(children):
                        if c[0] == op: 
                            break_idx = idx
                            break
                    if break_idx is None:
                        break
                    children = children[:break_idx] \
                             + children[break_idx][1:] \
                             + children[break_idx+1:]
            return Formula(op, *map(rec, children) )
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

    def simplify(self) -> "Formula":
        def try_remove_double_negation(form: Formula) -> Formula:
            if form.op == "~" and form.c1.op == "~": return form.c1.c1
            else: return form

        # removes occurrences of 0s and 1s
        if self.is_variable or self.is_constant:
            return copy.copy(self)
        if self.op == "~":
            sub = self.c1.simplify()
            if sub == Formula.zero: return Formula.one
            elif sub == Formula.one: return Formula.zero
            elif sub.op == "~": return sub.c1 # double negation
            else: return Formula("~", sub)
        
        simp_children = list(c.simplify() for c in self.children)
        if self.op == "&":
            if any(c == Formula.zero for c in simp_children): return Formula.zero
            if all(c == Formula.one for c in simp_children): return Formula.one
            filtered = [c for c in simp_children if c != Formula.one]
            filtered = list(dict.fromkeys(filtered)) # removes duplicates
            if len(filtered) == 1: return filtered[0]
            else: return Formula("&", *filtered)
        elif self.op == "|":
            if any(c == Formula.one for c in simp_children): return Formula.one
            if all(c == Formula.zero for c in simp_children): return Formula.zero
            filtered = [ c for c in simp_children if c != Formula.zero ]
            filtered = list(dict.fromkeys(filtered)) # removes duplicates
            if len(filtered) == 1: return filtered[0] # exactly one is not 0
            else: return Formula("|", *filtered) # more than one are not 0
        elif self.op == "^":
            filtered = [c for c in simp_children if c != Formula.zero and c != Formula.one]
            ones = len([c for c in simp_children if c == Formula.one])
            if ones % 2 == 0: # even number of ones
                if len(filtered) == 0: return Formula.zero
                elif len(filtered) == 1: return filtered[0]
                else: return Formula("^", *filtered)
            else: # odd number of ones
                if len(filtered) == 0: return Formula.one
                elif len(filtered) == 1: return try_remove_double_negation(Formula("~", filtered[0]))
                else: return Formula("~", Formula("^", *filtered))
        
        left, right = simp_children # there must be two at this point
        if self.op == "<->":
            if left == right: return Formula.one
            elif left.is_constant and right.is_constant: return Formula.zero # at this point, they cannot both be constant
            elif left == Formula.one: return right # right cannot be constant
            elif left == Formula.zero: return try_remove_double_negation(Formula("~", right)) # -- 
            elif right == Formula.one: return left  # left cannot be constant
            elif right == Formula.zero: return try_remove_double_negation(Formula("~", left)) # --
            else: return copy.copy(self)
        elif self.op == "->":
            if left == right: return Formula.one
            elif left == Formula.one: return right
            elif left == Formula.zero: return Formula.one 
            elif right == Formula.zero: return try_remove_double_negation(Formula("~", left))
            elif right == Formula.one: return Formula.one 
            else: return copy.copy(self)
        elif self.op == "<-":
            if left == right: return Formula.one
            elif right == Formula.one: return left
            elif right == Formula.zero: return Formula.one 
            elif left == Formula.zero: return try_remove_double_negation(Formula("~", right))
            elif left == Formula.one: return Formula.one 
            else: return copy.copy(self)


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
    
    def rename(self, d: dict):
        if self.op == "V" and self.c1 in d: return Formula("V", d[self.c1])
        elif self.op in ["V", "C"]: return copy.copy(self)
        else: return Formula(self.op, *(c.rename(d) for c in self.children))

    def __copy__(self) -> "Formula":
        return Formula(self.op, *(copy.copy(c) for c in self.children))

    def __hash__(self) -> int:
        return self.__repr__().__hash__()

    def tseitin(self) -> tuple[list[set], dict[str, int]]:
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

Formula.one = Formula.parse("1")
Formula.zero = Formula.parse("0")

if __name__ == "__main__":
    f = Formula.parse("((x <-> y) | z) & (x <-> y)") & Formula.parse("y")
    print(f)
    print(f.cofactor("y", False).simplify())
    print(f.flip("x").cofactor("y", False).simplify())
    print(f.tseitin())