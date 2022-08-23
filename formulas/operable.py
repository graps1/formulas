from abc import ABC, abstractmethod
from . import parser

class classproperty(object):
    # src: https://stackoverflow.com/questions/5189699/how-to-make-a-class-property
    def __init__(self, f):
        self.f = f
    def __get__(self, obj, owner):
        return self.f(owner)

class Operable(ABC):

    def __init__(self, manager: "OperableContext") -> None:
        self._manager = manager

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
    def vars(self) -> list[str]: 
        raise NotImplementedError()

    def __or__(self, other: "Operable") -> "Operable": return self._manager.apply("|", self, other)
    def __and__(self, other: "Operable") -> "Operable": return self._manager.apply("&", self, other)
    def __xor__(self, other: "Operable") -> "Operable": return self._manager.apply("^", self, other)
    def __rshift__(self, other: "Operable") -> "Operable": return self._manager.apply("->", self, other)
    def __lshift__(self, other: "Operable") -> "Operable": return self._manager.apply("<-", self, other)
    def __invert__(self): return self._manager.apply("~", self)
    def biimp(self, other: "Operable") -> "Operable": return self._manager.apply("<->", self, other)
    def ite(self, o1: "Operable", o2: "Operable") -> "Operable": return (self & o1) | (~self & o2)

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
            if op == "C" and args[0] == "0": return self.false()
            elif op == "C" and args[0] == "1": return self.true()
            elif op == "V": return self.var(args[0])
            else: return self.apply(op, *args)
        return rec(parser.parse(formula))
