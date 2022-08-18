from .parser import OPERATIONS, PRECEDENCE, ASSOCIATIVE, parse
from functools import cached_property
from typing import Union

class Formula:
    def __init__(self, op=None, c1=None, c2=None):
        assert op in ["C","V"] or op in OPERATIONS
        if op in ["C", "V"]: assert c2 is None and isinstance(c1, str)
        elif op == "~": assert c2 is None and isinstance(c1, Formula) 
        else: assert isinstance(c1, Formula) and isinstance(c2, Formula)
        self.__op = op 
        self.__children = [c for c in [c1,c2] if c is not None]
        self.__c1 = c1
        self.__c2 = c2
        self.__str_repr = None

    def __eq__(self, other) -> bool: 
        return  isinstance(other, Formula) and \
                self.op == other.op and \
                self.c1 == other.c1 and self.c2 == other.c2

    @property
    def is_constant(self) -> bool: return self.__op == "C"

    @property
    def is_variable(self) -> bool: return self.__op == "V"

    @property
    def op(self) -> str: return str(self.__op)

    @property
    def c1(self) -> Union["Formula", str]: return self.__c1

    @property
    def c2(self) -> Union["Formula", str]: return self.__c2

    @property 
    def children(self) -> list[Union["Formula", str]]: return self.__children

    @classmethod
    def parse(self, formula: str) -> "Formula":
        def rec(tree):
            op = tree[0]
            if op in ["C", "V"]: return Formula(op, *tree[1:])
            else: return Formula(op, *( rec(c) for c in tree[1:] ) )
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
            left = str(self.c1)
            if  not(self.c1.op in ASSOCIATIVE and self.c1.op == self.op \
                    or PRECEDENCE[self.c1.op] < PRECEDENCE[self.op]):
                left = "(" + left + ")"

            right = str(self.c2)
            if  not(self.c2.op in ASSOCIATIVE and self.c2.op == self.op \
                    or PRECEDENCE[self.c2.op] < PRECEDENCE[self.op]): 
                right = "(" + right + ")"

            self.__str_repr = f"{left} {self.op} {right}"
        return str(self)

    def simplify(self) -> "Formula":
        # removes occurrences of 0s and 1s
        if self.is_variable or self.is_constant:
            return self 
        if self.op == "~":
            sub = self.c1.simplify()
            if sub == Formula.zero: return Formula.one
            elif sub == Formula.one: return Formula.zero
            elif sub.op == "~": return sub.c1 # double negation
            else: return Formula("~", sub)
        left, right = self.c1.simplify(), self.c2.simplify()
        if self.op == "&":
            if left == Formula.one: return right
            if left == Formula.zero: return Formula.zero
            if right == Formula.one: return left
            if right == Formula.zero: return Formula.zero
        elif self.op == "|":
            if left == Formula.zero: return right
            if left == Formula.one: return Formula.one 
            if right == Formula.zero: return left
            if right == Formula.one: return Formula.one 
        elif self.op == "^":
            if left == Formula.one: return Formula("~", right).simplify()
            if left == Formula.zero: return right 
            if right == Formula.one: return Formula("~", left).simplify()
            if right == Formula.zero: return left
        elif self.op == "<->":
            if left == Formula.one: return right
            if left == Formula.zero: return Formula("~", right).simplify()
            if right == Formula.one: return left 
            if right == Formula.zero: return Formula("~", left).simplify()
        elif self.op == "->":
            if left == Formula.one: return right
            if left == Formula.zero: return Formula.one 
            if right == Formula.zero: return Formula("~", left).simplify()
            if right == Formula.one: return Formula.one 
        elif self.op == "<-":
            if right == Formula.one: return left
            if right == Formula.zero: return Formula.one 
            if left == Formula.zero: return Formula("~", right).simplify()
            if left == Formula.one: return Formula.one 

        return Formula(self.op, *(c.simplify() for c in self.__children))

    def cofactor(self, var : str, val : bool) -> "Formula":
        if self.op == "V" and self.c1 == var: return Formula.one if val else Formula.zero
        elif self.op in ["V", "C"]: return self
        else: return Formula(self.op, *(c.cofactor(var, val) for c in self.__children))
         
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
        else: return set().union(c.vars for c in self.__children)

    def flip(self, var : str) -> "Formula":
        if self.op == "V" and self.c1 == var: return Formula("~", self)
        elif self.op in ["V", "C"]: return self
        else: return Formula(self.op, *(c.flip(var) for c in self.__children))

    def __hash__(self) -> int:
        return self.__repr__().__hash__()

    def tseitin(self) -> tuple[list[set], dict[str, int]]:
        formula = self.simplify()
        if formula == Formula.zero or formula == Formula.one: return [], {}

        stack = [formula]
        subs = []
        vars2idx = set()
        while len(stack) > 0:
            top = stack.pop()
            if top.op == "C": 
                raise Exception(f"formula cannot contain 0s or 1s")
            vars2idx.add(str(top))
            if top.op == "V": continue
            subs.append(top) # all sub-formulas except variables
            for c in top.__children: stack.append(c)
        vars2idx = {k: v for v,k in enumerate(vars2idx)}

        # src: https://en.wikipedia.org/wiki/Tseytin_transformation
        cnf = [ { vars2idx[str(formula)] } ]
        for sub in subs:
            C = vars2idx[str(sub)]
            if sub.op == "V": continue
            A = vars2idx[str(sub.c1)] # 1 or 2-ary operation
            if sub.op == "~": # negation
                cnf += [{-C, -A}, {C, A}]
            else: # 2-ary operation
                B = vars2idx[str(sub.c2)]
                if sub.op == "^":
                    cnf += [{-C, -A, -B}, {-C, A, B}, {C, -A, B}, {C, A, -B}]
                elif sub.op == "&":
                    cnf += [{-A, -B, C}, {A, -C}, {B, -C}]
                elif sub.op == "<->":
                    cnf += [{-A, -B, C}, {A, B, C}, {A, -B, -C}, {-A, B, -C}]
                elif sub.op == "<-":
                    cnf += [{A, -B, -C}, {-A, C}, {B, C}]
                elif sub.op == "->":
                    cnf += [{-A, B, -C}, {A, C}, {-B, C}]
                elif sub.op == "|":
                    cnf += [{A, B, -C}, {-A, C}, {-B, C}]
                else:
                    raise Exception(f"operation {sub.op} unknown!")
        return cnf, vars2idx

    # def add_flip_vars(f : "Formula", target : set) -> tuple["Formula", dict[str, str]]:
    #     def rec(cur):
    #         if isinstance(cur, str) and cur not in target: # either constant or not in target set
    #             return cur, dict()
    #         elif isinstance(cur, str) and cur in target:
    #             z_x = "__z_" + cur 
    #             tree = ("^", cur, z_x)
    #             return tree, { z_x: cur }
    #         else:
    #             remainder = [ rec(c) for c in cur[1:] ]
    #             right = tuple(tree for tree, _ in remainder )
    #             new_vars = {} 
    #             for _, new_vars_sub in remainder: new_vars |= new_vars_sub
    #             return (cur[0], *right), new_vars
    #     tree, new_vars = rec(f.top)
    #     return Formula(tree), new_vars

# def outof(k : int, X : set) -> Formula:
#     if k <= 0: return Formula.parse("1") # all assignments for X satisfy this
#     if k > len(X): return Formula.parse("0") # no assignment for X can satisfy this
# 
#     x = next(iter(X))
#     Xmx = X - { x }
#     xf = Formula.parse(x)
#     if len(X) == 1 and k == 1: return xf
#     elif k == len(X): return xf & outof(k-1, Xmx)
#     elif k == 1: return xf | outof(1, Xmx) 
#     else: return xf & outof(k-1, Xmx) | outof(k, Xmx)
# 
# def reach(f : Formula, k : int, Y: set) -> tuple[Formula, set]:
#     # returns a (formula, set)-tuple (g,Y') where
#     # (exists Y'. g)(u) = 1 iff there exists v in B(Y) s.t. |v| <= k and f(u ^ v) = 1.
#     f_flip, new_vars = f.add_flip_vars(Y)
#     new_vars = set(flip_var for flip_var, var in new_vars.items() if var in Y)
#     return (~outof(k+1, new_vars) & f_flip).simplify(), new_vars

Formula.one = Formula.parse("1")
Formula.zero = Formula.parse("0")

if __name__ == "__main__":
    f = Formula.parse("((x <-> y) | z) & (x <-> y)") & Formula.parse("y")
    print(f)
    print(f.cofactor("y", False).simplify())
    print(f.flip("x").cofactor("y", False).simplify())
    print(f.tseitin())