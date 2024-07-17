import unittest

from seuranta import SeurantaDb

class TestSeurantaDbInit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seurdb = SeurantaDb(":memory:")


    def test_tables_exist(self):
        expect = ['person', 'device']
        self.assertEqual(expect, self.seurdb.tables)


class TestSeurantaDbPeople(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seurdb = SeurantaDb(":memory:")


    def test_addpeople(self):
        self.assertListEqual([], self.seurdb.people)
        self.seurdb.addpeople(['45spoons'])
        self.assertListEqual(['45spoons'], self.seurdb.people)


if __name__ == "__main__":
    unittest.main(verbosity=2)