from formulas import GPMC, Formula, FormulaContext

def test_satcount():
    solver = GPMC()
    ctx = FormulaContext(solver=solver)
    f = ctx.parse("x & (y | z)")
    assert f.satcount() == 3
    assert f.satcount(exists={"x"}) == 3
    assert f.satcount(exists={"y"}) == 2 # x/1 and for z/0 choose y/1, for z/1 d.c.

    f = ctx.parse("~x | (y & ~z)")
    assert f.satcount() == 5 

    f = ctx.parse("(x & y) ^ (z <-> e)")
    assert f.satcount() + (~f).satcount() == 2**4

    f0, f1 = map(lambda it: it.simplify(), f.branch("x"))
    m1 = 2**len(f.vars - f1.vars - {"x"})
    m0 = 2**len(f.vars - f0.vars - {"x"})
    assert f1.satcount()*m1 + f0.satcount()*m0 == f.satcount()