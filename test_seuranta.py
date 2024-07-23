import unittest

from seuranta import SeurantaDb

class TestSeurantaDb(unittest.TestCase):
    def setUp(self):
        self.seurdb = SeurantaDb(":memory:")


    def test_tables_exist(self):
        expect = ['person', 'device']
        self.assertEqual(expect, self.seurdb.tables)


    def test_add_people(self):
        self.assertListEqual([], self.seurdb.people)
        self.seurdb.add_people(['45spoons'])
        self.assertListEqual(['45spoons'], self.seurdb.people)


    def test_add_people_increment_id(self):
        names = ['45spoons', 'ikaros02']
        self.seurdb.add_people(names)
        id_list = list(self.seurdb.name_to_person_id(name) for name in names)
        self.assertEqual([1, 2], id_list)


if __name__ == "__main__":
    unittest.main(verbosity=2)