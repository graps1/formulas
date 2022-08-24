from formulas import GPMC, Formula, FormulaContext

def test_satcount():
    ctx = FormulaContext()
    f = ctx.parse("x & (y | z)")
    solver = GPMC()
    sc = solver.satcount
    assert sc(f) == 3
    assert sc(f, exists={"x"}) == 3
    assert sc(f, exists={"y"}) == 2 # x/1 and for z/0 choose y/1, for z/1 d.c.

    f = ctx.parse("~x | (y & ~z)")
    assert sc(f) == 5 

    f = ctx.parse("(x & y) ^ (z <-> e)")
    assert sc(f) + sc(~f) == 2**4

    f0, f1 = map(lambda it: it.simplify(), f.branch("x"))
    m1 = 2**len(f.vars - f1.vars - {"x"})
    m0 = 2**len(f.vars - f0.vars - {"x"})
    assert sc(f1)*m1 + sc(f0)*m0 == sc(f)