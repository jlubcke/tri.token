import pytest
from pydantic import BaseModel, ValidationError

from tri_token import TokenContainer, Token, TokenAttribute


class MyToken(Token):

    name = TokenAttribute()
    stuff = TokenAttribute()


class MyTokens(TokenContainer):

    foo = MyToken(stuff='Hello')
    bar = MyToken(stuff='World')
    baz = MyToken(stuff='')


class MyModel(BaseModel):
    thing: MyTokens


def test_strings_are_converted_into_the_appropriate_type():
    assert MyModel(thing="baz").thing == MyTokens.baz


def test_invalid_strings_raise_an_error():
    with pytest.raises(ValidationError):
        MyModel(thing="bob")


def test_a_useful_schema_is_generated():
    expected = {
        "title": "Thing",
        "pattern": "^foo|bar|baz$",
        "examples": ["foo", "bar", "baz"]
    }
    assert MyModel.schema()["properties"]["thing"] == expected
