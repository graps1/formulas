Library for working with formulas, BDDs (via Buddy) and model counting problems. Requires Lark. Model counting via BDDs requires Buddy and model counting via #SAT solvers requires GPMC. This code was only tested on Linux.

## Installation

Run `python3 setup.py install` in the root directory.

## Formulas

Importing the `Formula` class:

```python
>>> from formulas import Formula
```

Instantiating formulas, cofactors, flipping and renaming variables:

```python
>>> f = Formula.parse("x & (y | z) & 1") # output: x&(y|z)&1
>>> len(f) # output: 7 (counts constants, variables, operators)
>>> g = f.cofactor("x", True) # output: 1&(y|z)&1
>>> h = f.flip("x") # output: ~x&(y|z)&1
>>> k = f.rename({"x": "v"}) # output: v&(y|z)&1
>>> t = g.simplify() # output: y|z (could remove some variables!)
```

Allowed operations are, in the following precedence order,

```
    ~ & | -> <- ^ <->
```

Multiple levels of associative operators such as `|`, `&` and `^` are NOT expanded, i.e. `(x & y) & z` is not the same as `x & (y & z)`. This might be changed later on...

```python
>>> f = Formula.parse("(x & y) & z")
>>> g = Formula.parse("x & (y & z)")
>>> f == g
False
``` 

Ambiguous formulas like `x <-> y <-> z` are interpreted in a left-first manner, but should be avoided:

```python
>>> f = Formula.parse("x <-> y <-> z")
>>> f
x<->(y<->z)
```

Formulas can be created either by parsing strings or by applying binary operations directly on other formulas. However, mind that Python's operators might take a [different precedence order](https://www.programiz.com/python-programming/precedence-associativity):

```python
>>> from formulas import Formula
>>> x,y,z = Formula.parse("x"), Formula.parse("y"), Formula.parse("z")
>>> f = (x & y | z) >> x
>>> g = Formula.parse("(x & y | z) -> x")
>>> f == g 
True
```

One can apply a [Tseitin transformation](https://en.wikipedia.org/wiki/Tseytin_transformation) to obtain the CNF of an equisatisfiable formula. The function returns a tuple `(cnf, sub2id)`, where `cnf` is a list (=set of clauses) of lists (=clauses) of integers (=literals that denote variables. If negative, then they denote the negated variable). `sub2id` is a mapping from sub-formulas to their corresponding variable in the Tseitin-transformed formula.

```python
>>> from formulas import Formula
>>> f = Formula.parse("x & (y | z)")
>>> cnf, sub2id = f.tseitin()
>>> cnf
[{5}, {1, 2, -4}, {4, -2}, {4, -1}, {5, -4, -3}, {3, -5}, {-5, 4}]
>>> sub2id
{z: 1, y: 2, x: 3, y|z: 4, x&(y|z): 5}
```

## BDDs / Buddy

This requires [Buddy](https://github.com/jgcoded/BuDDy) to work. You also need the installation directory; mine is `/usr/local/lib/libbdd.so`. To work with Buddy, import the `Buddy` and `BuddyNode` classes from `formulas`,

```python
>>> from formulas import Buddy, BuddyNode
```

Instantiating a model requires a pre-defined set of variables that is used as the initial variable order. Instantiating a `Buddy`-object should be done with a surrounding `with`-statement, since this allows a final clean-up:

```python
>>> with Buddy(["x", "y", "z"], lib="/usr/local/lib/libbdd.so") as model:
...     f = model.node("x & (y | z)") # returns a BuddyNode object
...     ...
```

There are some operations that can be called on a `BuddyNode`-object. For example,

```python
f = model.node("x & (y | z)") # can also be called with a Formula-object
f.dump("f.pdf") # creates a pdf with a graphic depiction of f
f.satcount # The number of satisfying assignments. Output: 3.0
f.nodecount # The BDD's size. Output: 3
f.var_profile # The number of nodes/variable. Output: {'x': 1, 'y': 1, 'z': 1}
f.var # The variable associated with this node. Output: 'x'
f == model.node("(~z -> y) & x") # checks for functional equivalency. Output: True
f.flip("x") == model.node("~x & (y | z)") # Flips a variable. Output: True
x, y, z = model.node("x"), model.node("y"), model.node("z")
f == x & (y | z) # Alternative method of BDD construction. Output: True
f.high == model.node("y | z") # The cofactor f[x/1]. Output: True
f.low == model.false # The cofactor f[x/0]. Output: True
model.node("y|z").depends_on # Set of dependent variables. Output: {'y', 'z'}
f.restrict(y) == x # The cofactor f[y/1]. Output: True
```

Todo: initial ordering heuristics, re-ordering after construction, etc.

## Model counting / GPMC

Besides Buddy, there is also an API to the [GPMC-model counter](https://git.trs.css.i.nagoya-u.ac.jp/k-hasimt/GPMC). Can also be downloaded from [here](https://cloudstore.zih.tu-dresden.de/index.php/s/xPPwZx7382kxP7i) or [here](https://zenodo.org/record/4878583). Besides "normal" model counting, it can also handle projected model counting, which introduces a set of existentially quantified variables. Basically, it can count the number of satisfying assignments of formulas like $\exists Y. \varphi$.

To instantiate the solver, you need to specify the solver's location. Mine is at `/usr/local/bin/gpmc`. 

```python
>>> from formulas import GPMC, Formula
>>> f = Formula.parse("x & (y | z)")
>>> solver = GPMC("/usr/local/bin/gpmc")
>>> solver.satcount(f) 
3
>>> solver.satcount(f, exists={"y"})
2
```

In the last example $\exists y. (x \land (y \lor z)) = x \lor (x \land z)$, only the two assignments $x=1, z=0$ and $x=1, z=1$ are counted.