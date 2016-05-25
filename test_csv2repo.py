import unittest
from csv2repo import CSVData, Field, Item, Namespace
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef
from rdflib.namespace import DC, FOAF

g = Graph()

class TestNS(unittest.TestCase):
    def test_ns(self):
        ns = Namespace("something")
        self.assertEqual(ns.name, None)
        ns = Namespace("foaf")
        self.assertEqual(ns.name, "FOAF")
        self.assertEqual(ns.URI, "http://xmlns.com/foaf/0.1/")
        self.assertEqual(Namespace("dc").URI, Namespace("dcterms").URI)

        ns = Namespace("pcdm")
        self.assertEqual(ns.prefix, "pcdm")

   
        
class TestCSVData(unittest.TestCase):
     def test_item_types(self):
        c = CSVData(['dcterms:title,dcterms:identifier'])
        self.assertEqual(c.fieldnames, ['dcterms:title','dcterms:identifier'])
        f = c.fields["dcterms:title"]
        self.assertEqual(f.type, Field.TEXT)
        self.assertEqual(f.namespace.prefix, "dcterms")
        self.assertEqual(f.field_name, "title")

        data = ['dcterms:type,dcterms:title,dcterms:identifier,URL:1,RELATION:dc:creator,pcdm:Collection']
        data.append("Text,My title 1,1234,http://ptsefton.com,12345,texts")
        data.append("Image,My title 2,1235,http://ptsefton.com,,images")
        data.append("Text,My title 3,1236,http://ptsefton.com,,texts")
        data.append("pcdm:Collection,My collection,1237,,,")
        
        c = CSVData(data)
        c.get_items()
        self.assertEqual(c.collections[0].type, 'pcdm:Collection')
        self.assertTrue(c.collections[0].is_collection)
        self.assertEqual(len(c.items), 3)
        #TODO TEST TITLE AND ID
        self.assertEqual(c.items[2].title, "My title 3")
        self.assertEqual(c.items[2].in_collection, "texts")
        self.assertEqual(len(c.collections), 1)

        # Can serialise an item as RDF
        self.assertEqual(c.items[1].getRDF(), "")
        
class TestFields(unittest.TestCase):
    def test_file(self):
        f = Field("FILE:1")
        self.assertEqual(f.type, Field.FILE)
        self.assertEqual(f.namespace.URI, None)
        self.assertEqual(f.field_name, "1")
        
    def test_url(self):
        f = Field("URL:1001 1")
        self.assertEqual(f.type, Field.URL)
        self.assertEqual(f.namespace.URI, None)
        self.assertEqual(f.field_name, "1001 1")

    def test_collection(self):
        f = Field("pcdm:Collection")
        self.assertEqual(f.type, Field.IN_COLLECTION)
        
    def test_relation(self):
        f = Field("RELATION:dc:title")
        self.assertEqual(f.type, Field.RELATION)
        self.assertEqual(f.namespace.prefix, "dcterms")
        self.assertEqual(f.field_name, "title")

        f = Field("dc:type")
        self.assertEqual(f.type, Field.ITEM_TYPE)
        self.assertEqual(f.namespace.prefix, "dcterms")
        self.assertEqual(f.field_name, "type")

        f = Field("REL:dc:title")
        self.assertEqual(f.type, Field.RELATION)
        self.assertEqual(f.namespace.prefix, "dcterms")
        self.assertEqual(f.field_name, "title")

        
        f = Field("RELATION:title")
        self.assertEqual(f.type, None)
        self.assertEqual(f.namespace.name, None)
        self.assertEqual(f.field_name, None)

    def testRecurrence(self):
        f = Field("dc:creator+")
        self.assertEqual(f.type, Field.TEXT)
        self.assertEqual(f.namespace.prefix, "dcterms")
        self.assertEqual(f.field_name, "creator")
        self.assertTrue(f.repeats)

        
if __name__ == '__main__':
    unittest.main()
