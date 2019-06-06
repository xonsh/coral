import os
import sys

from setuptools import setup
from setuptools.command.sdist import sdist
from setuptools.command.install import install
from setuptools.command.develop import develop


TABLES = [
    "coral/lexer_table.py",
    "coral/parser_table.py",
]


def clean_tables():
    """Remove the lexer/parser modules that are dynamically created."""
    for f in TABLES:
        if os.path.isfile(f):
            os.remove(f)
            print("Removed " + f)

def build_tables():
    """Build the lexer/parser modules."""
    print("Building lexer and parser tables.")
    sys.path.insert(0, os.path.dirname(__file__))
    from coral.parser import Parser

    Parser(
        lexer_table="lexer_table",
        yacc_table="parser_table",
        outputdir="coral",
        yacc_debug=True,
    )
    sys.path.pop(0)


class cinstall(install):
    """coral specialization of setuptools install class."""

    def run(self):
        clean_tables()
        build_tables()
        super().run()


class csdist(sdist):
    """coral specialization of setuptools sdist class."""

    def make_release_tree(self, basedir, files):
        clean_tables()
        build_tables()
        super().make_release_tree(basedir, files)

class cdevelop(develop):
    """coral specialization of setuptools develop class."""

    def run(self):
        clean_tables()
        build_tables()
        develop.run(self)


def main():
    with open(os.path.join(os.path.dirname(__file__), "README.md"), "r") as f:
        readme = f.read()
    cmdclass = {
        "install": cinstall,
        "sdist": csdist,
        "develop": cdevelop,
        }
    scripts = [],
    skw = dict(
        name="living-coral",
        description="The animating and life-affirming code formatter for Xonsh & Python",
        long_description=readme,
        long_description_content_type="text/markdown",
        license="BSD",
        version='0.0.0',
        author="Anthony Scopatz",
        maintainer="Anthony Scopatz",
        author_email="scopatz@gmail.com",
        url="https://github.com/xonsh/coral",
        platforms="Cross Platform",
        classifiers=["Programming Language :: Python :: 3"],
        packages=[
            "coral",
        ],
        package_dir={"coral": "coral"},
        package_data={
            "coral": ["*.xsh"],
        },
        cmdclass=cmdclass,
        scripts=scripts,
    )
    skw["python_requires"] = ">=3.5"
    setup(**skw)


if __name__ == "__main__":
    main()
