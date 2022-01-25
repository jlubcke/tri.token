from typing import TYPE_CHECKING

import pytest
from pydantic import BaseModel, ValidationError

from tri_token import TokenContainer, Token, TokenAttribute


class MyToken(Token):

    name = TokenAttribute()
    stuff = TokenAttribute()


class MyTokens(TokenContainer):
    if TYPE_CHECKING:
        __token_class__ = MyToken

    foo = MyToken(stuff='Hello')
    bar = MyToken(stuff='World')
    baz = MyToken(stuff='')


class MyOtherTokens(TokenContainer):
    if TYPE_CHECKING:
        __token_class__ = MyToken

    foo = MyToken(stuff='Hello')
    bar = MyToken(stuff='World')


class MyModel(BaseModel):
    thing: MyTokens.__token_class__


class AnotherModel(BaseModel):
    thing: MyOtherTokens.__token_class__


def test_strings_are_converted_into_the_appropriate_type():
    assert MyModel(thing="baz").thing == MyTokens.baz


def test_invalid_strings_raise_an_error():
    with pytest.raises(ValidationError):
        MyModel(thing="bob")


def test_invalid_strings_raise_an_error_even_if_the_string_would_be_a_valid_token_in_another_container():
    with pytest.raises(ValidationError):
        AnotherModel(thing="baz")


def test_the_containers_token_property_is_the_type_of_the_tokens():
    assert issubclass(MyTokens.__token_class__, MyToken)


def test_a_useful_schema_is_generated():
    expected = {
        "title": "Thing",
        "pattern": "^foo|bar|baz$",
        "examples": ["foo", "bar", "baz"],
        "type": "string"
    }
    assert MyModel.schema()["properties"]["thing"] == expected
