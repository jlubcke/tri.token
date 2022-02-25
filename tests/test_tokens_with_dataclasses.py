import dataclasses

from tests.test_tokens import (
    MyToken,
    MyTokens,
)


@dataclasses.dataclass
class MyDataClass:
    thing: MyToken


def test_a_token_used_in_a_dataclass_passed_to_asdict_works():
    my_data = MyDataClass(thing=MyTokens.bar)
    assert dataclasses.asdict(my_data) == {'thing': MyTokens.bar}
