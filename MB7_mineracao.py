import ee
import collections
import json
import os # This is is needed in the pyqgis console also
from qgis.core import QgsJsonUtils
from qgis.core import QgsJsonExporter
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *
from qgis.gui import *
from qgis.utils import *

from PyQt5.QtGui import QInputDialog #this is for your dialogs
from qgis.core import (
    QgsVectorLayer
)

collections.Callable = collections.abc.Callable
from ee_plugin import Map
try:
    ee.Initialize()
except:
    ee.Authenticate()
    ee.Initialize()


tempTuple = QInputDialog.getText(None, "senha" ,"Digite a Senha")
password = tempTuple[0]
uri = QgsDataSourceUri()
uri.setConnection("azure.solved.eco.br", "5432", "mb7_mining", "luizcf14", password)
uri.setDataSource("public", "remove_regions", "geom")
vlayer = QgsVectorLayer(uri.uri(False), "PG - Remove Regions", "postgres")

teste = QgsJsonExporter(vlayer)
data  = str(teste.exportFeatures(vlayer.getFeatures())).replace("id","gid").replace("'",'"')
data = json.loads(data)
postgisGeometries = ee.FeatureCollection(data)

def getGeometriasLixo(feat):
    print(str(feat['name']))
    return ee.FeatureCollection(str(feat['name']))
    
geomLixolista = ee.data.listAssets({'parent':'projects/solvedltda/assets/MB7_mining/geometriasLixo/'})['assets']
geomLixolist =  ee.List([])
for glixo in geomLixolista:
    geomLixolist = geomLixolist.add(ee.FeatureCollection(str(glixo['id'])))
#print(geomLixolist.size().getInfo())
geomLixolist = ee.FeatureCollection(geomLixolist).flatten().merge(postgisGeometries)
#geomAddImage = ee.Image(0).toByte().paint(adicionar,1)
geomLixoImage = ee.Image(0).toByte().paint(geomLixolist,1)

def selectClass(img):
    return img.eq(30)

def filterPixelFrequency(imc,cutPercentage,classID):
    def selectClass(img):
        return img.eq(30)
    imcFreq = imc.select('classification').map(selectClass).sum().divide(36).multiply(100)
    filteredImages= ee.List([])
    for i in range(1985,2022):
        image = imc.filterMetadata('year','equals',i).first()
        gtAgua = ee.ImageCollection('projects/mapbiomas-workspace/TRANSVERSAIS/AGUA5-FT').filter(ee.Filter.eq('version', '11')).filter(ee.Filter.eq('biome', 'AMAZONIA')).filter(ee.Filter.eq('year', i)).filter(ee.Filter.eq('cadence', 'annual')).max()
        #consec_band = image.select('consecutiveness').eq(0)
        image = image.where(gtAgua.eq(1),0).where(imcFreq.lte(cutPercentage),0)#.and(consec_band)
        filteredImages = filteredImages.add(image)
    return ee.ImageCollection(filteredImages)


def getImageCollection():
    images = ee.List([]);
    for i in range(1985,2022):
        img = ee.Image('projects/solvedltda/assets/MB7_mining/MB7_Mining/ft-'+str(i)+'-1').where(geomLixoImage.eq(1),0)#.and(geomAddImage.eq(0)),0)
        images = images.add(img)
        if(i == 2021):
            img = img.set({'nextYear':(i-1)})
        else:
            img = img.set({'nextYear':(i+1)})
    return ee.ImageCollection(images)
    
def PixelFrequency (imc,cutPercentage,classID):
    imcFreq = imc.map(selectClass).sum().divide(36).multiply(100) #Frequency Image
    return imcFreq
    
imc = getImageCollection()
copyIMC = imc

def getConsecutively(img):
    yearRef = img.get('nextYear')
    yearN1 = ee.Image( getImageCollection().filterMetadata('year','equals',yearRef).mosaic())
    consecutive = ee.Image(0).toByte().where(img.eq(yearN1),1)
    return img.addBands(consecutive.rename('consecutiveness'))

#imc = imc.map(getConsecutively)
mosaic = ee.Image('projects/mapbiomas-workspace/TRANSVERSAIS/ZONACOSTEIRA6/mosaic_2021')
Map.addLayer(mosaic,{'bands': ["swir1","nir","red"], 'max': 126,'min': 10,'opacity': 1},'Mosaico - 2021')
mosaic = ee.Image('projects/mapbiomas-workspace/TRANSVERSAIS/ZONACOSTEIRA6/mosaic_2015')
Map.addLayer(mosaic,{'bands': ["swir1","nir","red"], 'max': 126,'min': 10,'opacity': 1},'Mosaico - 2015',False)
mosaic = ee.Image('projects/mapbiomas-workspace/TRANSVERSAIS/ZONACOSTEIRA6/mosaic_2010')
Map.addLayer(mosaic,{'bands': ["swir1","nir","red"], 'max': 126,'min': 10,'opacity': 1},'Mosaico - 2010',False)
mosaic = ee.Image('projects/mapbiomas-workspace/TRANSVERSAIS/ZONACOSTEIRA6/mosaic_2005')
Map.addLayer(mosaic,{'bands': ["swir1","nir","red"], 'max': 126,'min': 10,'opacity': 1},'Mosaico - 2005',False)
Map.addLayer(ee.Image(PixelFrequency(imc,0,30)).selfMask(),{'min':0,'max':100,'palette':['fff9f9','ff0000','efff00','27ff00','ef00ff']},'Freq Antes-'+str(30),False)

mining = ee.ImageCollection(filterPixelFrequency(imc,11,30))
imcFreq = PixelFrequency(mining,0,30)

Map.addLayer(geomLixolist,{'color':'pink'},'Geom',False)

Map.addLayer(imcFreq.selfMask(),{'min':0,'max':100,'palette':['fff9f9','ff0000','efff00','27ff00','ef00ff']},'Freq -'+str(30))

checkLayer = True
for lyr in QgsProject.instance().mapLayers().values():
    if lyr.name() == "PG - Remove Regions":
        checkLayer = False
if checkLayer:
    QgsProject.instance().addMapLayer(vlayer, False)
    layerTree = iface.layerTreeCanvasBridge().rootGroup()
    layerTree.insertChildNode(0, QgsLayerTreeLayer(vlayer))