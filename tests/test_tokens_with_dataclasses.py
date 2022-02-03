import dataclasses

import pytest

from tests.test_tokens import MyToken, MyTokens


@dataclasses.dataclass
class MyDataClass:
    thing: MyToken


def test_a_token_used_in_a_dataclass_passed_to_asdict_raises_a_clear_exception_message():
    my_data = MyDataClass(thing=MyTokens.bar)
    with pytest.raises(TypeError) as error:
        dataclasses.asdict(my_data)
    assert "Instance of tri.token MyToken can not be constructed from a generator." in str(error.value)
    assert "If you are using dataclass.asdict you will need to implement an alternative that is token aware." \
        in str(error.value)
