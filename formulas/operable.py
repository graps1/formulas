from abc import ABC, abstractmethod
from . import parser

class Operable(ABC):

    def __init__(self, context: "OperableContext") -> None:
        self.ctx = context 

    @abstractmethod
    def __hash__(self): 
        raise NotImplementedError()

    @abstractmethod
    def __call__(self, assignment: dict[str, bool]) -> bool: 
        raise NotImplementedError()

    @abstractmethod
    def __copy__(self): 
        raise NotImplementedError()

    @abstractmethod
    def cofactor(self, x: str, value: bool) -> "Operable": 
        raise NotImplementedError()

    @abstractmethod
    def flip(self, x: str) -> "Operable": 
        raise NotImplementedError()

    @property
    @abstractmethod 
    def vars(self) -> set[str]: 
        raise NotImplementedError()

    def __or__(self, other: "Operable") -> "Operable": return self.ctx.apply("|", self, other)
    def __and__(self, other: "Operable") -> "Operable": return self.ctx.apply("&", self, other)
    def __xor__(self, other: "Operable") -> "Operable": return self.ctx.apply("^", self, other)
    def __rshift__(self, other: "Operable") -> "Operable": return self.ctx.apply("->", self, other)
    def __lshift__(self, other: "Operable") -> "Operable": return self.ctx.apply("<-", self, other)
    def __invert__(self): return self.ctx.apply("~", self)
    def biimp(self, other: "Operable") -> "Operable": return self.ctx.apply("<->", self, other)

class OperableContext(ABC):
    @property
    @abstractmethod
    def false(self) -> "Operable": 
        raise NotImplementedError()

    @property
    @abstractmethod
    def true(self) -> "Operable": 
        raise NotImplementedError()

    @abstractmethod
    def apply(self, op: str, *children) -> "Operable":
        raise NotImplementedError() 

    @abstractmethod
    def var(self, x: str) -> "Operable": 
        raise NotImplementedError()

    def parse(self, formula: str) -> "Operable":
        def rec(parsed):
            op, args = parsed[0], parsed[1:]
            if op == "C" and args[0] == "0": return self.false
            elif op == "C" and args[0] == "1": return self.true
            elif op == "V": return self.var(args[0])
            else: return self.apply(op, *(rec(a) for a in args))
        return rec(parser.parse(formula))
