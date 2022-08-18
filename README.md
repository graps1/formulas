Library for working with formulas, BDDs (via Buddy) and model counting problems. Requires Lark. Model counting via BDDs requires Buddy and model counting via #SAT solvers requires GPMC.

## Working with formulas

Instantiating formulas, cofactors, flipping and renaming variables:

```python
    import formulas
    f = formulas.Formula.parse("x & ( y | z ) & 1") # returns instance of formulas.Formula
    g = f.cofactor("x", True) # returns the cofactor f[x/1]
    h = f.flip("x") # replaces every occurrence of x by ~x
    k = f.rename({"x": "v"}) # renames x to v
    print(f, g, h, k)
```

Allowed operations are 
```
    ~ & | 
```

* Tseitin transformation
* GPMC api
* Buddy api
* Formula simplification
* Formula api
    * Operations on formulas

## Tests