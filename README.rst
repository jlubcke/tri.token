.. image:: https://travis-ci.org/TriOptima/tri.struct.svg?branch=master
    :target: https://travis-ci.org/TriOptima/tri.struct
.. image:: http://codecov.io/github/TriOptima/tri.struct/coverage.svg?branch=master
    :target: http://codecov.io/github/TriOptima/tri.struct?branch=master

tri.struct
==========

tri.struct supplies classes that can be used like dictionaries and as objects with attribute access at the same time. There are three classes:

- Struct: mutable struct
- FrozenStruct: immutable struct
- NamedStruct: mutable struct with restrictions on which fields can be present

Some niceties include:

- Predictable repr() so it's easy to write tests
- Plus operator for Struct (`Struct(a=1) + Struct(b=1) == Struct(a=1, b=1)`)

Example
-------

.. code:: python

    >>> foo = Struct()
    >>> foo.a = 1
    >>> foo['a']
    1
    >>> foo['a'] = 2
    >>> foo.a
    2


Running tests
-------------

You need tox installed then just `make test`.


License
-------

BSD


Documentation
-------------

http://tristruct.readthedocs.org.
