# coding=utf-8

import unittest
from tempfile import mktemp
from qgis.testing.mocked import get_iface
get_iface()


from qgis.core import (
    QgsVectorLayer,
    QgsRasterLayer,
    QgsField,
    QgsCoordinateReferenceSystem,
    QGis,
)
from PyQt4.QtCore import QFileInfo, QVariant
from osgeo import gdal



from geopackage import GeoPackage



class TestGeoPackage(unittest.TestCase):

    """Test the GeoPackage datastore."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_geopackage(self):
        """Test if we can store geopackage."""
        # Create a geopackage from an empty file.
        path = QFileInfo(mktemp() + '.gpkg')
        self.assertFalse(path.exists())
        data_store = GeoPackage(path)
        path.refresh()
        self.assertTrue(path.exists())

        # Create a new field from scratch
        fields = [
            QgsField('id', QVariant.Int),
            QgsField('name', QVariant.String)
        ]
        crs = QgsCoordinateReferenceSystem('EPSG:4326')
        print crs.authid()
        print crs.isValid()
        # geopackage.create_vector_layer('test', crs, QGis.Polygon)
        # self.assertIn('test', geopackage.vector_layers_list())



if __name__ == '__main__':
    unittest.main()
