from copy import copy, deepcopy
import pickle
import sys

import pytest

from tri.token import TokenContainer, Token, TokenAttribute, PRESENT

try:
    from tri.cache.memoize import memoize
except ImportError:
    memoize = None


class MyToken(Token):

    name = TokenAttribute()
    stuff = TokenAttribute()


class MyTokens(TokenContainer):

    foo = MyToken(stuff='Hello')
    bar = MyToken(stuff='World')


def test_in():
    assert MyTokens.foo in MyTokens

    class OtherTokens(MyTokens):
        boink = MyToken()

    assert MyTokens.foo in OtherTokens


def test_immutable():
    d = {MyTokens.foo: 17}
    assert d[MyTokens.foo] is 17

    with pytest.raises(TypeError):
        MyTokens.foo.stuff = "Not likely"


def test_immutable_attribute_values():

    with pytest.raises(ValueError) as exception_info:
        MyToken(stuff=[])

    assert "Attribute stuff has unhashable value: []" == str(exception_info.value)


def test_copy():
    assert copy(MyTokens.foo) is MyTokens.foo
    assert copy([MyTokens.foo]) == [MyTokens.foo]


def test_deepcopy():
    assert deepcopy(MyTokens.foo) is MyTokens.foo
    assert deepcopy([MyTokens.foo]) == [MyTokens.foo]


def test_pickle():
    s = pickle.dumps(MyTokens.foo, pickle.HIGHEST_PROTOCOL)
    assert pickle.loads(s) == MyTokens.foo


def test_modification():
    existing_token = MyTokens.foo
    attributes = dict(existing_token)
    attributes.update(stuff="Other stuff")
    new_token = type(existing_token)(**attributes)
    assert new_token.stuff == "Other stuff"
    assert isinstance(new_token, MyToken)


def test_attribute_ordering():

    class OrderedToken(Token):
        first = TokenAttribute()
        second = TokenAttribute()
        third = TokenAttribute()
        fourth = TokenAttribute()
        fifth = TokenAttribute()

    assert OrderedToken.attribute_names() == ('name', 'first', 'second', 'third', 'fourth', 'fifth')


def test_token_sorting():

    class OrderedTokens(TokenContainer):
        first = MyToken()
        second = MyToken()
        third = MyToken()
        fourth = MyToken()
        fifth = MyToken()

    assert list(OrderedTokens) == list(sorted(set(OrderedTokens)))


def test_names():
    assert [token.name for token in MyTokens] == ['foo', 'bar']


@pytest.mark.skipif(sys.version_info > (3, 0), reason="unicode is python 2")
def test_unicode():
    assert unicode(MyToken()) == u'(unnamed)'
    assert unicode(MyTokens.foo) == u'foo'


def test_str():
    assert str(MyToken()) == "(unnamed)"
    assert str(MyTokens.foo) == "foo"
    assert str(list(MyTokens)) == "[<MyToken: foo>, <MyToken: bar>]"


def test_type_str():
    assert "<class 'tests.test_tokens.MyToken'>" == str(MyToken)
    assert "<class 'tests.test_tokens.MyToken'>" == str(type(MyTokens.foo))
    assert "<class 'tests.test_tokens.MyTokens'>" == str(MyTokens)


def test_repr():
    assert repr(MyToken()) == "<MyToken: (unnamed)>"
    assert repr(MyTokens.foo) == "<MyToken: foo>"
    assert repr(list(MyTokens)) == "[<MyToken: foo>, <MyToken: bar>]"


def test_other_field():
    assert [token.stuff for token in MyTokens] == ['Hello', 'World']


def test_get():
    assert MyTokens.get('foo') is MyTokens.foo
    assert MyTokens.get('ASDASDDS', 'default') == 'default'


def test_inheritance():

    class FooToken(Token):
        foo = TokenAttribute()

    class BarToken(Token):
        bar = TokenAttribute()

    class FieToken(FooToken, BarToken):
        fie = TokenAttribute()

    t = FieToken(foo=1, bar=2, fie=3)
    assert dict(t) == dict(name=None, foo=1, bar=2, fie=3)


def test_container_inheritance_ordering():

    class MoreTokens(MyTokens):
        boink = MyToken(stuff='Other Stuff')

    assert list(MoreTokens) == [MyTokens.foo, MyTokens.bar, MoreTokens.boink]
    assert MoreTokens.foo is MyTokens.foo


def test_container_inheritance_override():

    class MoreTokens(MyTokens):
        foo = MyToken(stuff='Override')

    assert len(MoreTokens) == 2
    assert MoreTokens.foo != MyTokens.foo
    assert MoreTokens.bar is MyTokens.bar
    assert MoreTokens.foo.stuff == 'Override'


def test_token_without_subclassing():

    class TestTokens(TokenContainer):
        foo = Token(bar=17)
        fie = Token(foe="Fum")
        one = Token()
        two = Token()
        three = Token()

    f = TestTokens.foo
    assert f.name == "foo"
    assert f.bar == 17
    assert ('name', ) == f.attribute_names()  # Might be unexpected, but if you want ('name', 'bar') subclass is the way to go...

    f2 = TestTokens.fie
    assert f2.name == "fie"
    assert f2.foe == "Fum"

    assert list(TestTokens) == list(sorted(set(TestTokens)))


@pytest.mark.skipif(memoize is None, reason="tri.cache.memoize not available")
def test_extra_stuff():

    @memoize
    def alpha_ordered():
        return sorted(ExtendedTokens, key=lambda token: token.name)

    class ExtendedTokens(MyTokens):

        @classmethod
        def alpha_index(cls, index):
            return alpha_ordered()[index]

    assert [ExtendedTokens.alpha_index(index) for index in range(len(ExtendedTokens))] == [ExtendedTokens.bar, ExtendedTokens.foo]


def test_default_value():

    class TokenWithDefaultValue(Token):
        name = TokenAttribute()
        another_name = TokenAttribute(default="a nonymous")

    token = TokenWithDefaultValue(name="a name")
    assert token.another_name == "a nonymous"

    token = TokenWithDefaultValue(name="a naome",
                                  another_name="explicit override")
    assert token.another_name == "explicit override"


def test_default_value_none_override():
    class TokenWithDefaultValue(Token):
        name = TokenAttribute()
        another_name = TokenAttribute(default="a nonymous")

    token = TokenWithDefaultValue(name="a name",
                                  another_name=None)
    assert token.another_name is None


def test_derived_value():
    class TokenWithDerivedValue(Token):
        name = TokenAttribute()
        another_name = TokenAttribute(value=lambda name, **_: "also " + name)

    token = TokenWithDerivedValue(name="a name")
    assert token.another_name == "also a name"

    token = TokenWithDerivedValue(name="not used", another_name="explicit override")
    assert token.another_name == "explicit override"


def test_optional_value():

    class TokenWithOptionalValue(Token):
        name = TokenAttribute()
        another_name = TokenAttribute(optional_value=lambda name, **_: "also " + name)

    token = TokenWithOptionalValue(name="a name")
    assert token.another_name is None

    token = TokenWithOptionalValue(name="a name", another_name=PRESENT)
    assert token.another_name == "also a name"

    token = TokenWithOptionalValue(name="not used", another_name="explicit override")
    assert token.another_name == "explicit override"


def test_fancy_optional_value_marker():

    class TokenWithOptionalValue(Token):
        name = TokenAttribute()
        another_name = TokenAttribute(optional_value=lambda name, **_: "also " + name)

    another_name = PRESENT('another_name')

    token = TokenWithOptionalValue(name="a name")
    assert token.another_name is None

    token = TokenWithOptionalValue(another_name, name="a name")
    assert token.another_name == "also a name"


def test_prefix():

    class TokenWithPrefix(Token):

        name = TokenAttribute()
        prefix = TokenAttribute()

    class TokensWithPrefix(TokenContainer):

        class Meta:
            prefix = "test"

        foo = TokenWithPrefix()

    assert str(TokensWithPrefix.foo) == "test.foo"
    assert repr(TokensWithPrefix.foo) == "<TokenWithPrefix: test.foo>"


def test_prefix_error():
    class TokenWithoutPrefix(Token):
        name = TokenAttribute()

    with pytest.raises(AssertionError) as e:
        class TokensWithoutPrefix(TokenContainer):
            class Meta:
                prefix = "test"

            foo = TokenWithoutPrefix()

    assert 'You must define a token attribute called "prefix"' == str(e.value)


def test_prefix_inheritance():

    class AToken(Token):
        name = TokenAttribute()
        prefix = TokenAttribute()

    class FooTokens(TokenContainer):

        class Meta:
            prefix = 'f'

        foo = AToken()

    class BarTokens(TokenContainer):

        class Meta:
            prefix = 'b'

        bar = AToken()

    assert 'f.foo' == str(FooTokens.foo)
    assert 'b.bar' == str(BarTokens.bar)

    class CommonTokens(FooTokens, BarTokens):
        pass

    assert 'f.foo' == str(CommonTokens.foo)
    assert 'b.bar' == str(CommonTokens.bar)


def test_to_csv_no_spec():

    class TestTokensWithoutDocumentation(MyTokens):
        class Meta:
            pass

    assert TestTokensWithoutDocumentation.to_csv() == """\
name\r
foo\r
bar\r
"""


def test_to_csv_sorting():
    class TestTokensWithSortOrder(MyTokens):
        class Meta:
            documentation_columns = ['name', 'stuff']
            documentation_sort_key = lambda token: token.stuff[::-1]  # Sort on last character

    assert TestTokensWithSortOrder.to_csv() == """\
name,stuff\r
bar,World\r
foo,Hello\r
"""


def test_to_csv():
    class TestTokensWithDocumentation(MyTokens):
        baz = Token(stuff=None)

        class Meta:
            documentation_columns = ['name', 'stuff']

    assert TestTokensWithDocumentation.to_csv() == """\
name,stuff\r
foo,Hello\r
bar,World\r
baz,\r
"""


def test_to_rst():
    class TestTokensWithDocumentation(MyTokens):

        class Meta:
            documentation_columns = ['name', 'stuff']
            documentation_sort_key = lambda token: token.name

    assert TestTokensWithDocumentation.to_rst() == """\
+------+-------+
| name | stuff |
+======+=======+
| bar  | World |
+------+-------+
| foo  | Hello |
+------+-------+"""


def test_to_confluence():
    class TestTokensWithDocumentation(MyTokens):

        class Meta:
            documentation_columns = ['name', 'stuff']

    assert TestTokensWithDocumentation.to_confluence() == """\
||name||stuff||
|foo|Hello|
|bar|World|
"""
