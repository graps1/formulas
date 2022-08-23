from typing import Iterable
from .operable import Operable, OperableContext
from .utils import iter_assignments
import copy

class Table(Operable):
    def __init__(self, context: "TableContext", table: list[int], vars: list[str]):
        super().__init__(context)
        self.__table = table
        self.__vars = vars
        assert 2**len(self.vars) == len(self.table)

    @property 
    def table(self) -> list[int]:
        return self.__table

    # --- ABSTRACT METHODS ---

    @property 
    def vars(self) -> list[str]:
        return self.__vars

    def __call__(self, assignment: dict[str, bool]) -> bool:
        return self.table[self.assignment2idx(assignment)]

    def __hash__(self): 
        return tuple(self.table).__hash__() + tuple(self.vars).__hash__()

    def __copy__(self): 
        return Table(self, self.ctx, self.table.copy(), self.vars.copy())

    def cofactor(self, x: str, value: bool) -> "Table": 
        new_vars = self.vars.copy()
        new_vars.remove(x)
        table = Table(self.ctx, [0 for _ in range(2**len(new_vars))], new_vars)
        for ass in iter_assignments(new_vars):
            idx = table.assignment2idx(ass)
            table.table[idx] = self(ass | { x: value })
        return table

    def flip(self, x: str) -> "Table": 
        table = copy.copy(self)
        for ass in iter_assignments(self.vars):
            table[ass] = self(ass | { x: not ass[x] })
        return table

    # --- END ABSTRACT METHODS ---

    @property
    def satcount(self):
        return sum(self.table)

    def __setitem__(self, key, val):
        if isinstance(key, dict): 
            key = self.assignment2idx(key)
        self.table[key] = val

    def __getitem__(self, key):
        return self(key)

    def resort(self, new_vars: Iterable[str]) -> "Table":
        assert set(new_vars) == set(self.vars)
        cpy = copy.copy(self)
        for ass in iter_assignments(new_vars):
            cpy[ass] = self[ass]
        return cpy

    def assignment2idx(self, assignment: dict[str, bool]) -> int:
        table_index = 0
        for idx in range(len(self.vars)):
            v = self.vars[len(self.vars)-idx-1]
            if assignment[v]: table_index += 2**idx
        return table_index

    def __repr__(self):
        ret = " ".join(self.vars) + " f" + "\n" + "-"*(len(self.vars)*2+1) 
        for ass in iter_assignments(self.vars):
            ret += "\n" + " ".join({True: "1", False: "0"}[ass[x]] for x in self.vars)
            ret += " " + str(int(self(ass)))
        ret += "\n"
        return ret

    def __le__(self, other):
        return isinstance(other, Table) and \
               other.ctx == self.ctx and \
               set(other.vars) == set(self.vars) and \
               all(other[ass] <= self[ass] for ass in iter_assignments(self.vars))

    def __ge__(self, other):
        other <= self

    def __eq__(self, other):
        return other <= self and self <= other

    def __ne__(self, other):
        return not (other == self)

class TableContext(OperableContext):
    @property
    def false(self) -> "Table": 
        return Table(self, [False], [])

    @property
    def true(self) -> "Table": 
        return Table(self, [True], [])

    def apply(self, op: str, *children) -> "Table":
        all_vars = list( set().union( *(set(c.vars) for c in children)) ) 
        new_table = Table(self, [0 for _ in range(2**len(all_vars))], all_vars)
        for ass in iter_assignments(all_vars):
            val = None
            if op == "~": val = not children[0](ass)
            elif op == "&": val = all(c(ass) for c in children)
            elif op == "|": val = any(c(ass) for c in children)
            elif op == "^": val = (children[0](ass) != children[1](ass))
            elif op == "->": val = (not children[0](ass) or children[1](ass))
            elif op == "<-": val = (children[0](ass) or not children[1](ass))
            elif op == "<->": val = (children[0](ass) == children[1](ass))
            new_table[ass] = val
        return new_table

    def var(self, x: str) -> "Table":
        return Table(self, [False, True], [x])
