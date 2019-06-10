.. image:: https://travis-ci.org/TriOptima/tri.token.svg?branch=master
    :target: https://travis-ci.org/TriOptima/tri.token


.. image:: https://codecov.io/github/TriOptima/tri.token/coverage.svg?branch=master
    :target: https://codecov.io/github/TriOptima/tri.token?branch=master


tri.token
=========

tri.token provides enriched enum functionality. tri.token enum structures are declared using:

- TokenAttribute: overridable attribute definitions with support for dynamic values.
- Token: holds TokenAttributes objects.
- TokenContainer: holds Token objects.

In other words: a Token is an enum which has TokenInstance members. Token instances are declared within TokenContainer(s).


Basic usage
-----------

.. code:: python

    from tri_token import Token, TokenAttribute, TokenContainer, PRESENT


    class Taste(Token):
        name = TokenAttribute()
        display_name = TokenAttribute(value=lambda **kwargs: kwargs['name'].upper() + '!!')
        opinion = TokenAttribute()


    class Tastes(TokenContainer):
        vanilla = Taste()
        pecan_nut = Taste(display_name="pecan nutz", opinion="Tasty")


    # A TokenContainer is a collection of Token objects.
    assert Tastes.vanilla in Tastes

    # The order of Token objects in a TokenContainer is by order of declaration.
    assert list(Tastes) == [Tastes.vanilla, Tastes.pecan_nut]
    assert list(Tastes) != [Tastes.pecan_nut, Tastes.vanilla]

    # Magic for 'name' TokenAttribute. It is set automatically from the token declaration within it's container.
    assert Tastes.vanilla.name == "vanilla"

    # A TokenAttribute will have a None value if not set during Token instantiation.
    assert Tastes.vanilla.opinion is None

    # A TokenAttribute can have a dynamic value, derived from the invocation to the callable
    # set as 'value' in the TokenAttribute definition
    # (see declaration of 'display_name' TokenAttribute further up in the code).

    # The real value of the token attribute will be the return value of an invocation to said callable.
    # The invocation will receive the values of all other token attributes passed as keyword arguments.
    assert Tastes.vanilla.display_name == "VANILLA!!"

    # TokenAttribute dynamic value behavior is overridden/not used if value is set explicitly during Token instantiation.
    assert Tastes.pecan_nut.display_name == "pecan nutz"

    # A TokenContainer can be rendered as csv, excel, rst etc
    assert """\
    +--------------+---------+
    | display_name | opinion |
    +==============+=========+
    |  VANILLA!!   |         |
    +--------------+---------+
    |  pecan nutz  |  Tasty  |
    +--------------+---------+\
    """ == Tastes.to_rst(['display_name', 'opinion'])


Optional token attributes
-------------------------

.. code:: python

    # A TokenAttribute may be declared as having optional dynamic values.
    # That is, we want these dynamic attributes to be evaluated sometimes, but not always.
    # In the example below, we want some superheroes to have homes, but not others.

    SUPERHERO_HOMES = {'superman': 'Fortress of Solitude',
                       'batman': 'Batcave'}


    class Superhero(Token):
        name = TokenAttribute()
        home = TokenAttribute(optional_value=lambda name, **_: SUPERHERO_HOMES[name])


    # The PRESENT special value is used during Token instantiation to decide what
    # optional token attributes should be evaluated.
    class Superheroes(TokenContainer):
        batman = Superhero(home=PRESENT)
        hawkman = Superhero()
        wonder_woman = Superhero(home='Themyscira')

    # Batman has a home, but poor Hawkman does not.
    assert Superheroes.batman.home == 'Batcave'
    assert Superheroes.hawkman.home is None

    # Just as with dynamic attributes, the logic for TokenAttribute optional dynamic values is overridden
    if value is set explicitly during Token instantiation.
    assert Superheroes.wonder_woman.home = 'Themyscira'

    # As a shortcut, PRESENT for specific optional token attributes may be assigned to
    # variables, and used in declarations, for enhanced readability.
    # This is useful when one has tokens with many attributes declared using dynamic values,
    # but we don't want all of them to be evaluated in all tokens.
    home = PRESENT('home')

    class Superheroes(TokenContainer):
        batman = Superhero(home)
        hawkman = Superhero()

    # Again, Batman has a home, but poor Hawkman does not.
    assert Superheroes.batman.home == 'Batcave'
    assert Superheroes.hawkman.home is None


TokenAttribute inheritance
--------------------------

.. code:: python

    class FooToken(Token):
        foo = TokenAttribute(value=lambda **kwargs: 'foo_value')

    class BarToken(Token):
        bar = TokenAttribute()

    class FieToken(FooToken, BarToken):
        fie = TokenAttribute()

    class FooBarFieTokenContainer(TokenContainer):
        t = FieToken(fie=3)

    assert dict(FooBarFieTokenContainer.t) == {'foo': 'foo_value', 'bar': None, 'name': 't', 'fie': 3}


TokenAttribute container inheritance
------------------------------------

.. code:: python

    class MyToken(Token):

        name = TokenAttribute()
        stuff = TokenAttribute()


    class MyTokens(TokenContainer):

        foo = MyToken(stuff='Hello')
        bar = MyToken(stuff='World')

    assert MyTokens.foo in MyTokens

    class MoreTokens(MyTokens):
        boink = MyToken(stuff='Other Stuff')

    assert MyTokens.foo in MoreTokens

    assert list(MoreTokens) == [MyTokens.foo, MyTokens.bar, MoreTokens.boink]
    assert MoreTokens.foo is MyTokens.foo


For more tri.token examples, please have a look at the contents of tests/test_tokens.py in the installation directory.

.. _test_tokens: tests/test_tokens.py


Running tests
-------------

You need tox installed then just `make test`.


License
-------

BSD


Documentation
-------------

http://tritoken.readthedocs.org.
