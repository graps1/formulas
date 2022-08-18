from formulas import Formula

def test_parsing():
    f1 = Formula.parse("x & (y | z)")
    f2 = Formula.parse("x & y | z")
    assert f1 != f2
    f3 = Formula.parse("x <-> (y___ | z) | x & (a_2 ^ z)") 
    assert f3.vars == { "x", "y___", "z", "x", "a_2", "z" }
    f4 = Formula.parse("(x & y) & z")
    f5 = Formula.parse("x & (y & z)") 
    f6 = Formula.parse("x & y & z")
    assert f4 == f5 == f6
    
    x,y,z = Formula.parse("x"), Formula.parse("y"), Formula.parse("z")
    f = (x & y | z) >> x
    g = Formula.parse("(x & y | z) -> x")
    assert f == g

def test_simplification():
    formula_result_pairs = [
        ("x & 1 & 1", "x"),
        ("x & 0", "0"),
        ("x | 0 | 0", "x"),
        ("x | 1", "1"),
        ("x ^ 1 ^ (1 ^ 1)", "~x"), 
        ("x ^ 1 ^ 1", "x"),
        ("x <-> x", "1"),
        ("(x <-> y) <-> (x <-> y)", "1"),
        ("(~x ^ 0) ^ 1", "x"),
        ("(x & 1) | x", "x"),
        ("x -> x", "1"), 
        ("x <- x", "1"),
        ("0 -> x", "1"), 
        ("1 <- x", "1"),
        ("~x -> 0", "x"), 
        ("x <- 1", "x"),
        ("~~~~x", "x"),
        ("~~~x", "~x")
    ]
    for form, res in formula_result_pairs: 
        assert Formula.parse(form).simplify() == Formula.parse(res)

def test_cofactor():
    formula_result_pairs = [
        ("x & 1 & 1", "1 & 1 & 1"),
        ("x & (x <-> y)", "1 & (1 <-> y)")
    ]
    for form, res in formula_result_pairs: 
        assert Formula.parse(form).cofactor("x", True) == Formula.parse(res)

def test_tseitin():
    x, y, z  = Formula.parse("x"), Formula.parse("y"), Formula.parse("z")

    f = Formula.parse("x & y")
    cnf, sub2idx = f.tseitin()
    C, A, B = sub2idx[f], sub2idx[x], sub2idx[y]
    expected = [{C}, {-A, -B, C}, {A, -C}, {B, -C}]
    assert set(map(frozenset, cnf)) == set(map(frozenset, expected))

    # brackets are removed from associative operators
    # then the sub-formulas are parsed in a left-to-right manner
    # so the sub-formulas of f are: 
    # x, y, z, y&z, x&y&z
    f = Formula.parse("(x & y) & z") 
    g = Formula.parse("y & z")
    cnf, sub2idx = f.tseitin()
    Cf, Ax, Cg, Ay, Bz = sub2idx[f], sub2idx[x], sub2idx[g], sub2idx[y], sub2idx[z]
    expected = [{Cf}, {-Ax, -Cg, Cf}, {Ax, -Cf}, {Cg, -Cf}, {-Ay, -Bz, Cg}, {Ay, -Cg}, {Bz, -Cg}]
    assert set(map(frozenset, cnf)) == set(map(frozenset, expected))

def test_renaming():
    f = Formula.parse("x & y")
    g = f.rename({"x": "y", "y": "x"})
    assert g == Formula.parse("y & x")
