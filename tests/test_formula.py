from formulas import  FormulaContext

def test_parsing():
    ctx = FormulaContext()
    f1 = ctx.parse("x & (y | z)")
    f2 = ctx.parse("x & y | z")
    assert f1 != f2
    f3 = ctx.parse("x <-> (y___ | z) | x & (a_2 ^ z)") 
    assert f3.vars == { "x", "y___", "z", "x", "a_2", "z" }
    f4 = ctx.parse("(x & y) & z")
    f5 = ctx.parse("x & (y & z)")
    assert f4 != f5

    x,y,z = ctx.parse("x"), ctx.parse("y"), ctx.parse("z")
    f = (x & y | z) >> x
    g = ctx.parse("(x & y | z) -> x")
    assert f == g

def test_simplification():
    formula_result_pairs = [
        ("~0", "1"),
        ("~1", "0"),
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
        ("~~~x", "~x"),
        ("(1 & (x | z)) | y", "(x | z) | y")
    ]
    ctx = FormulaContext()
    for form, res in formula_result_pairs: 
        assert ctx.parse(form).simplify() == ctx.parse(res).simplify()

def test_cofactor():
    formula_result_pairs = [
        ("x & 1 & 1", "1 & 1 & 1"),
        ("x & (x <-> y)", "1 & (1 <-> y)")
    ]
    ctx = FormulaContext()
    for form, res in formula_result_pairs: 
        assert ctx.parse(form).cofactor({"x": True}) == ctx.parse(res)

def test_tseitin():
    ctx = FormulaContext()
    x, y, z  = ctx.var("x"), ctx.var("y"), ctx.var("z")

    f = ctx.parse("x & y")
    cnf, sub2idx = f.tseitin()
    C, A, B = sub2idx[f], sub2idx[x], sub2idx[y]
    expected = [{C}, {-A, -B, C}, {A, -C}, {B, -C}]
    assert set(map(frozenset, cnf)) == set(map(frozenset, expected))

    # brackets are removed from associative operators
    # then the sub-formulas are parsed in a left-to-right manner
    # so the sub-formulas of f are: 
    # x, y, z, y&z, x&y&z
    f = ctx.parse("x & (y & z)").simplify()
    g = ctx.parse("y & z")
    cnf, sub2idx = f.tseitin()
    Cf, Ax, Cg, Ay, Bz = sub2idx[f], sub2idx[x], sub2idx[g], sub2idx[y], sub2idx[z]
    expected = [{Cf}, {-Ax, -Cg, Cf}, {Ax, -Cf}, {Cg, -Cf}, {-Ay, -Bz, Cg}, {Ay, -Cg}, {Bz, -Cg}]
    assert set(map(frozenset, cnf)) == set(map(frozenset, expected))

def test_renaming():
    ctx = FormulaContext()
    f = ctx.parse("x & y")
    g = f.replace({"x": "y", "y": "x"})
    assert g == ctx.parse("y & x")
