import os
from ctypes import CDLL, c_double, c_int, c_char_p, byref, POINTER
from functools import cached_property, cache
from typing import Tuple, Union

from .formula import Formula

class BuddyNode:
	def __init__(self, model : "Buddy", node_id : int):
		self.node_id = node_id
		self.model = model 
		model._bdd.bdd_addref(self.node_id)

	def __del__(self):
		if not self.model.called_done: 
			self.model._bdd.bdd_delref(self.node_id)

	def __hash__(self): return self.node_id.__hash__()
	def __eq__(self, other : "BuddyNode"): 
		return isinstance(other, BuddyNode) and \
			   self.model == other.model and \
			   self.node_id == other.node_id

	# boolean operations on BDDs
	@cache
	def __invert__(self) -> "BuddyNode": 
		return self.model.apply("~", self)

	@cache
	def __and__(self, other : "BuddyNode") -> "BuddyNode": 
		return self.model.apply("&", self, other)

	@cache
	def __sub__(self, other : "BuddyNode") -> "BuddyNode": 
		return self & ~other

	@cache
	def __or__(self, other : "BuddyNode") -> "BuddyNode": 
		return self.model.apply("|", self, other)

	@cache
	def __xor__(self, other : "BuddyNode") -> "BuddyNode": 
		return self.model.apply("^", self, other)

	@cache
	def __lshift__(self, other : "BuddyNode") -> "BuddyNode": 
		return self.model.apply("->", self, other)

	@cache
	def __rshift__(self, other : "BuddyNode") -> "BuddyNode": 
		return other << self

	@cache
	def ite(self, if_true : "BuddyNode", if_false : "BuddyNode") -> "BuddyNode": 
		return self.model.apply("ite", self, if_true, if_false)

	@cache
	def equiv(self, other : "BuddyNode") -> "BuddyNode": 
		return self.model.apply("<->", self, other)

	@cache
	def flip(self, var : str) -> "BuddyNode":
		xf = self.model.node(var)
		f0, f1 = self.restrict(~xf), self.restrict(xf)
		return xf.ite(f0, f1)	

	@cached_property
	def var(self) -> str:
		if self.node_id in [0,1]: return None
		return self.model.vars[self.model._bdd.bdd_var(self.node_id)]

	@cached_property
	def low(self) -> "BuddyNode": 
		return BuddyNode(self.model, self.model._bdd.bdd_low(self.node_id))

	@cached_property
	def high(self) -> "BuddyNode": 
		return BuddyNode(self.model, self.model._bdd.bdd_high(self.node_id))

	@cached_property
	def satcount(self) -> int: 
		return self.model._bdd.bdd_satcount(self.node_id)

	@cached_property
	def nodecount(self) -> int:
		return self.model._bdd.bdd_nodecount(self.node_id)

	@cached_property
	def var_profile(self) -> dict[str, int]:
		# returns a variable-int-dictionary that counts how often variable nodes occur in this function
		profile = self.model._bdd.bdd_varprofile(self.node_id)
		return { var: count for var, count in zip(self.model.vars, profile.contents ) }

	@cached_property 
	def depends_on(self) -> set[str]:
		return set(v for v,c in self.var_profile.items() if c > 0)

	@cache
	def restrict(self, u : "BuddyNode") -> "BuddyNode": 
		return BuddyNode(self.model, self.model._bdd.bdd_restrict(self.node_id, u.node_id))

	def dump(self, filename="out.bdd"):
		if filename[-3:] == "dot":
			self.model._bdd.bdd_fnprintdot(c_char_p(filename.encode("UTF-8")), self.node_id)
		if filename[-3:] == "pdf":
			tempf = filename+".tmp"
			self.model._bdd.bdd_fnprintdot(c_char_p(tempf.encode("UTF-8")), self.node_id)
			os.system(f"dot -Tpdf {tempf} > {filename}")
			os.remove(tempf)
		else:
			self.model._bdd.bdd_fnsave(c_char_p(filename.encode("UTF-8")), self.node_id)
			with open(filename+"v", "w") as f:
				f.write("\n".join(self.model.vars))

class Buddy:
	def __init__(self, vars: list, lib="/usr/local/lib/libbdd.so") -> None: 
		buddy = CDLL(lib)

		buddy.bdd_varprofile.restype = POINTER(c_int * len(vars))
		buddy.bdd_satcount.restype = c_double
		buddy.bdd_init(1<<28, 1<<20)
		buddy.bdd_setmaxincrease(1<<27)
		buddy.bdd_setcacheratio(32)
		buddy.bdd_setvarnum(c_int(len(vars)))
		self._bdd = buddy

		# generate dict for varnames
		self.__vars = tuple(vars)
		self.__name2var_id = { x : k for k, x in enumerate(self.vars) }
		self.__called_done = False

	@property 
	def vars(self) -> tuple[str]:
		return self.__vars

	@property
	def called_done(self) -> bool:
		return self.__called_done

	@property
	def varcount(self) -> int: 
		return len(self.vars)

	@property 
	def nodenum(self) -> int:
		return self._bdd.bdd_getnodenum()

	def node(self, formula: Union[Formula, str]) -> BuddyNode:
		if isinstance(formula, str): formula = Formula.parse(formula)

		if formula.op == "C" and formula.c1 == "1":
			return BuddyNode(self, self.true)
		elif formula.op == "C" and formula.c1 == "0":
			return BuddyNode(self, self.false)
		elif formula.op == "V":
			if formula.c1 not in self.__name2var_id.keys():
				raise Exception(f"Variable {formula.c1} not found!")
			return BuddyNode(self, self._bdd.bdd_ithvar(self.__name2var_id[formula.c1]))
		else:
			nodes = [ self.node(c) for c in formula.children ]
			return self.apply(formula.op, *nodes)

	def __enter__(self): 
		return self

	def __exit__(self, exc_type, exc_value, exc_traceback): 
		self._bdd.bdd_done()
		self.__called_done =True

	@property
	def false(self) -> BuddyNode:
		return BuddyNode(self, self._bdd.bdd_false())

	@property
	def true(self) -> BuddyNode:
		return BuddyNode(self, self._bdd.bdd_true())

	def apply(self, op : str, u : BuddyNode, v : BuddyNode = None, w : BuddyNode = None) -> BuddyNode:
		result = None	
		if op in ('~', 'not', '!'):
			result =  self._bdd.bdd_not(u.node_id)
		elif op in ('or', r'\/', '|', '||'):
			result =  self._bdd.bdd_or(u.node_id, v.node_id)
		elif op in ('and', '/\\', '&', '&&', "band", "*", "land", "."):
			result =  self._bdd.bdd_and(u.node_id, v.node_id)
		elif op in ('xor', '^'):
			result =  self._bdd.bdd_xor(u.node_id, v.node_id)
		elif op in ('=>', '->', 'implies'):
			result =  self._bdd.bdd_imp(u.node_id, v.node_id)
		elif op in ('<=>', '<->', 'equiv'):
			result =  self._bdd.bdd_biimp(u.node_id, v.node_id)
		elif op in ('diff', '-'):
			result =  self._bdd.bdd_ite(u.node_id, self._bdd.bdd_not(u.node_id), self.false.node_id)
		elif op == 'ite':
			result =  self._bdd.bdd_ite(u.node_id, v.node_id, w.node_id)
		else:
			raise Exception(f'Unknown operator "{op}"')
		return BuddyNode(self, result)

	def set_dynamic_reordering(self, type=True):
		if type:
			self._bdd.bdd_autoreorder(3) # sifting as standard reordering
			self._bdd.bdd_enable_reorder()
		else:
			self._bdd.bdd_disable_reorder()

	def add_reorder_vars(self):
		self._bdd.bdd_varblockall()

	def reorder(self, method=3):
		rnames = {1:"WIN2", 2:"WIN2ITE", 3:"SIFT", 4:"SIFTITE", 5:"WIN3", 6:"WIN3ITE"}
		print("reorder via",rnames[method])
		self._bdd.bdd_reorder(method)

	@classmethod
	def load(file_bdd, vars) -> Tuple["Buddy", BuddyNode]:
		# returns new root node of read bdd
		# print(f"load {file_bdd} ...")
		root = c_int()
		buddy = Buddy(vars)
		buddy._bdd.bdd_fnload(c_char_p(file_bdd.encode("UTF-8")), byref(root))
		buddy._bdd.bdd_addref(root.value)
		# print(f"loaded {file_bdd}")
		return buddy, BuddyNode(buddy, root.value)
