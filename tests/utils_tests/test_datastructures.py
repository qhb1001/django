"""
Tests for stuff in django.utils.datastructures.
"""

import copy

from django.test import SimpleTestCase
from django.utils.datastructures import (
    CaseInsensitiveMapping, DictWrapper, ImmutableList, MultiValueDict,
    MultiValueDictKeyError, OrderedSet,
)


class OrderedSetTests(SimpleTestCase):

    def test_bool(self):
        # Refs #23664
        s = OrderedSet()
        self.assertFalse(s)
        s.add(1)
        self.assertTrue(s)

    def test_len(self):
        s = OrderedSet()
        self.assertEqual(len(s), 0)
        s.add(1)
        s.add(2)
        s.add(2)
        self.assertEqual(len(s), 2)

    def test_del(self):
        # initialization
        s = OrderedSet()
        for i in range(3):
            s.add(i)

        # try to remove the existing key
        s.remove(1)
        self.assertEqual(s.dict, {0: None, 2: None})

        # try to remove the non-existing value
        s.discard(5)
        self.assertEqual(s.dict, {0: None, 2: None})

    def test_contains(self):
        # initialization
        s = OrderedSet()
        for i in range(3):
            s.add(i)

        # test
        for i in range(5):
            if i < 3:
                self.assertEqual(i in s, True)
            else:
                self.assertEqual(i in s, False)


class MultiValueDictTests(SimpleTestCase):

    def test_multivaluedict(self):
        d = MultiValueDict({'name': ['Adrian', 'Simon'], 'position': ['Developer']})
        self.assertEqual(d['name'], 'Simon')
        self.assertEqual(d.get('name'), 'Simon')
        self.assertEqual(d.getlist('name'), ['Adrian', 'Simon'])
        self.assertEqual(
            sorted(d.items()),
            [('name', 'Simon'), ('position', 'Developer')]
        )
        self.assertEqual(
            sorted(d.lists()),
            [('name', ['Adrian', 'Simon']), ('position', ['Developer'])]
        )
        with self.assertRaisesMessage(MultiValueDictKeyError, "'lastname'"):
            d.__getitem__('lastname')
        self.assertIsNone(d.get('lastname'))
        self.assertEqual(d.get('lastname', 'nonexistent'), 'nonexistent')
        self.assertEqual(d.getlist('lastname'), [])
        self.assertEqual(d.getlist('doesnotexist', ['Adrian', 'Simon']), ['Adrian', 'Simon'])
        d.setlist('lastname', ['Holovaty', 'Willison'])
        self.assertEqual(d.getlist('lastname'), ['Holovaty', 'Willison'])
        self.assertEqual(sorted(d.values()), ['Developer', 'Simon', 'Willison'])

    def test_appendlist(self):
        d = MultiValueDict()
        d.appendlist('name', 'Adrian')
        d.appendlist('name', 'Simon')
        self.assertEqual(d.getlist('name'), ['Adrian', 'Simon'])

    def test_copy(self):
        for copy_func in [copy.copy, lambda d: d.copy()]:
            d1 = MultiValueDict({
                "developers": ["Carl", "Fred"]
            })
            self.assertEqual(d1["developers"], "Fred")
            d2 = copy_func(d1)
            d2.update({"developers": "Groucho"})
            self.assertEqual(d2["developers"], "Groucho")
            self.assertEqual(d1["developers"], "Fred")

            d1 = MultiValueDict({
                "key": [[]]
            })
            self.assertEqual(d1["key"], [])
            d2 = copy_func(d1)
            d2["key"].append("Penguin")
            self.assertEqual(d1["key"], ["Penguin"])
            self.assertEqual(d2["key"], ["Penguin"])

    def test_deepcopy(self):
        # initialization
        dic = {'a': [[1, 2], [3, 4]], 'b': [[5, 6], 'c']}
        d1 = MultiValueDict(dic)

        d2 = copy.deepcopy(d1)
        d1['a'][0] = [5, 6]
        self.assertEqual(d1['a'], [[5, 6], 4])
        self.assertEqual(d2['a'], [3, 4])

    def test_dict_translation(self):
        mvd = MultiValueDict({
            'devs': ['Bob', 'Joe'],
            'pm': ['Rory'],
        })
        d = mvd.dict()
        self.assertEqual(sorted(d), sorted(mvd))
        for key in mvd:
            self.assertEqual(d[key], mvd[key])

        self.assertEqual({}, MultiValueDict().dict())

    def test_getlist_doesnt_mutate(self):
        x = MultiValueDict({'a': ['1', '2'], 'b': ['3']})
        values = x.getlist('a')
        values += x.getlist('b')
        self.assertEqual(x.getlist('a'), ['1', '2'])

    def test_internal_getlist_does_mutate(self):
        x = MultiValueDict({'a': ['1', '2'], 'b': ['3']})
        values = x._getlist('a')
        values += x._getlist('b')
        self.assertEqual(x._getlist('a'), ['1', '2', '3'])

    def test_getlist_default(self):
        x = MultiValueDict({'a': [1]})
        MISSING = object()
        values = x.getlist('b', default=MISSING)
        self.assertIs(values, MISSING)

    def test_getlist_none_empty_values(self):
        x = MultiValueDict({'a': None, 'b': []})
        self.assertIsNone(x.getlist('a'))
        self.assertEqual(x.getlist('b'), [])

    def test_index(self):
        # initialization
        x = MultiValueDict({'a': [1], 'b': []})
        # empty value
        self.assertEqual(x['b'], [])
        # get default value
        self.assertEqual(x.get('b'), None)
        # set item
        x['c'] = ['a', 'b', 'c']
        self.assertEqual(x['c'], ['a', 'b', 'c'])

    def test_setdefault(self):
        d = MultiValueDict({'a': [1]})
        d.setdefault('b')
        d.setdefault('a', [5, 6])
        self.assertEqual(d['b'], None)
        self.assertEqual(d['a'], 1)

    def test_update(self):
        d1 = MultiValueDict({'a': [1], 'b': [2]})
        d2 = MultiValueDict({'c': [3]})
        d2.update(d1)
        d1['c'] = 3
        self.assertEqual(d1, d2)
        d2.update({'d': [4]})
        self.assertEqual(d2['d'], [4])

        # accepts only one parameter
        with self.assertRaisesMessage(TypeError, "update expected at most 1 argument, got 2"):
            d2.update(d1, 1)


class ImmutableListTests(SimpleTestCase):

    def test_sort(self):
        d = ImmutableList(range(10))

        # AttributeError: ImmutableList object is immutable.
        with self.assertRaisesMessage(AttributeError, 'ImmutableList object is immutable.'):
            d.sort()

        self.assertEqual(repr(d), '(0, 1, 2, 3, 4, 5, 6, 7, 8, 9)')

    def test_custom_warning(self):
        d = ImmutableList(range(10), warning="Object is immutable!")

        self.assertEqual(d[1], 1)

        # AttributeError: Object is immutable!
        with self.assertRaisesMessage(AttributeError, 'Object is immutable!'):
            d.__setitem__(1, 'test')


class DictWrapperTests(SimpleTestCase):

    def test_dictwrapper(self):
        def f(x):
            return "*%s" % x
        d = DictWrapper({'a': 'a'}, f, 'xx_')
        self.assertEqual(
            "Normal: %(a)s. Modified: %(xx_a)s" % d,
            'Normal: a. Modified: *a'
        )


class CaseInsensitiveMappingTests(SimpleTestCase):
    def setUp(self):
        self.dict1 = CaseInsensitiveMapping({
            'Accept': 'application/json',
            'content-type': 'text/html',
        })

    def test_create_with_invalid_values(self):
        msg = 'dictionary update sequence element #1 has length 4; 2 is required'
        with self.assertRaisesMessage(ValueError, msg):
            CaseInsensitiveMapping([('Key1', 'Val1'), 'Key2'])

    def test_create_with_invalid_key(self):
        msg = 'Element key 1 invalid, only strings are allowed'
        with self.assertRaisesMessage(ValueError, msg):
            CaseInsensitiveMapping([(1, '2')])

    def test_list(self):
        self.assertEqual(list(self.dict1), ['Accept', 'content-type'])

    def test_dict(self):
        self.assertEqual(dict(self.dict1), {'Accept': 'application/json', 'content-type': 'text/html'})

    def test_repr(self):
        dict1 = CaseInsensitiveMapping({'Accept': 'application/json'})
        dict2 = CaseInsensitiveMapping({'content-type': 'text/html'})
        self.assertEqual(repr(dict1), repr({'Accept': 'application/json'}))
        self.assertEqual(repr(dict2), repr({'content-type': 'text/html'}))

    def test_str(self):
        dict1 = CaseInsensitiveMapping({'Accept': 'application/json'})
        dict2 = CaseInsensitiveMapping({'content-type': 'text/html'})
        self.assertEqual(str(dict1), str({'Accept': 'application/json'}))
        self.assertEqual(str(dict2), str({'content-type': 'text/html'}))

    def test_equal(self):
        self.assertEqual(self.dict1, {'Accept': 'application/json', 'content-type': 'text/html'})
        self.assertNotEqual(self.dict1, {'accept': 'application/jso', 'Content-Type': 'text/html'})
        self.assertNotEqual(self.dict1, 'string')

    def test_items(self):
        other = {'Accept': 'application/json', 'content-type': 'text/html'}
        self.assertEqual(sorted(self.dict1.items()), sorted(other.items()))

    def test_copy(self):
        copy = self.dict1.copy()
        self.assertIs(copy, self.dict1)
        self.assertEqual(copy, self.dict1)

    def test_getitem(self):
        self.assertEqual(self.dict1['Accept'], 'application/json')
        self.assertEqual(self.dict1['accept'], 'application/json')
        self.assertEqual(self.dict1['aCCept'], 'application/json')
        self.assertEqual(self.dict1['content-type'], 'text/html')
        self.assertEqual(self.dict1['Content-Type'], 'text/html')
        self.assertEqual(self.dict1['Content-type'], 'text/html')

    def test_in(self):
        self.assertIn('Accept', self.dict1)
        self.assertIn('accept', self.dict1)
        self.assertIn('aCCept', self.dict1)
        self.assertIn('content-type', self.dict1)
        self.assertIn('Content-Type', self.dict1)

    def test_del(self):
        self.assertIn('Accept', self.dict1)
        msg = "'CaseInsensitiveMapping' object does not support item deletion"
        with self.assertRaisesMessage(TypeError, msg):
            del self.dict1['Accept']
        self.assertIn('Accept', self.dict1)

    def test_set(self):
        self.assertEqual(len(self.dict1), 2)
        msg = "'CaseInsensitiveMapping' object does not support item assignment"
        with self.assertRaisesMessage(TypeError, msg):
            self.dict1['New Key'] = 1
        self.assertEqual(len(self.dict1), 2)
