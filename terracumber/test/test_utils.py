import unittest
import utils

class TestUtils(unittest.TestCase):
    def test_merge_two_dicts(self):
        dict_x = { 'a': 1, 'b': 2 }
        dict_y = { 'c': 3, 'd': 4 }
        self.assertDictEqual(utils.merge_two_dicts(dict_x, dict_y), { 'a': 1, 'b': 2, 'c': 3, 'd': 4 })

        dict_x = { 'a': 1, 'b': 2 }
        dict_y = { }
        self.assertDictEqual(utils.merge_two_dicts(dict_x, dict_y), { 'a': 1, 'b': 2 })

        dict_x = { }
        dict_y = { }
        self.assertDictEqual(utils.merge_two_dicts(dict_x, dict_y), { })

    def test_overwrite_dict(self):
        dict_x = { 'a': 1, 'b': 2 }
        dict_y = { 'b': 22, 'c': 3 }
        dict_z = utils.overwrite_dict(dict_x, dict_y)
        self.assertDictEqual(dict_z, { 'a': 1, 'b': 22 })
        self.assertDictEqual(dict_x, { 'a': 1, 'b': 2 })
        self.assertDictEqual(dict_y, { 'b': 22, 'c': 3 })

        dict_x = { 'a': 1, 'b': 2 }
        dict_y = { }
        self.assertDictEqual(utils.overwrite_dict(dict_x, dict_y), { 'a': 1, 'b': 2 })

        dict_x = { }
        dict_y = { 'a': 1, 'b': 2 }
        self.assertDictEqual(utils.overwrite_dict(dict_x, dict_y), { })

        dict_x = { }
        dict_y = { }
        self.assertDictEqual(utils.overwrite_dict(dict_x, dict_y), { })

if __name__ == '__main__':
    unittest.main()
