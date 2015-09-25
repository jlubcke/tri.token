from copy import copy, deepcopy
import pickle

import pytest
from tri.cache.memoize import memoize

from tri.token import TokenContainer, Token, TokenAttribute, PRESENT


class TestToken(Token):

    name = TokenAttribute()
    stuff = TokenAttribute()


class TestTokens(TokenContainer):

    foo = TestToken(stuff='Hello')
    bar = TestToken(stuff='World')


def test_in():
    assert TestTokens.foo in TestTokens

    class OtherTokens(TestTokens):
        boink = TestToken()

    assert TestTokens.foo in OtherTokens


def test_immutable():
    d = {TestTokens.foo: 17}
    assert d[TestTokens.foo] is 17

    with pytest.raises(AttributeError):
        TestTokens.foo.stuff = "Not likely"


def test_immutable_attribute_values():

    with pytest.raises(ValueError) as exception_info:
        TestToken(stuff=[])

    assert exception_info.value.message == "Attribute stuff has unhashable value: []"


def test_copy():
    assert copy(TestTokens.foo) is TestTokens.foo
    assert copy([TestTokens.foo]) == [TestTokens.foo]


def test_deepcopy():
    assert deepcopy(TestTokens.foo) is TestTokens.foo
    assert deepcopy([TestTokens.foo]) == [TestTokens.foo]


def test_pickle():
    s = pickle.dumps(TestTokens.foo, pickle.HIGHEST_PROTOCOL)
    assert pickle.loads(s) == TestTokens.foo


def test_modification():
    existing_token = TestTokens.foo
    attributes = dict(existing_token)
    attributes.update(stuff="Other stuff")
    new_token = type(existing_token)(**attributes)
    assert new_token.stuff == "Other stuff"
    assert isinstance(new_token, TestToken)


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
        first = TestToken()
        second = TestToken()
        third = TestToken()
        fourth = TestToken()
        fifth = TestToken()

    assert list(OrderedTokens) == list(sorted(set(OrderedTokens)))


def test_names():
    assert [token.name for token in TestTokens] == ['foo', 'bar']


def test_unicode():
    assert unicode(TestToken()) == u'(unnamed)'
    assert unicode(TestTokens.foo) == u'foo'


def test_str():
    assert str(TestToken()) == "(unnamed)"
    assert str(TestTokens.foo) == "foo"
    assert str(list(TestTokens)) == "[<TestToken: foo>, <TestToken: bar>]"


def test_type_str():
    assert "<class 'tri.token.test.unittest.test_tokens.TestToken'>" == str(TestToken)
    assert "<class 'tri.token.test.unittest.test_tokens.TestToken'>" == str(type(TestTokens.foo))
    assert "<class 'tri.token.test.unittest.test_tokens.TestTokens'>" == str(TestTokens)


def test_repr():
    assert repr(TestToken()) == "<TestToken: (unnamed)>"
    assert repr(TestTokens.foo) == "<TestToken: foo>"
    assert repr(list(TestTokens)) == "[<TestToken: foo>, <TestToken: bar>]"


def test_other_field():
    assert [token.stuff for token in TestTokens] == ['Hello', 'World']


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

    class MoreTokens(TestTokens):
        boink = TestToken(stuff='Other Stuff')

    assert list(MoreTokens) == [TestTokens.foo, TestTokens.bar, MoreTokens.boink]
    assert MoreTokens.foo is TestTokens.foo


def test_container_inheritance_override():

    class MoreTokens(TestTokens):
        foo = TestToken(stuff='Override')

    assert len(MoreTokens) == 2
    assert MoreTokens.foo != TestTokens.foo
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


def test_extra_stuff():

    @memoize
    def alpha_ordered():
        return sorted(ExtendedTokens, key=lambda token: token.name)

    class ExtendedTokens(TestTokens):

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


def test_to_csv_no_spec():

    class TestTokensWithoutDocumentation(TestTokens):
        class Meta:
            pass

    assert TestTokensWithoutDocumentation.to_csv() == """\
name\r
foo\r
bar\r
"""


def test_to_csv():
    class TestTokensWithDocumentation(TestTokens):
        class Meta:
            documentation_columns = ['name', 'stuff']

    assert TestTokensWithDocumentation.to_csv() == """\
name,stuff\r
foo,Hello\r
bar,World\r
"""


def test_to_rst():
    class TestTokensWithDocumentation(TestTokens):

        class Meta:
            documentation_columns = ['name', 'stuff']

    assert TestTokensWithDocumentation.to_rst() == """\
+------+-------+
| name | stuff |
+======+=======+
| bar  | World |
+------+-------+
| foo  | Hello |
+------+-------+"""
