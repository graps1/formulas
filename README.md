Library for working with formulas, BDDs (via Buddy) and model counting problems. Requires Lark. Model counting via BDDs requires Buddy and model counting via #SAT solvers requires GPMC.

## Installation

Requirements

* Lark

## Working with formulas

Instantiating formulas, cofactors, flipping and renaming variables:

```python
>>> from formulas import Formula
>>> f = Formula.parse("x & (y | z) & 1") # output: x&(y|z)&1
>>> g = f.cofactor("x", True) # output: 1&(y|z)&1
>>> h = f.flip("x") # output: ~x&(y|z)&1
>>> k = f.rename({"x": "v"}) # output: v&(y|z)&1
>>> t = g.simplify() # output: y|z (could remove some variables!)
```

Allowed operations are, in the following precedence order,

```
    ~ & | -> <- ^ <->
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

One can apply a [Tseitin transformation](https://en.wikipedia.org/wiki/Tseytin_transformation) to obtain the CNF of an equisatisfiable formula. The function returns a tuple `(cnf, sub2id)`, where `cnf` is a list (=the set of clauses) of lists (=clause) of integers (=literals that denote variables. If negative, then they denote the negated variable). `sub2id` is a mapping from sub-formulas to their corresponding variable in the Tseitin-transformed formula.

```python
>>> from formulas import Formula
>>> f = Formula.parse("x & (y | z)")
>>> cnf, sub2id = f.tseitin()
>>> cnf
[{5}, {1, 2, -4}, {4, -2}, {4, -1}, {5, -4, -3}, {3, -5}, {-5, 4}]
>>> sub2id
{z: 1, y: 2, x: 3, y|z: 4, x&(y|z): 5}
```

## BDDs

## Model counting and BDDs

* Tseitin transformation
* GPMC api
* Buddy api
* Formula simplification
* Formula api
    * Operations on formulas

## Tests