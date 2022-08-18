from formulas import Buddy, BuddyNode, Formula

def test_bdd():
    with Buddy(["x", "y", "z"]) as model:
        x,y,z = model.node("x"), model.node("y"), model.node("z")

        f = model.node("x & (y | z)")
        assert f.nodecount == 3
        assert f.satcount == 3 

        h = f & y
        assert h.satcount == 2 

        fx = f.flip("x")
        assert fx == model.node("~x & (y | z)")

        f1 = f.restrict(x)
        f0 = f.restrict(~x)
        assert f1 == model.node("y | z")
        assert f0 == model.false

        assert f.high == f1 # x is the top-most variable
        assert f.low == f0

        assert f1.depends_on == {"y", "z"}
        assert f0.depends_on == set()

        assert f.var_profile == {"x": 1, "y": 1, "z": 1}

        assert f1.var == "y"
        assert f0.var is None
        assert f.var == "x"

        assert not model.called_done

    assert model.called_done
