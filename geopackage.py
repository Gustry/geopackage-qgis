from osgeo import ogr, osr, gdal
from PyQt4.QtCore import QFileInfo
from qgis.core import (
    QgsVectorLayer,
    QgsRasterLayer,
)

# Testing
from tempfile import mktemp
from qgis.core import (
    QgsVectorLayer,
    QgsRasterLayer,
    QgsField,
    QgsCoordinateReferenceSystem,
    QGis,
)
from PyQt4.QtCore import QFileInfo, QVariant
from osgeo import gdal
# End testing


# From https://qgis.org/api/classQGis.html#a8da456870e1caec209d8ba7502cceff7
QGIS_OGR_GEOMETRY_MAP = {
    0: ogr.wkbUnknown,
    1: ogr.wkbPoint,
    2: ogr.wkbLineString,
    3: ogr.wkbPolygon,
    4: ogr.wkbMultiPoint,
    5: ogr.wkbMultiLineString,
    6: ogr.wkbMultiPolygon,
    100: ogr.wkbNone
}


class GeoPackage(object):

    """Helper class to create and manage a geopackage."""

    vector_driver = ogr.GetDriverByName('GPKG')
    raster_driver = gdal.GetDriverByName('GPKG')

    def __init__(self, uri):
        """Constructor for the GeoPackage DataStore.

        :param uri: A filepath
        :type uri: QFileInfo, str
        """
        if isinstance(uri, QFileInfo):
            self._uri = uri
        elif isinstance(uri, basestring):
            self._uri = QFileInfo(uri)
        else:
            raise Exception('Unknown URI type')

        if self._uri.exists():
            raster_datasource = gdal.Open(self._uri.absoluteFilePath())
            if raster_datasource is None:
                # Raster driver failed to load, let's try if it's a vector one.
                vector_datasource = self.vector_driver.Open(
                    self._uri.absoluteFilePath())
                if vector_datasource is None:
                    msg = 'The file is not a geopackage or it doesn\'t ' \
                          'contain any layers.'
                    raise Exception(msg)
        else:
            # The file doesn't exist, we create the geopackage.
            path = self._uri.absoluteFilePath()
            datasource = self.vector_driver.CreateDataSource(path)
            del datasource

    @property
    def uri(self):
        """Return the URI of the GeoPackage.

        :return: The URI as a path.
        :rtype: basestring
        """
        return self._uri

    def vector_layers_list(self):
        """Return a list of vector layers available in the geopackage.

        :return: List of vector layer names.
        :rtype: list
        """
        layers = []
        vector_datasource = self.vector_driver.Open(
            self._uri.absoluteFilePath())
        if vector_datasource:
            for i in range(vector_datasource.GetLayerCount()):
                layers.append(vector_datasource.GetLayer(i).GetName())
        return layers

    def raster_layers_list(self):
        """Return a list of raster layers available in the geopackage.

        :return: List of raster layer names available.
        :rtype: list
        """
        layers = []

        raster_datasource = gdal.Open(self._uri.absoluteFilePath())
        if raster_datasource:
            sub_datasets = raster_datasource.GetSubDatasets()
            if len(sub_datasets) == 0:
                metadata = raster_datasource.GetMetadata()
                layers.append(metadata['IDENTIFIER'])
            else:
                for sub_dataset in sub_datasets:
                    layers.append(sub_dataset[0].split(':')[2])

        return layers

    def layers_list(self):
        """Return a list of layers available.

        :return: List of layers available in the geopackage.
        :rtype: list
        """
        return self.vector_layers_list() + self.raster_layers_list()

    def layer_uri(self, layer_name):
        """Get a layer URI.

        For a vector layer :
        /path/to/the/geopackage.gpkg|layername=my_vector_layer

        For a raster :
        GPKG:/path/to/the/geopackage.gpkg:my_raster_layer

        :param layer_name: The name of the layer to fetch.
        :type layer_name: str

        :return: The URI to the layer or None if the layer name doesn't exist.
        :rtype: str
        """
        for layer in self.vector_layers_list():
            if layer == layer_name:
                uri = u'{file_path}|layername={layer_name}'.format(
                    file_path=self._uri.absoluteFilePath(),
                    layer_name=layer_name)
                return uri
        else:
            for layer in self.raster_layers_list():
                if layer == layer_name:
                    uri = u'GPKG:{file_path}:{layer_name}'.format(
                        file_path=self._uri.absoluteFilePath(),
                        layer_name=layer_name)
                    return uri
            else:
                return None

    def layer(self, layer_name):
        """Get a QGIS layer given a layer name.

        :param layer_name: The name of the layer to fetch.
        :type layer_name: str

        :return: The QGIS layer or None if the layer name doesn't exist.
        :rtype: QgsMapLayer
        """
        uri = self.layer_uri(layer_name)
        layer = QgsVectorLayer(uri, layer_name, 'ogr')
        if not layer.isValid():
            layer = QgsRasterLayer(uri, layer_name)
            if not layer.isValid():
                return None

        return layer

    def create_vector_layer(self, name, crs=None, geometry=None):
        """Create a vector layer from scratch.
        
        :param name: The name of the layer.
        :type name: basestring
        
        :param crs: The CRS of the new layer.
        :type crs: QgsCoordinateReferenceSystem
        
        :param geometry: The geometry. It can be None for a non spatial table.
        :type geometry: wkbType
        """
        # TODO
        # Check non spatial table, (CRS and geometry)
        # Check if the layer is existing

        print name
        print crs.authid()
        print geometry

        gdal_spatial_reference = osr.SpatialReference()
        qgis_spatial_reference = crs.authid()
        gdal_spatial_reference.ImportFromEPSG(
            int(qgis_spatial_reference.split(':')[1]))

        print int(qgis_spatial_reference.split(':')[1])

        vector_datasource = GeoPackage.vector_driver.Open(
            self._uri.absoluteFilePath(), True)
        layer = vector_datasource.CreateLayer(
            name, gdal_spatial_reference, geometry)
        layer.DeleteField(0)
        del vector_datasource

        qgis_layer = self.layer(name)
        qgis_layer.startEditing()
        fid_in_fields = False
        for field in fields:
            if field.name() == 'fid':
                fid_in_fields = True
            qgis_layer.addAttribute(field)
        qgis_layer.commitChanges()

        # Hack to remove the field creating by OGR. Not working for now.
        if not fid_in_fields:
            print 'here'
            data_provider = qgis_layer.dataProvider()
            index = qgis_layer.fieldNameIndex('fid')
            print index
            print data_provider.deleteAttributes([index])
            qgis_layer.updateFields()

    def add_vector_layer(self, layer):
        """Add a vector layer to the geopackage.

        :param layer: The layer to add.
        :type layer: QgsVectorLayer

        :returns: A two-tuple. The first element will be True if we could add
            the layer to the datastore. The second element will be the layer
            name which has been used or the error message.
        :rtype: (bool, str)
        """
        print layer.wkbType()
        print QGIS_OGR_GEOMETRY_MAP[layer.wkbType()]
        self.create_vector_layer(
            layer.name(), layer.crs(), QGIS_OGR_GEOMETRY_MAP[layer.wkbType()])
        vector_layer = self.layer(layer.name())

        data_provider = vector_layer.dataProvider()
        for feature in vector_layer.getFeatures():
            data_provider.addFeatures([feature])

        return True, layer.name()

    def remove(self, name):

        if name in self.vector_layers_list():
            datasource = GeoPackage.vector_driver.Open(
                self._uri.absoluteFilePath(), True)
        elif name in self.raster_layers_list():
            datasource = GeoPackage.raster_driver.Open(
                self._uri.absoluteFilePath(), True)
        else:
            datasource = None

        if datasource:
            datasource.DeleteLayer(name)


# Testing
path = QFileInfo(mktemp() + '.gpkg')
geopackage = GeoPackage(path)
path.refresh()
assert path.exists()

# Create a new field from scratch
fields = [
    QgsField('id', QVariant.Int),
    QgsField('name', QVariant.String)
]
crs = QgsCoordinateReferenceSystem('EPSG:4326')
geopackage.create_vector_layer('test', crs, QGis.WKBPolygon)
geopackage.create_vector_layer('test2', crs, QGis.WKBPolygon)
geopackage.create_vector_layer('test3', crs, QGis.WKBPolygon)
geopackage.remove('test')
assert 'test2' in geopackage.vector_layers_list()
print geopackage.vector_layers_list()
print 'working'
print path.absoluteFilePath()

print "ADD"
layer = iface.activeLayer()
geopackage.add_vector_layer(layer)
