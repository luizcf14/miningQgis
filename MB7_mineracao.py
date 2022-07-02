import collections
collections.Callable = collections.abc.Callable
import ee
import json
import os # This is is needed in the pyqgis console also
import requests
from qgis.core import QgsJsonUtils
from qgis.core import QgsJsonExporter
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *
from qgis.gui import *
from qgis.utils import *

from PyQt5 import QtCore, QtGui, QtWidgets
#from PyQt5.QtGui import QToolButton, QIcon #this is for your dialogs
from qgis.core import (QgsVectorLayer)



from ee_plugin import Map
try:
    ee.Initialize()
except:
    ee.Authenticate()
    ee.Initialize()


def UpdateLayer():
    print('Here')
    #postgisGeometries = ee.FeatureCollection(data)



url = "https://github.com/luizcf14/miningQgis/raw/main/icon.png"
toolbar = iface.addToolBar("Solved Plugin")
response = requests.get(url)
pixmap = QPixmap()
pixmap.loadFromData(response.content)
someact = QAction(QIcon(pixmap),QCoreApplication.translate("test", "My Action"),iface.mainWindow())
someact.triggered.connect(UpdateLayer)
toolbar.addAction(someact)


tempTuple = QInputDialog.getText(None, "senha" ,"Digite a Senha")
password = tempTuple[0]
uri = QgsDataSourceUri()
uri.setConnection("azure.solved.eco.br", "5432", "mb7_mining", "luizcf14", password)
uri.setDataSource("public", "remove_regions", "geom")
vlayer = QgsVectorLayer(uri.uri(False), "PG - Remove Regions", "postgres")

teste = QgsJsonExporter(vlayer)
data  = str(teste.exportFeatures(vlayer.getFeatures())).replace("id","gid").replace("'",'"')
data = json.loads(data)
#postgisGeometries = ee.FeatureCollection(data)

uriPOI = QgsDataSourceUri()
uriPOI.setConnection("azure.solved.eco.br", "5432", "mb7_mining", "luizcf14", password)
uriPOI.setDataSource("public", "miningsolved", "geom","scale not like 'Falso positivo'")
uriPOI_layer = QgsVectorLayer(uriPOI.uri(False), "PG - Interest Regions", "postgres")
#jsonExporter = QgsJsonExporter(uriPOI_layer)
#data_uriPOI_layer   = str(jsonExporter.exportFeatures(uriPOI_layer.getFeatures())).replace("id","gid").replace("'",'"')
#data_uriPOI_layer  = json.loads(data_uriPOI_layer)
#includeGeometries = ee.FeatureCollection(data_uriPOI_layer)
#ROI = ee.Image(0).toByte().paint(includeGeometries,1)


def getGeometriasLixo(feat):
    print(str(feat['name']))
    return ee.FeatureCollection(str(feat['name']))
    
geomLixolista = ee.data.listAssets({'parent':'projects/solvedltda/assets/MB7_mining/geometriasLixo/'})['assets']
geomLixolist =  ee.List([])
for glixo in geomLixolista:
    geomLixolist = geomLixolist.add(ee.FeatureCollection(str(glixo['id'])))
#print(geomLixolist.size().getInfo())
geomLixolist = ee.FeatureCollection(geomLixolist).flatten()#.merge(postgisGeometries)
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

def getImageCollectionMB6():
    images = ee.List([]);
    for i in range(1985,2021):
        img = ee.Image('projects/mapbiomas-workspace/TRANSVERSAIS/MINERACAO6-FT/'+str(i)+'-5')
        images = images.add(img)
    return ee.ImageCollection(images)


def getImageCollection():
    images = ee.List([]);
    for i in range(1985,2022):
        img = ee.Image('projects/solvedltda/assets/MB7_mining/MB7_Mining/ft-'+str(i)+'-1').where(geomLixoImage.eq(1),0)#.where(ROI.eq(0),0)#.and(geomAddImage.eq(0)),0)
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
imcMB6 = getImageCollectionMB6()
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
#Map.addLayer(geomLixolist,{'color':'pink'},'Geom',False)
Map.addLayer(ee.Image(PixelFrequency(imcMB6,0,30)).selfMask(),{'min':0,'max':100,'palette':['fff9f9','ff0000','efff00','27ff00','ef00ff']},'Freq MB6 -'+str(30),False)
Map.addLayer(imcFreq.selfMask(),{'min':0,'max':100,'palette':['fff9f9','ff0000','efff00','27ff00','ef00ff']},'Freq -'+str(30))



checkLayer = True
for lyr in QgsProject.instance().mapLayers().values():
    if lyr.name() == "PG - Remove Regions":
        checkLayer = False
if checkLayer:
    QgsProject.instance().addMapLayer(vlayer, False)
    layerTree = iface.layerTreeCanvasBridge().rootGroup()
    layerTree.insertChildNode(0, QgsLayerTreeLayer(vlayer))
    
checkLayer = True
for lyr in QgsProject.instance().mapLayers().values():
    if lyr.name() == "PG - Interest Regions":
        checkLayer = False
if checkLayer:
    QgsProject.instance().addMapLayer(uriPOI_layer, False)
    layerTree = iface.layerTreeCanvasBridge().rootGroup()
    layerTree.insertChildNode(0, QgsLayerTreeLayer(uriPOI_layer))
