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


if __name__ == '__main__':
    unittest.main()
