from formulas import BuddyContext, random_k_cnf, Formula, FormulaContext

def test_reordering():
    _, formula = random_k_cnf(20, 5*4, 3)
    vars = FormulaContext().parse(formula).vars
    optimized_size = None
    with BuddyContext(vars) as model:
        model.set_dynamic_reordering(True) # this doesn't work...
        f = model.parse(formula)
        # model.reorder(2)
        optimized_size = f.nodecount
    with BuddyContext(vars) as model:
        model.set_dynamic_reordering(False)
        f = model.parse(formula)
        assert optimized_size < f.nodecount

def test_bdd():
    with BuddyContext(["x", "y", "z"]) as model:
        x,y,z = model.var("x"), model.var("y"), model.var("z")

        f = model.parse("x & (y | z)")
        assert f.nodecount == 3
        assert f.satcount == 3 

        h = f & y
        assert h.satcount == 2 

        fx = f.flip("x")
        assert fx == model.parse("~x & (y | z)") 

        f1 = f.cofactor({"x": True})
        f0 = f.cofactor({"x": False})
        assert f1 == model.parse("y | z")
        assert f0 == model.false

        assert f.high == f1 # x is the top-most variable
        assert f.low == f0

        assert f1.vars == {"y", "z"}
        assert f0.vars == set()

        assert f.var_profile == {"x": 1, "y": 1, "z": 1}

        assert f1.var == "y"
        assert f0.var is None
        assert f.var == "x"

        assert not model.called_done

        # todo: evaluation

    assert model.called_done
