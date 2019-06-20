import builtins

import pytest

from xonsh.ast import pdump, pprint_ast

from coral.formatter import reformat

from tools import nodes_equal


@pytest.mark.parametrize("inp, exp", [
("#a bad comment\n", "# a bad comment\n"),
("'single quotes'", '"single quotes"'),
("True", "True"),
("None\n", "None\n"),
("42\n", "42\n"),
("42.84\n", "42.84\n"),
("42E+84\n", "4.2e+85\n"),
("[]\n", "[]\n"),
("[1]\n", "[1]\n"),
("[1, 2, 3]\n", "[1, 2, 3]\n"),
("()\n", "()\n"),
("(1)\n", "1\n"),
("(  1, )\n", "(1,)\n"),
("(1, 2, 3)\n", "(1, 2, 3)\n"),
("{}\n", "{}\n"),
("{  1 :  2}\n", "{1: 2}\n"),
("{1:2,3:4,5:6,}\n", "{1: 2, 3: 4, 5: 6}\n"),
("{1,2,3,}\n", "{1, 2, 3}\n"),
("lambda  : None\n", "lambda: None\n"),
("lambda x : None\n", "lambda x: None\n"),
("lambda x ,y : None\n", "lambda x, y: None\n"),
("lambda x = 10 : None\n", "lambda x=10: None\n"),
("lambda x ,y, z = 10 : None\n", "lambda x, y, z=10: None\n"),
("lambda x ,y,*, z = 10 : None\n", "lambda x, y, *, z=10: None\n"),
("lambda x ,y=42,*, z = 10 : None\n", "lambda x, y=42, *, z=10: None\n"),
("lambda *args: None\n", "lambda *args: None\n"),
("lambda  x, *y: None\n", "lambda x, *y: None\n"),
("lambda  x=42,*y: None\n", "lambda x=42, *y: None\n"),
("lambda  *y,x=42: None\n", "lambda *y, x=42: None\n"),
("lambda **kwargs: None\n", "lambda **kwargs: None\n"),
("lambda *args, **kwargs: None\n", "lambda *args, **kwargs: None\n"),
("lambda x,*args,**kwargs: None\n", "lambda x, *args, **kwargs: None\n"),
("lambda x, y=42,*args,**kwargs: None\n", "lambda x, y=42, *args, **kwargs: None\n"),
("lambda x, y=42,*args, z=43,**kwargs: None\n", "lambda x, y=42, *args, z=43, **kwargs: None\n"),
("1+2", "1 + 2"),
("1-2", "1 - 2"),
("1*2", "1 * 2"),
("1/2", "1 / 2"),
("1//2", "1 // 2"),
("1**2", "1 ** 2"),
("1@2", "1 @ 2"),
("1<<2", "1 << 2"),
("14>>2", "14 >> 2"),
("1|2", "1 | 2"),
("1^2", "1 ^ 2"),
("1&2", "1 & 2"),
("True  and    False", "True and False"),
("True  and    False and None", "True and False and None"),
("True  or    False", "True or False"),
("True  or    False   or    None", "True or False or None"),
("-  1", "-1"),
("+  1", "+1"),
("not   False", "not False"),
("~  True", "~True"),
])
def test_formatting(inp, exp):
    execer =  builtins.__xonsh__.execer
    # first check that we get what we expect
    try:
        obs = reformat(inp)
    except TypeError:
        print("Formatter failed!")
        pprint_ast(execer.parse(inp, {}))
        raise
    assert exp == obs, "Bad Tree:\n" + pdump(execer.parse(inp, {}))
    # next check that the transformation is stable
    obs2 = reformat(obs)
    assert obs == obs2
    # last, check that the initial AST is the same as the AST we produced
    # using the normal xonsh parser, barring line & column numbers
    exp_tree = execer.parse(exp, {})
    obs_tree = execer.parse(obs, {})
    assert nodes_equal(exp_tree, obs_tree, check_attributes=False)

