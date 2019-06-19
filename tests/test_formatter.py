import builtins

from coral.formatter import reformat

import pytest

from tools import nodes_equal


@pytest.mark.parametrize("inp, exp", [
("#a bad comment\n", "# a bad comment\n"),
])
def test_formatting(inp, exp):
    # first check that we get what we expect
    obs = reformat(inp)
    assert obs == exp
    # next check that the transformation is stable
    obs2 = reformat(obs)
    assert obs2 == obs
    # last, check that the initial AST is the same as the AST we produced
    # using the normal xonsh parser, barring line & column numbers
    exp_tree = builtins.__xonsh__.execer.parse(exp, {})
    obs_tree = builtins.__xonsh__.execer.parse(obs, {})
    assert nodes_equal(obs_tree, exp_tree, check_attributes=False)



