pytest-everyfunc
================

A pytest plugin to detect completely untested functions using coverage.

Motivation
----------

If you add pytest-everyfunc to your CI, you can prevent yourself from
checking in code that adds functions without tests.

Installation
------------

::

    $ pip install pytest-everyfunc

Usage
-----

::

    $ pytest --cov=mypackage --fail-on-untested
    ...
    tests/test_script.py ........      [100%]
    mypackage/foo.py:253: untested function: rv_logpdf
    mypackage/bar.py:717: untested function: norms
    mypackage/baz.py:86: untested function: prior_predictive_check_plot
    Exit: Untested functions found.


The output shows the functions that were not called.

If --fail-on-untested is set, then the exit code is 32 (regardless whether tests succeed).

::

    $ echo $?
    32

git hook
--------

add to .git/hooks/pre-commit the pytest command above.
