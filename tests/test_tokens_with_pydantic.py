import pydantic
import pytest
from pydantic import (
    BaseModel,
    ValidationError,
)

from tri_token import (
    Token,
    TokenAttribute,
    TokenContainer,
)


class MyToken(Token):
    stuff = TokenAttribute()


class MyTokens(TokenContainer):
    foo = MyToken(stuff='Hello')
    bar = MyToken(stuff='World')
    baz = MyToken(stuff='')


@pydantic.dataclasses.dataclass
class MyModelDirectly:
    thing: MyToken


def test_token_class_something_something():
    assert MyModelDirectly(thing=MyTokens.foo).thing == MyTokens.foo


def test_token_class_rejects_invalid_values():
    with pytest.raises(ValidationError) as e:
        MyModelDirectly(thing=5)
    assert "Given 'int' expected either an instance of 'MyToken' or 'str'" in str(e.value)


def test_token_class_can_coerce_strings():
    assert MyModelDirectly(thing="foo").thing == MyTokens.foo


def test_token_class_coersion_conflict():
    class TheToken(Token):
        pass

    class OneTokenContainer(TokenContainer):
        foo = TheToken()

    class AnotherTokenContainer(TokenContainer):
        foo = TheToken()

    with pytest.raises(TypeError) as e:
        @pydantic.dataclasses.dataclass
        class MyModelDirectly:
            thing: TheToken

    assert str(e.value) == 'Non-unique names: foo'


def test_token_class_cant_coerce_badness():
    with pytest.raises(ValidationError) as e:
        MyModelDirectly(thing="badness")
    assert 'badness is not a valid value for MyToken' in str(e.value)


def test_a_useful_schema_is_generated():
    expected = {
        "title": "Thing",
        "pattern": "^foo|bar|baz$",
        "examples": ["foo", "bar", "baz"],
        "type": "string"
    }

    class SomeModel(BaseModel):
        thing: MyToken

    assert SomeModel.schema()['properties']['thing'] == expected


def test_accidentally_using_the_container_type_directly_produces_a_helpful_error():
    with pytest.raises(Exception) as error:
        class MyBrokenModel(BaseModel):
            thing: MyTokens
        MyBrokenModel(thing="baz")
    expected_error = 'MyTokens cannot be used as a type in pydantic. Use the class of the instances instead'
    assert str(error.value) == expected_error
