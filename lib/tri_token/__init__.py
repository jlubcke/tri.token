import csv
from collections.abc import Hashable
from dataclasses import dataclass
from io import (
    BytesIO,
    StringIO,  # pragma: no cover
)
from typing import Any

from tri_declarative import (
    declarative,
    with_meta,
)

__version__ = '4.0.0'


class PRESENT(object):
    def __init__(self, attribute_name):
        self.attribute_name = attribute_name


MISSING = object()
HASH_KEY_ATTRIBUTE = '_hash'


@dataclass(frozen=True)
class TokenAttribute:
    description: str = None
    value: Any = None
    optional_value: Any = None
    default: Any = MISSING


@declarative(TokenAttribute, add_init_kwargs=False)
class Token:
    name = TokenAttribute()

    @classmethod
    def attribute_names(cls):
        return tuple(cls.get_declared().keys())

    def __init__(self, *args, **kwargs):
        for arg in args:
            if isinstance(arg, PRESENT):
                assert arg.attribute_name not in kwargs, f"{arg.attribute_name} used with PRESENT and kwarg at the same time"
                kwargs[arg.attribute_name] = PRESENT
            else:  # pragma: no cover
                assert False, f"Unexpected position argument: {arg}"  # pragma: no mutate

        token_attributes = self.get_declared()

        if type(self) is Token:
            # Make a fake definition if user did not bother to make a proper sub-class
            token_attributes_from_kwargs = [(name, TokenAttribute()) for name in kwargs]
            token_attributes = dict(list(token_attributes.items()) + token_attributes_from_kwargs)

        object.__setattr__(self, '_token_attributes', token_attributes)

        attribute_values = dict()
        for name, token_attribute in token_attributes.items():
            default = token_attribute.default
            if token_attribute.default is MISSING:
                default = None
            attribute_values[name] = kwargs.pop(name, default)

        object.__setattr__(self, '__override__', kwargs.pop('__override__', False))

        assert len(kwargs) == 0, f"Unexpected constructor arguments: {kwargs}"  # pragma: no mutate

        for name, value in attribute_values.items():
            if not isinstance(value, Hashable):
                raise ValueError(f"Attribute {name} has unhashable value: {value}")

            object.__setattr__(self, name, value)

        self._set_derived_attributes()

    def _set_derived_attributes(self):
        if self.name is not None:
            for name, token_attribute in self._token_attributes.items():
                if token_attribute.value is not None:
                    existing_value = getattr(self, name, None)
                    if existing_value is None:
                        kwargs = {k: getattr(self, k, None) for k in self._token_attributes}
                        new_value = token_attribute.value(**kwargs)
                        object.__setattr__(self, name, new_value)

                if token_attribute.optional_value is not None:
                    existing_value = getattr(self, name, None)
                    if existing_value is PRESENT or isinstance(existing_value, PRESENT):
                        kwargs = {k: getattr(self, k, None) for k in self._token_attributes}
                        new_value = token_attribute.optional_value(**kwargs)
                        # Only update if we got a value (otherwise retain the PRESENT marker)
                        if new_value is not None:
                            object.__setattr__(self, name, new_value)

    def __setattr__(self, k, v):
        raise TypeError(f"'{type(self).__name__}' object attributes are read-only")

    def __delattr__(self, *_, **__):
        raise TypeError(f"'{type(self).__name__}' object attributes are read-only")

    def __lt__(self, other):
        if not type(self) is type(other):
            return NotImplemented
        return self._index < other._index

    def __gt__(self, other):
        if not type(self) is type(other):
            return NotImplemented
        return self._index > other._index

    def __le__(self, other):
        if not type(self) is type(other):
            return NotImplemented
        return self._index <= other._index

    def __ge__(self, other):
        if not type(self) is type(other):
            return NotImplemented
        return self._index >= other._index

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        if self.name != other.name:
            return False
        try:
            return self._container == other._container
        except AttributeError:
            return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        try:
            _hash = object.__getattribute__(self, HASH_KEY_ATTRIBUTE)
        except AttributeError:
            _hash = hash(tuple(
                (k, getattr(self, k))
                for k in sorted(self._token_attributes)
            ))
            object.__setattr__(self, HASH_KEY_ATTRIBUTE, _hash)
        return _hash

    def __repr__(self):
        return '<{}: {}{}>'.format(
            type(self).__name__,
            (self.prefix + '.') if getattr(self, 'prefix', None) else '',
            self.name if self.name else '(unnamed)',
        )

    def __str__(self):
        return '{}{}'.format(
            (self.prefix + '.') if getattr(self, 'prefix', None) else '',
            self.name if self.name else '(unnamed)',
        )

    def __copy__(self):
        return self

    def __deepcopy__(self, _):
        return self

    def __getstate__(self):
        return (
            {k: getattr(self, k) for k in self._token_attributes},
            getattr(self, '_container', None),
            getattr(self, '_index', None),
        )

    def __setstate__(self, state):
        d, _container, _index = state
        for k, v in d.items():
            object.__setattr__(self, k, v)
        object.__setattr__(self, '_token_attributes', {k: TokenAttribute() for k in d})

        if _index is not None:
            object.__setattr__(self, '_index', _index)
        if _container is not None:
            object.__setattr__(self, '_container', _container)

    @classmethod
    def __get_validators__(cls):
        """
        Interface method for using a Token as part of a pydantic model or dataclass
        """
        found_names = set()
        for container in cls._container_classes:
            new_names = set(token.name for token in container)
            overlap = new_names & found_names
            if bool(overlap):
                raise TypeError(f'Non-unique names: {", ".join(overlap)}')
            found_names |= new_names

        yield cls._validate

    @classmethod
    def _validate(cls, value):
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            for container in cls._container_classes:
                token = container.get(value)
                if token is not None:
                    return token
            raise ValueError(f"{value} is not a valid value for {cls.__name__}")
        raise ValueError(f"Given '{type(value).__name__}' expected either an instance of '{cls.__name__}' or 'str'")

    @classmethod
    def __modify_schema__(cls, field_schema):
        """
        Interface method for using a Token as part of a pydantic model or dataclass
        """
        token_names = [token.name for c in cls._container_classes for token in c]
        field_schema.update(
            pattern=f"^{'|'.join(token_names)}$",
            examples=token_names,
            type="string",
        )

    @classmethod
    def _register_container(cls, container):
        _container_classes = cls.__dict__.get('_container_classes')

        if _container_classes is None:
            _container_classes = set()
            cls._container_classes = _container_classes

        _container_classes.add(container)


@declarative(Token)
@with_meta
class ContainerBase:
    pass


_next_index = 0


class TokenContainerMeta(ContainerBase.__class__):

    def __init__(cls, name, bases, dct):

        super(TokenContainerMeta, cls).__init__(name, bases, dct)

        prefix = getattr(cls.get_meta(), 'prefix', cls.__name__)

        all_tokens = {}
        for token_name, token in cls.get_declared().items():

            if (
                token_name in cls.__dict__ and
                any(token_name in base.get_declared() for base in bases) and
                not token.__override__
            ):
                raise TypeError('Illegal enum value override. Use __override__=True parameter to override.')

            if token.name is None:
                object.__setattr__(token, 'name', token_name)
            else:
                assert token.name == token_name

            if prefix:
                assert 'prefix' in token.attribute_names(), 'You must define a token attribute called "prefix"'
                if token.prefix is None:
                    object.__setattr__(token, 'prefix', prefix)

            if not hasattr(token, '_index'):
                global _next_index
                object.__setattr__(token, '_index', _next_index)
                _next_index += 1

            if not hasattr(token, '_container'):
                object.__setattr__(token, '_container', f"{cls.__module__}.{cls.__name__}")

            token._set_derived_attributes()

            if hasattr(token, HASH_KEY_ATTRIBUTE):
                object.__delattr__(token, HASH_KEY_ATTRIBUTE)

            all_tokens[token.name] = token

        cls.tokens = all_tokens

        for token in all_tokens.values():
            token._register_container(cls)

        cls.set_declared(cls.tokens)

    def __iter__(cls):
        return iter(cls.tokens.values())

    def __contains__(cls, item):
        return item in cls.tokens.values()

    def __len__(cls):
        return len(cls.tokens.values())

    def __getitem__(cls, key):
        return cls.tokens[key]


class TokenContainer(ContainerBase, metaclass=TokenContainerMeta):
    class Meta:
        prefix = ''
        documentation_columns = ['name']
        documentation_sort_key = None

    @classmethod  # pragma: no mutate
    def __iter__(cls):  # pragma: no cover
        # Done in the metaclass, only here as a comfort blanket for PyCharm
        raise Exception("Not implemented here")  # pragma: no mutate

    @classmethod  # pragma: no mutate
    def __len__(cls):  # pragma: no cover
        # Done in the metaclass, only here as a comfort blanket for PyCharm
        raise Exception("Not implemented here")  # pragma: no mutate

    @classmethod
    def __get_validators__(cls):
        """
        Interface method for pydantic
        """
        raise Exception(
            f"{cls.__name__} cannot be used as a type in pydantic. Use the class of the instances instead"
        )

    @classmethod
    def get(cls, key, default=None):
        try:
            return cls[key]
        except KeyError:
            return default

    @classmethod
    def in_documentation_order(cls, sort_key=None):
        tokens = list(cls)
        if sort_key is None:
            sort_key = cls.get_meta().documentation_sort_key
        if sort_key is not None:
            tokens.sort(key=sort_key)
        return tokens

    @classmethod
    def to_csv(cls, columns=None, sort_key=None):
        out = StringIO()
        w = csv.writer(out)
        if columns is None:
            columns = cls.get_meta().documentation_columns
        w.writerow(columns)
        for token in cls.in_documentation_order(sort_key):
            w.writerow([(getattr(token, a) or '') for a in columns])
        return out.getvalue()

    @classmethod
    def to_confluence(cls, columns=None, sort_key=None):
        out = StringIO()
        if columns is None:
            columns = cls.get_meta().documentation_columns
        out.write('||' + '||'.join(columns) + '||\n')
        for token in cls.in_documentation_order(sort_key):
            out.write('|' + '|'.join((getattr(token, a) or ' ') for a in columns) + '|\n')
        return out.getvalue()

    @classmethod
    def to_rst(cls, columns=None, sort_key=None):
        input = StringIO(cls.to_csv(columns, sort_key).replace('\\', '\\\\').replace('`', '\\`').replace('*', '\\*'))
        from prettytable import from_csv
        table = from_csv(input)
        lines = table.get_string(hrules=True).splitlines()

        # Special separator between header and rows in RST
        lines[2] = lines[2].replace('-', '=')
        return '\n'.join(lines)

    @classmethod
    def to_excel(cls, columns=None, sort_key=None):
        from xlwt import Workbook
        wb = Workbook(encoding="utf8")
        sheet = wb.add_sheet('Attributes')

        if columns is None:
            columns = cls.get_meta().documentation_columns

        for i, heading in enumerate(columns):
            sheet.write(0, i, heading)

        for row, field in enumerate(cls.in_documentation_order(sort_key)):
            for col, heading in enumerate(columns):
                value = getattr(field, heading)
                if value:
                    sheet.write(row + 1, col, value)

        result = BytesIO()
        wb.save(result)
        return result.getvalue()


def generate_documentation(token_container):  # pragma: no cover
    import argparse
    parser = argparse.ArgumentParser(description='Generate documentation of fields.')  # pragma: no mutate
    group = parser.add_mutually_exclusive_group(required=True)  # pragma: no mutate
    group.add_argument('-c', '--csv', action='store_true', help='Generate a csv description of all fields')  # pragma: no mutate
    group.add_argument('-w', '--wiki', action='store_true', help='Generate a confluence wiki markup description of all fields')  # pragma: no mutate
    group.add_argument('-r', '--rst', action='store_true', help='Generate a RST table of all fields')  # pragma: no mutate
    group.add_argument('-e', '--excel', action='store_true', help='Generate a excel table of all fields')  # pragma: no mutate
    args = parser.parse_args()
    if args.csv:
        print(token_container.to_csv())
    if args.wiki:
        print(token_container.to_confluence())
    if args.rst:
        print(token_container.to_rst())
    if args.excel:
        print(token_container.to_excel())
