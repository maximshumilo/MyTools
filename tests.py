import unittest


class TestFlaskCommonMarshmallow(unittest.TestCase):
    def test_convert_to_instance(self):
        a = 1
        self.assertEqual(a, 2)


if __name__ == '__main__':
    unittest.main()
