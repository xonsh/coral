# coral
The animating and life-affirming code formatter for Xonsh &amp; Python

`coral` is a Python and xonsh source code formatter. Similar to other
code formatters, coral provides a minimum of options to the user and
has strong opinions about what is the "right" way to format code.

## Differences with black
`coral` is PEP-8 compliant. However, PEP-8 does have some ambiguity.
[Black](https://black.readthedocs.io/en/stable/), a popular code
formatter for Python, holds some opinions and has some limitations
that coral addresses.

* Black only works on pure Python code. Coral works on Xonsh too!
* It is easier to type single quotes, so the default quotes are
  single quotes, not double quotes.

## Why the name "coral"
There are a few reasons for the name:

1. It is a color, like some other code formatters (e.g. black)
2. It is five letters long, like some other code formatters (e.g. black)
3. It is the [Pantone Color of Year 2019](https://store.pantone.com/uk/en/color-of-the-year-2019/)
   (the year the coral project was started!), unlike some other code formatters
   (e.g. black) which have never been color of the year.

Also note that conchs live in reefs, so `coral` also
has that going for it.

