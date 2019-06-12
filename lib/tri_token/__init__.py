from collections import Hashable, OrderedDict
import csv
import sys
from io import BytesIO

from tri_declarative import creation_ordered, declarative, with_meta
from tri_struct import FrozenStruct, Struct, merged

from io import StringIO  # pragma: no cover


__version__ = '3.0.0'  # pragma: no mutate
assert(sys.version_info >= (3, 0))


class PRESENT(object):
    def __init__(self, attribute_name):
        self.attribute_name = attribute_name


MISSING = object()


@creation_ordered
class TokenAttribute(FrozenStruct):
    def __init__(self, **kwargs):
        kwargs.setdefault('description')
        kwargs.setdefault('default', MISSING)
        kwargs.setdefault('value')
        kwargs.setdefault('optional_value')
        super(TokenAttribute, self).__init__(**kwargs)


@creation_ordered
@declarative(TokenAttribute, add_init_kwargs=False)
class Token(FrozenStruct):

    name = TokenAttribute()

    @classmethod
    def attribute_names(cls):
        return tuple(cls.get_declared().keys())

    def __init__(self, *args, **kwargs):

        for arg in args:
            if isinstance(arg, PRESENT):
                assert arg.attribute_name not in kwargs, "%s used with PRESENT and kwarg at the same time" % arg.attribute_name
                kwargs[arg.attribute_name] = PRESENT
            else:  # pragma: no cover
                assert False, "Unexpected position argument: %s" % (arg, )  # pragma: no mutate

        token_attributes = self.get_declared()

        if type(self) is Token:
            # Make a fake definition if user did not bother to make a proper sub-class
            token_attributes_from_kwargs = [(name, TokenAttribute()) for name in kwargs]
            token_attributes = OrderedDict(list(token_attributes.items()) + token_attributes_from_kwargs)

        new_kwargs = Struct()
        for name, token_attribute in token_attributes.items():
            default = token_attribute.default
            if token_attribute.default is MISSING:
                default = None
            new_kwargs[name] = kwargs.pop(name, default)

        object.__setattr__(self, '__override__', kwargs.pop('__override__', False))

        assert len(kwargs) == 0, "Unexpected constructor arguments: %s" % (kwargs, )  # pragma: no mutate

        if new_kwargs.name is not None:
            for name, token_attribute in token_attributes.items():

                if token_attribute.value is not None:
                    existing_value = new_kwargs[name]
                    if existing_value is None:
                        new_kwargs[name] = token_attribute.value(**new_kwargs)

                if token_attribute.optional_value is not None:
                    existing_value = new_kwargs[name]
                    if existing_value is PRESENT or isinstance(existing_value, PRESENT):
                        new_value = token_attribute.optional_value(**new_kwargs)
                        # Only update if we got a value (otherwise retain the PRESENT marker)
                        if new_value is not None:
                            new_kwargs[name] = new_value

        for name, value in new_kwargs.items():
            if not isinstance(value, Hashable):
                raise ValueError("Attribute {} has unhashable value: {}".format(name, value))

        super(Token, self).__init__(**new_kwargs)

    def __repr__(self):
        return "<%s: %s%s>" % (type(self).__name__, (self.prefix + '.') if getattr(self, 'prefix', None) else '', self.name if self.name else '(unnamed)')

    def __unicode__(self):
        return u"%s%s" % ((self.prefix + '.') if getattr(self, 'prefix', None) else '', self.name if self.name else '(unnamed)')  # pragma: no mutate

    def __str__(self):
        return "%s%s" % ((self.prefix + '.') if getattr(self, 'prefix', None) else '', self.name if self.name else '(unnamed)')

    def duplicate(self, **overrides):
        result = merged(self, overrides)
        # __setattr__ since FrozenStruct is read-only
        object.__setattr__(result, '_index', self._index)
        return result

    def __copy__(self):
        return self

    def __deepcopy__(self, _):
        return self


@declarative(Token)
@with_meta
class ContainerBase(object):
    pass


class TokenContainerMeta(ContainerBase.__class__):

    def __init__(cls, name, bases, dct):

        super(TokenContainerMeta, cls).__init__(name, bases, dct)

        prefix = getattr(cls.get_meta(), 'prefix', cls.__name__)

        all_tokens = []
        for token_name, token in cls.get_declared().items():

            if (
                token_name in cls.__dict__ and
                any(token_name in base.get_declared() for base in bases) and
                not token.__override__
            ):
                raise TypeError('Illegal enum value override. Use __override__=True parameter to override.')

            overrides = Struct()

            if token.name is None:
                overrides.name = token_name
            else:
                assert token.name == token_name

            if prefix:
                assert 'prefix' in token, 'You must define a token attribute called "prefix"'
                if token.prefix is None:
                    overrides.prefix = prefix

            new_token = token.duplicate(**overrides)

            if token != new_token:
                setattr(cls, token_name, new_token)
                token = new_token

            all_tokens.append(token)

        cls.tokens = OrderedDict((t.name, t) for t in all_tokens)

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
        input = StringIO(cls.to_csv(columns, sort_key))
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
