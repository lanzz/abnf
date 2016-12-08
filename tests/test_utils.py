from unittest import TestCase

import pytest

from abnf.utils import Context, CharRange


class TestContext(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestContext, cls).setUpClass()
        cls.key = 'foo'
        cls.value = 'bar'
        cls.private_key = '_private'
        cls.private_value = '_value'

    def setUp(self):
        super(TestContext, self).setUp()
        self.dict = {self.key: self.value, self.private_key: self.private_value}


class TestContextNew(TestContext):

    def test_empty(self):
        ctx = Context()
        assert type(ctx) == Context
        assert len(ctx) == 0
        assert list(ctx.items()) == []

    def test_kwargs(self):
        ctx = Context(**self.dict)
        assert type(ctx) == Context
        assert len(ctx) == len(self.dict)
        assert sorted(ctx.items()) == sorted(self.dict.items())

    def test_dict(self):
        ctx = Context(self.dict)
        assert type(ctx) == Context
        assert len(ctx) == len(self.dict)
        assert sorted(ctx.items()) == sorted(self.dict.items())


class TestContextInstance(TestContext):

    @classmethod
    def setUpClass(cls):
        super(TestContextInstance, cls).setUpClass()
        cls.newkey = 'newkey'
        cls.newvalue = 'newvalue'

    def setUp(self):
        super(TestContextInstance, self).setUp()
        self.ctx = Context(self.dict)

    def test_repr(self):
        assert repr(self.ctx) == repr(self.dict)

    def test_in(self):
        assert self.key in self.ctx
        assert self.private_key in self.ctx

    def test_not_existing(self):
        assert self.newkey not in self.ctx
        with pytest.raises(KeyError):
            self.ctx[self.newkey]

    def test_getitem(self):
        value = self.ctx[self.key]
        assert value == self.value

    def test_getattr(self):
        value = getattr(self.ctx, self.key)
        assert value == self.value

    def test_setitem(self):
        self.ctx[self.newkey] = self.newvalue
        value = self.ctx[self.newkey]
        assert value == self.newvalue

    def test_setattr(self):
        setattr(self.ctx, self.newkey, self.newvalue)
        value = self.ctx[self.newkey]
        assert value == self.newvalue

    def test_delitem(self):
        del self.ctx[self.key]
        assert self.key not in self.ctx

    def test_delattr(self):
        delattr(self.ctx, self.key)
        assert self.key not in self.ctx

    def test_clean(self):
        self.ctx.clean()
        assert self.private_key not in self.ctx


class TestCharRange(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCharRange, cls).setUpClass()
        cls.start = 'a'
        cls.end = 'z'
        cls.str = 'abcdefghijklmnopqrstuvwxyz'


class TestCharRangeNew(TestCharRange):

    def test_empty(self):
        with pytest.raises(TypeError):
            CharRange()

    def test_empty_str(self):
        r = CharRange('')
        assert len(r) == 0

    def test_str(self):
        r = CharRange(self.str)
        assert set(r) == set(self.str)

    def test_char_range(self):
        r = CharRange(self.start, self.end)
        assert set(r) == set(self.str)

    def test_int_range(self):
        r = CharRange(ord(self.start), ord(self.end))
        assert set(r) == set(self.str)


class TestCharRangeInstance(TestCharRange):

    def setUp(self):
        self.cr = CharRange(self.str)

    def test_str(self):
        assert str(self.cr) == self.str

    def test_repr(self):
        assert repr(self.cr) == '<CharRange {chars!r}>'.format(chars=self.str)
