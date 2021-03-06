import builtins

import pytest

from xonsh.ast import pdump, pprint_ast

from coral.formatter import reformat

from tools import nodes_equal


@pytest.mark.parametrize("inp, exp", [
("#a bad comment\n", "# a bad comment\n"),
("'single quotes'", '"single quotes"'),
# (r'r"\raw"', r'r"\raw"'),
("b'single quotes'", 'b"single quotes"'),
("True", "True"),
("None\n", "None\n"),
("...   \n", "...\n"),
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
("1   if   True   else   2", "1 if True else 2"),
("[ i*2 for i in [ 1, 2, 3 ] ]", "[i * 2 for i in [1, 2, 3]]"),
("[ i*2 for i in [ 1, 2, 3 ] if   True ]", "[i * 2 for i in [1, 2, 3] if True]"),
("[ i*2 for i in [ 1, 2, 3 ] for x in [4, 5] ]", "[i * 2 for i in [1, 2, 3] for x in [4, 5]]"),
("[ i*2 for i in [ 1, 2, 3 ] if True for x in [4, 5] if False ]",
 "[i * 2 for i in [1, 2, 3] if True for x in [4, 5] if False]"),
("{ i : i*2 for i in [ 1, 2, 3 ] }", "{i: i * 2 for i in [1, 2, 3]}"),
("{ i*2 for i in [ 1, 2, 3 ] }", "{i * 2 for i in [1, 2, 3]}"),
("(  i*2 for i in [ 1, 2, 3 ]  ) \n", "(i * 2 for i in [1, 2, 3])\n"),
("def f(): await   1\n", "def f():\n    await 1\n"),
("def f():\n yield  1\n", "def f():\n    yield 1\n"),
("def f():\n yield   from  [ ]\n", "def f():\n    yield from []\n"),
("2 <   3", "2 < 3"),
("2 <=   3", "2 <= 3"),
("2 >   3", "2 > 3"),
("2 >=   3", "2 >= 3"),
("2 ==   3", "2 == 3"),
("2 !=   3", "2 != 3"),
("2  <   3   <4", "2 < 3 < 4"),
("2 is   3", "2 is 3"),
("2 is   not  3", "2 is not 3"),
("2 in   [3]", "2 in [3]"),
("2 not   in   [3]", "2 not in [3]"),
("int(42.0)", "int(42.0)"),
("int(42.0,    2)", "int(42.0, 2)"),
("int(42.0,    base = 2)", "int(42.0, base=2)"),
('f"{True!r}" \n', 'f"{True!r}"\n'),
('f"int({42:.3})"   \n', 'f"int({42:.3})"\n'),
('f"int({42:.3!a})"   \n', 'f"int({42:.3!a})"\n'),
('f"float({42}) is {float(42):.3}"   \n', 'f"float({42}) is {float(42):.3}"\n'),
("''  .  join", '"".join'),
("'hello'   [ 1   :   ] ", '"hello"[1:]'),
("'hello'   [ :  5 ] ", '"hello"[:5]'),
("'hello'   [ 1   :  5 ] ", '"hello"[1:5]'),
("'hello'   [    :  ] ", '"hello"[:]'),
("'hello'   [    :  : ] ", '"hello"[:]'),
("'hello'   [    : : -  1 ] ", '"hello"[::-1]'),
("'hello'   [ 1   : : -  1 ] ", '"hello"[1::-1]'),
("'hello'   [    : 5 : -  1 ] ", '"hello"[:5:-1]'),
("'hello'   [  1  : 5 : -  1 ] ", '"hello"[1:5:-1]'),
("(1,  2,   *  'hello'  )", '(1, 2, *"hello")'),
("int   \n", "int\n"),
("async     def f(): await   1\n", "async def f():\n    await 1\n"),
("class   A  : \n pass\n", "class A:\n    pass\n"),
("class   A  (   ): \n pass\n", "class A:\n    pass\n"),
("class   A ( object ) : \n pass\n", "class A(object):\n    pass\n"),
("class   A ( object , metaclass = type ) : \n pass\n", "class A(object, metaclass=type):\n    pass\n"),
("def f(): return   \n", "def f():\n    return\n"),
("def f(): return   1\n", "def f():\n    return 1\n"),
("x    =    42\n", "x = 42\n"),
("x    =    42\ndel    x   \n", "x = 42\ndel x\n"),
("x    =    42\nx  +=    1\n", "x = 42\nx += 1\n"),
# Fix xonsh for the following
#("def f():\n  c  :    int   \n", "def f():\n    c: int\n"),
#("def f():\n  ( c  ):    int   \n", "def f():\n    (c): int\n"),
#("c  :   int  =  1\n", "c: int = 1\n"),
("for   i    in   [ 1, 2,  3 ]:\n\n  pass\n", "for i in [1, 2, 3]:\n    pass\n"),
("for   i    in   [ 1, 2,  3 ]:\n\n  pass\nelse:\n\n  pass\n\n",
 "for i in [1, 2, 3]:\n    pass\nelse:\n    pass\n"),
("async   for   i    in   [ 1, 2,  3 ]:\n\n  pass\n", "async for i in [1, 2, 3]:\n    pass\n"),
("while    True  :  \n  break  \n", "while True:\n    break\n"),
("while    True  :  \n  break  \nelse:\n  pass\n\n",
 "while True:\n    break\nelse:\n    pass\n"),
("if    True  :  \n  pass  \n", "if True:\n    pass\n"),
("if    True  :  \n  pass  \nelse:\n  pass\n",
 "if True:\n    pass\nelse:\n    pass\n"),
("if    True  :  \n  pass  \nelif  False :\n   pass  \nelse:\n  pass\n",
 "if True:\n    pass\nelif False:\n    pass\nelse:\n    pass\n"),
("if    True  :  \n  pass  \nelif  False :\n   pass  \nelif  None :\n   pass  \nelse:\n  pass\n",
 "if True:\n    pass\nelif False:\n    pass\nelif None:\n    pass\nelse:\n    pass\n"),
("with   None  :\n  pass\n", "with None:\n    pass\n"),
("async   with   None  :\n  pass\n", "async with None:\n    pass\n"),
("raise   \n", "raise\n"),
("raise     Exception\n", "raise Exception\n"),
("raise     Exception  from   KeyError  \n", "raise Exception from KeyError\n"),
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
