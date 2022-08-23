from formulas import iter_assignments

def test_iter_assignments():
    assignments = list(iter_assignments(["x", "y"]))
    assert assignments == [
        {"x": False, "y": False},
        {"x": True, "y": False},
        {"x": False, "y": True},
        {"x": True, "y": True},
    ]
