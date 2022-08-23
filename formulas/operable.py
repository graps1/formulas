from abc import ABC, abstractmethod
from . import parser

class classproperty(object):
    # src: https://stackoverflow.com/questions/5189699/how-to-make-a-class-property
    def __init__(self, f):
        self.f = f
    def __get__(self, obj, owner):
        return self.f(owner)

class Operable(ABC):

    @classmethod
    @abstractmethod
    def var(cls, x: str) -> "Operable": raise NotImplementedError()

    @classproperty
    @abstractmethod
    def true(cls): raise NotImplementedError()

    @classproperty
    @abstractmethod
    def false(cls): raise NotImplementedError()

    @abstractmethod
    def __hash__(self): raise NotImplementedError()

    @abstractmethod
    def cofactor(self, x: str, value: bool) -> "Operable": raise NotImplementedError()

    @abstractmethod
    def flip(self, x: str) -> "Operable": raise NotImplementedError()

    @abstractmethod
    def __call__(self, assignment: dict[str, int]) -> int: raise NotImplementedError()

    @abstractmethod
    def __copy__(self): raise NotImplementedError()

    @abstractmethod
    def apply(self, op: str, o1: "Operable"=None, o2: "Operable"=None) -> "Operable":
        raise NotImplementedError() 

    @classmethod
    def parse(cls, formula: str) -> "Operable":
        def rec(parsed):
            op, args = parsed[0], parsed[1:]
            if op == "C" and args[0] == "0": return cls.false()
            elif op == "C" and args[0] == "1": return cls.true()
            elif op == "V": return cls.var(args[0])
            else: return cls.apply(op, *args)
        return rec(parser.parse(formula))

    def __or__(self, other: "Operable") -> "Operable": return self.apply("|", other)
    def __and__(self, other: "Operable") -> "Operable": return self.apply("&", other)
    def __xor__(self, other: "Operable") -> "Operable": return self.apply("^", other)
    def __rshift__(self, other: "Operable") -> "Operable": return self.apply("->", other)
    def __lshift__(self, other: "Operable") -> "Operable": return self.apply("<-", other)
    def __invert__(self): return self.apply("~")
    def biimp(self, other: "Operable") -> "Operable": return self.apply("<->", other)
    def ite(self, o1: "Operable", o2: "Operable") -> "Operable": return (self & o1) | (~self & o2)

