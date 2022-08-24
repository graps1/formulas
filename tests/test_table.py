from formulas import Table, TableContext
import copy

def test_operations():
    ctx = TableContext(print_mode="primes")
    table = Table(ctx, [False, True, True, False], ["x", "y"])
    assert table.assignment2idx({"x": True, "y": True}) == 3
    assert table.assignment2idx({"x": True, "y": False}) == 2 
    assert table == ctx.parse("x ^ y")

    table1 = ctx.parse("x & (y | z)")
    table2 = ctx.parse("x & y & z")
    table3 = ctx.parse("(y | z) & x")
    assert table2 <= table1
    assert table1 >= table2
    assert table3 == table1

    table4 = ctx.parse("x & y")
    t4_0, t4_1 = table4.branch("x")
    assert t4_1 == ctx.var("y") 
    assert t4_0 != ctx.false # variables don't agree!

    assert table.satcount() == 2
    assert table1.satcount() == 3

    primes = table1.prime_implicants()
    assert len(primes) == 2 and \
           {"x": True, "y": True} in primes and \
           {"x": True, "z": True} in primes

    cpy = copy.copy(table1)
    assert cpy == table1
