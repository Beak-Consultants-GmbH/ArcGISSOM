#!/usr/bin/env python
# -*- coding: utf8 -*-

"""
SOM-Toolbox for Arcmap 10.6.1

SOM_Clustering.py author: Peggy Hielscher, Andreas Kempe, Beak Consultants GmbH, finished on 22 Oct 2020
"""

import arcpy
import xml.dom.minidom as dom
import subprocess
from arcpy.sa import Con, Raster, IsNull
from os.path import join
import os, sys
arcpy.env.overwriteOutput = True

class ApplicationError(Exception):
    pass
class VersionError(Exception):
    pass

# creates temporary folder in the workspace
def createfolders():
    tempfolder = "Temp"
    arcpy.CreateFolder_management(workspace, tempfolder)
    path_to_temp0 = join(workspace,tempfolder) 
    if arcpy.Exists(path_to_temp0):
        arcpy.AddMessage("Folder 'Temp' is created.")

    # creates folder Geo-space in the workspace
    geofolder = "GeoSpace"
    arcpy.CreateFolder_management(workspace, geofolder)
    path_to_geofolder0 = join(workspace,geofolder) 
    if arcpy.Exists(path_to_geofolder0):
        arcpy.AddMessage("Folder 'GeoSpace' is created.")

    # creates folder SOM-space in the workspace
    somfolder = "SomSpace"
    arcpy.CreateFolder_management(workspace, somfolder)
    path_to_somfolder0 = join(workspace,somfolder) 
    if arcpy.Exists(path_to_somfolder0):
        arcpy.AddMessage("Folder 'SomSpace' is created.")

    # creates output folder in the workspace
    output_folder = "output_folder"
    arcpy.CreateFolder_management(workspace, output_folder)
    path_to_outputfolder0 = join(workspace,output_folder) 
    if arcpy.Exists(path_to_outputfolder0):
        arcpy.AddMessage("Folder 'output_folder' is created.")
    
    return path_to_temp0, path_to_geofolder0, path_to_somfolder0, path_to_outputfolder0 

# creates an xml file for transferring parameters
def write_xml():
    tree = dom.Document()
    som_configuration = dom.Element("som_configuration")

    som_files = dom.Element("som_files")

    som_input = dom.Element("input")
    text = dom.Text()
    text.data = join(workspace,"SOM.lrn")
    som_input.appendChild(text)

    output_somspace = dom.Element("output_somspace")
    text = dom.Text()
    text.data = join(workspace,"somspace.txt")
    output_somspace.appendChild(text)

    output_geospace = dom.Element("output_geospace")
    text = dom.Text()
    text.data = join(workspace,"geospace.txt")
    output_geospace.appendChild(text) 

    output_folder = dom.Element("output_folder") 
    text = dom.Text()
    text.data = join(workspace,"output_folder")                     
    output_folder.appendChild(text) 

    som_files.appendChild(som_input)
    som_files.appendChild(output_somspace)
    som_files.appendChild(output_geospace)
    som_files.appendChild(output_folder)

    som_parameters = dom.Element("som_parameters")

    som_x = dom.Element("som_x") 
    text = dom.Text()
    text.data = cellsize_x
    som_x.appendChild(text) 

    som_y = dom.Element("som_y")
    text = dom.Text()
    text.data = cellsize_y
    som_y.appendChild(text) 

    nEpoch = dom.Element("nEpoch")
    text = dom.Text()
    text.data = num_epochs
    nEpoch.appendChild(text) 

    mapType = dom.Element("mapType")
    text = dom.Text()
    text.data = map_type
    mapType.appendChild(text) 

    gridType = dom.Element("gridType")
    text = dom.Text()
    text.data = grid_shape
    gridType.appendChild(text) 

    neighborhood = dom.Element("neighborhood")
    text = dom.Text()
    text.data = neigh_func
    neighborhood.appendChild(text) 

    std_coeff = dom.Element("std_coeff")
    text = dom.Text()
    text.data = Gaussian_coeff.replace(",",".")
    std_coeff.appendChild(text) 

    initialization = dom.Element("initialization")
    text = dom.Text()
    text.data = inits
    initialization.appendChild(text) 

    radius0 = dom.Element("radius0")
    text = dom.Text()
    text.data = initial_neigh
    radius0.appendChild(text) 

    radiusN = dom.Element("radiusN")
    text = dom.Text()
    text.data = final_neigh
    radiusN.appendChild(text) 

    radiuscooling = dom.Element("radiuscooling")
    text = dom.Text()
    text.data = radius_cooling
    radiuscooling.appendChild(text) 

    scale0 = dom.Element("scale0")
    text = dom.Text()
    text.data = initial_trainingrate.replace(",",".")
    scale0.appendChild(text) 

    scaleN = dom.Element("scaleN")
    text = dom.Text()
    text.data = final_trainingrate.replace(",",".")
    scaleN.appendChild(text) 

    scalecooling = dom.Element("scalecooling")
    text = dom.Text()
    text.data = scale_cooling
    scalecooling.appendChild(text) 
   
    som_parameters.appendChild(som_x)
    som_parameters.appendChild(som_y)
    som_parameters.appendChild(nEpoch)
    som_parameters.appendChild(mapType)
    som_parameters.appendChild(gridType)
    som_parameters.appendChild(neighborhood)
    som_parameters.appendChild(std_coeff)
    som_parameters.appendChild(initialization)
    som_parameters.appendChild(radius0)
    som_parameters.appendChild(radiusN)
    som_parameters.appendChild(radiuscooling)
    som_parameters.appendChild(scale0)
    som_parameters.appendChild(scaleN)
    som_parameters.appendChild(scalecooling)
    
    Kmeans = dom.Element("kMeans")

    number = dom.Element("number")
    text = dom.Text()
    text.data = num_initital_centroids
    number.appendChild(text) 

    number_min = dom.Element("number_min")
    text = dom.Text()
    text.data = min_num_clusters
    number_min.appendChild(text) 

    number_max = dom.Element("number_max")
    text = dom.Text()
    text.data = max_num_clusters
    number_max.appendChild(text) 

    Kmeans.appendChild(number)
    Kmeans.appendChild(number_min)
    Kmeans.appendChild(number_max)
        
    som_parameters.appendChild(Kmeans)
    
    som_configuration.appendChild(som_files)
    som_configuration.appendChild(som_parameters)

    tree.appendChild(som_configuration)

    f = open(join(workspace,"SOM.xml"), "w")
    tree.writexml(f, "", "\t", "\n")
    f.close()
    path_to_somxml = join(workspace,"SOM.xml") 
    if arcpy.Exists(path_to_somxml):
        arcpy.AddMessage("File 'SOM.xml' is written.")
    return path_to_somxml

# creates a mask via raster calculator 
def create_mask(path_to_temp):
    arcpy.CheckOutExtension('Spatial')
    inputrasters = arcpy.GetParameterAsText(1).split(";")
    rasterlist = []
    for elements in inputrasters:
        rasterobject = Raster(elements)
        rasterlist.append(rasterobject)
    rasterlistSum = sum(rasterlist)                     
    outcon = Con(IsNull(rasterlistSum) == 0,1)          # result raster has 1 when value meets value and NoData when value meets NoData
    outcon.save(join(path_to_temp,"mask"))              # filename is 'mask'
    #arcpy.CheckInExtension('Spatial')                  
    path_to_mask = join(path_to_temp,"mask")
    if arcpy.Exists(path_to_mask):
        arcpy.AddMessage("Creating mask.")
    return path_to_mask

# executes Run_CreateSOMLrnFile.exe
def create_lrn(path_to_temp):
    path_to_Run_CreateSOMLrnFile_exe = path_to_Run_CreateSOMLrnFile
    output_lrn_file = join(workspace,"SOM.lrn")
    maskRasterFullFileName = join(path_to_temp,"mask")                 
    rasterDataset = input_raster.replace(";"," ") 
    
    arcpy.AddMessage("{} {} {} {} {}".format(path_to_Run_CreateSOMLrnFile_exe,
                                                    workspace,
                                                    output_lrn_file,
                                                    maskRasterFullFileName,
                                                    rasterDataset))
    
    Run_CreateSOMLrnFile_exe = "{} {} {} {} {}".format(path_to_Run_CreateSOMLrnFile_exe,
                                                    workspace,
                                                    output_lrn_file,
                                                    maskRasterFullFileName,
                                                    rasterDataset)
    arcpy.AddMessage("Creating 'SOM.lrn'.")
    
    subprocess.call(Run_CreateSOMLrnFile_exe, startupinfo = sinfo) 
    return None

# executes nextsom_wrap.exe
def wrap():
    path_to_nextsom_wrap_exe = path_to_nextsom_wrap
    path_to_somxml = write_xml()
    xml_file = '"'+path_to_somxml+'"'
    xml_command = '--xmlfile='+xml_file
    proc_command = (path_to_nextsom_wrap_exe+" "+xml_command)
    arcpy.AddMessage("Processing 'SOM.xml' and executing 'nextsom_wrap.exe'.")
    subprocess.call(proc_command, startupinfo = sinfo)
    return None

# executes CreateSomResultRaster.exe
def resultraster(path_to_temp, path_to_geofolder, path_to_somfolder):
    path_to_CreateSomResultRaster_exe = path_to_CreateSomResultRaster
    maskRasterFullFileName = join(path_to_temp,"mask")       
    GeoSpaceTxtFullFileName = join(workspace,"geospace.txt")
    GeoClusterFullFileName = join(path_to_geofolder, "Geo_cluster")
    SomSpaceTxtFullFileName = join(workspace,"somspace.txt")
    SomClusterFullFileName = join(path_to_somfolder, "SOM_cluster")
    SomDim_X = cellsize_x # number of cells in x-direction
    SomDim_Y = cellsize_y # number of cells in y-direction
    NumberMID = len(arcpy.GetParameterAsText(1).split(";"))
    
    arcpy.AddMessage("Creating results. This can take a few minutes.")
    
    Run_CreateSomResultRaster = "{} {} {} {} {} {} {} {} {} {} {} {}".format(path_to_CreateSomResultRaster_exe,
                                                                workspace,
                                                                path_to_geofolder,
                                                                path_to_somfolder,
                                                                maskRasterFullFileName,
                                                                GeoSpaceTxtFullFileName,
                                                                GeoClusterFullFileName,
                                                                SomSpaceTxtFullFileName,
                                                                SomClusterFullFileName,
                                                                SomDim_X,
                                                                SomDim_Y,
                                                                NumberMID)
    subprocess.call(Run_CreateSomResultRaster, startupinfo = sinfo)
    return None

# loads project
def loadresults(path_to_geofolder, path_to_somfolder):
    mxd = arcpy.mapping.MapDocument("CURRENT")
    activeDataframe = mxd.activeDataFrame
    
    if arcpy.Exists(path_to_EmptyLayer):
        # creates first group layer from empty layer and adds rasters of Geo-space
        emptyLayer1 = arcpy.mapping.Layer(path_to_EmptyLayer)	  
        arcpy.mapping.AddLayer(activeDataframe, emptyLayer1, "BOTTOM")
        
        targetGroupLayer1 = arcpy.mapping.ListLayers(mxd, emptyLayer1, activeDataframe)[0]
        targetGroupLayer1.name = "Geospace Data"
        targetGroupLayer1.description = "This is a group layer of geospace results."

        newlayer_geo_cluster = arcpy.mapping.Layer(join(path_to_geofolder,"Geo_cluster"))
        newlayer_geo_cluster.name = "Geo Cluster"
        newlayer_quant_error = arcpy.mapping.Layer(join(path_to_geofolder,"quant_error"))
        newlayer_quant_error.name = "Quantization Error"
        
        arcpy.mapping.AddLayerToGroup(activeDataframe, targetGroupLayer1, newlayer_geo_cluster, "BOTTOM")
        arcpy.mapping.AddLayerToGroup(activeDataframe, targetGroupLayer1, newlayer_quant_error, "BOTTOM")

        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()

        # creates second group layer from empty layer and adds rasters of SOM-space
        emptyLayer2 = arcpy.mapping.Layer(path_to_EmptyLayer)	  
        arcpy.mapping.AddLayer(activeDataframe, emptyLayer2, "BOTTOM")
        
        targetGroupLayer2 = arcpy.mapping.ListLayers(mxd, emptyLayer2, activeDataframe)[0]
        targetGroupLayer2.name = "SOM Space Data"
        targetGroupLayer2.description = "This is a group layer of SOM-space results."

        newlayer_SOM_cluster = arcpy.mapping.Layer(join(path_to_somfolder,"SOM_cluster")) 
        newlayer_SOM_cluster.name = "SOM Cluster"
        newlayer_umatrix = arcpy.mapping.Layer(join(path_to_somfolder,"umatrix"))
        newlayer_umatrix.name = "U-Matrix"

        colorSourceLayer = arcpy.mapping.Layer(path_to_ColorSource)
        arcpy.mapping.UpdateLayer(activeDataframe, newlayer_SOM_cluster, colorSourceLayer)
        arcpy.mapping.UpdateLayer(activeDataframe, newlayer_umatrix, colorSourceLayer)

        arcpy.mapping.AddLayerToGroup(activeDataframe, targetGroupLayer2, newlayer_SOM_cluster, "BOTTOM")
        arcpy.mapping.AddLayerToGroup(activeDataframe, targetGroupLayer2, newlayer_umatrix, "BOTTOM")

        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()

        # create subordered group layer from empty layer and adds it to the group layer 1
        emptyLayer3 = arcpy.mapping.Layer(path_to_EmptyLayer)
        arcpy.mapping.AddLayerToGroup(activeDataframe, targetGroupLayer1, emptyLayer3, "BOTTOM")

        targetGroupLayer3 = arcpy.mapping.ListLayers(mxd, emptyLayer3, activeDataframe)[0] 
        targetGroupLayer3.name = "BMU Data" #Raster input data
        targetGroupLayer3.description = "This is a group layer of input rasters"
        
        arcpy.env.workspace=path_to_geofolder
        created_files_geospace = arcpy.ListFiles()
        
        created_files_geospace.remove('geo_cluster')
        created_files_geospace.remove('quant_error')
        created_files_geospace.remove('info')

        for layers in created_files_geospace:
            newlayer = arcpy.mapping.Layer(layers)
            arcpy.mapping.AddLayerToGroup(activeDataframe, targetGroupLayer3, newlayer, "BOTTOM")
       
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()
        
        # create subordered group layer from empty layer and adds it to the group layer 2
        emptyLayer4 = arcpy.mapping.Layer(path_to_EmptyLayer)
        arcpy.mapping.AddLayerToGroup(activeDataframe, targetGroupLayer2, emptyLayer4, "BOTTOM")

        targetGroupLayer4 = arcpy.mapping.ListLayers(mxd, emptyLayer4, activeDataframe)[0] 
        targetGroupLayer4.name = "BMU Data" #Raster input data
        targetGroupLayer4.description = "This is a group layer of input rasters"

        arcpy.env.workspace=path_to_somfolder
        created_files_somspace = arcpy.ListFiles()
        created_files_somspace.remove('som_cluster')
        created_files_somspace.remove('umatrix')
        created_files_somspace.remove('info')

        colorSourceLayer = arcpy.mapping.Layer(path_to_ColorSource)
        
        for layers in created_files_somspace:
            newlayer = arcpy.mapping.Layer(layers)
            arcpy.mapping.UpdateLayer(activeDataframe, newlayer, colorSourceLayer)
            arcpy.mapping.AddLayerToGroup(activeDataframe, targetGroupLayer4, newlayer, "BOTTOM")
        
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()
        
    else:# if subordered layers fail, layers are grouped without subordering
        # defines Geospace results
        newlayer_geo_cluster = arcpy.mapping.Layer(join(path_to_geofolder,"Geo_cluster"))
        newlayer_quant_error = arcpy.mapping.Layer(join(path_to_geofolder,"quant_error"))
        
        arcpy.env.workspace=path_to_geofolder
        created_files_geospace = arcpy.ListFiles()
        created_files_geospace.remove('geo_cluster')
        created_files_geospace.remove('quant_error')
        created_files_geospace.remove('info')

        # defines Somspace results
        newlayer_SOM_cluster = arcpy.mapping.Layer(join(path_to_somfolder,"SOM_cluster")) 
        newlayer_umatrix = arcpy.mapping.Layer(join(path_to_somfolder,"umatrix"))

        arcpy.env.workspace=path_to_somfolder
        created_files_somspace = arcpy.ListFiles()
        created_files_somspace.remove('som_cluster')
        created_files_somspace.remove('umatrix')
        created_files_somspace.remove('info')

        # adds Geospace results to the map
        arcpy.mapping.AddLayer(activeDataframe, newlayer_geo_cluster, "BOTTOM")
        arcpy.mapping.AddLayer(activeDataframe, newlayer_quant_error, "BOTTOM")
        
        for layers in created_files_geospace:
            newlayer_g = arcpy.mapping.Layer(layers)
            arcpy.mapping.AddLayer(activeDataframe, newlayer_g, "BOTTOM")

        # adds Somspace results to the map
        colorSourceLayer = arcpy.mapping.Layer(path_to_ColorSource)
        arcpy.mapping.UpdateLayer(activeDataframe, newlayer_SOM_cluster, colorSourceLayer)
        arcpy.mapping.UpdateLayer(activeDataframe, newlayer_umatrix, colorSourceLayer)
        arcpy.mapping.AddLayer(activeDataframe, newlayer_SOM_cluster, "BOTTOM")
        arcpy.mapping.AddLayer(activeDataframe, newlayer_umatrix, "BOTTOM")
        
        for layers in created_files_somspace:
            newlayer_s = arcpy.mapping.Layer(layers)
            arcpy.mapping.UpdateLayer(activeDataframe, newlayer_s, colorSourceLayer)
            arcpy.mapping.AddLayer(activeDataframe, newlayer_s, "BOTTOM")
        
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()
    return None

# check presence of data 
def check_data_and_run():
    inputrasters = arcpy.GetParameterAsText(1).split(";")
    for layers in inputrasters:
        rasterobj1 = Raster(layers)
        # resolution and extent
        arcpy.AddMessage ("The name of the raster: " + str(rasterobj1.name))
        arcpy.AddMessage ("The resolution of the raster: x " + str(rasterobj1.meanCellWidth) + ', y '+ str(rasterobj1.meanCellHeight))
        arcpy.AddMessage ("The extent of the raster: " + str(rasterobj1.extent))
        # projection
        rasterobj2 = arcpy.Describe(layers).spatialReference
        arcpy.AddMessage ("The name of the spatial reference: " + str(rasterobj2.name))
        arcpy.AddMessage ("The type of the spatial reference: " + str(rasterobj2.type))
        arcpy.AddMessage ("The projected coordinate system code: " + str(rasterobj2.PCSCode))
        #https://desktop.arcgis.com/de/arcmap/10.3/analyze/arcpy-classes/spatialreference.htm
        #https://desktop.arcgis.com/de/arcmap/10.3/analyze/arcpy-classes/raster-object.htm
    
    check_res = []
    check_proj = []
    for layers in inputrasters:
        rasterobj1 = Raster(layers)
        rasterobj2 = arcpy.Describe(layers).spatialReference
        check_res.append(rasterobj1.meanCellWidth)
        check_proj.append(rasterobj2.name)
    testres1 = all(x == check_res[0] for x in check_res)
    testres2 = all(x == check_proj[0] for x in check_proj)

    if testres1 == True and testres2 == True:
        # create folders
        path_to_temp, path_to_geofolder, path_to_somfolder, out = createfolders()       #(access from VB)
    
        # create mask
        create_mask(path_to_temp)                                                       

        if arcpy.Exists(join(path_to_temp,"mask")):
            # create lrn
            create_lrn(path_to_temp)                                                    
            # wrap
            wrap()                                                                      
    
            if arcpy.Exists(join(workspace,"SOM.lrn")):
                if arcpy.Exists(join(workspace,"geospace.txt")):
                    if arcpy.Exists(join(workspace,"somspace.txt")):
                        resultraster(path_to_temp, path_to_geofolder, path_to_somfolder)# resultraster
                    else:
                        arcpy.AddMessage("File 'somspace.txt' was not created.")
                        pass
                else:
                    arcpy.AddMessage("File 'geospace.txt' was not created.")
                    pass
            else:
                arcpy.AddMessage("File 'SOM.lrn' was not created.")    
                pass
        else:
            arcpy.AddMessage("File 'mask' was not created.")
            pass    
    
        if arcpy.Exists(join(path_to_geofolder,"Geo_cluster")):
            arcpy.AddMessage("File 'Geo_cluster' successfully created.")
            if arcpy.Exists(join(path_to_geofolder,"quant_error")):
                arcpy.AddMessage("File 'quant_error' successfully created.")
                if arcpy.Exists(join(path_to_somfolder,"SOM_cluster")):
                    arcpy.AddMessage("File 'SOM_cluster' successfully created.")
                    if arcpy.Exists(join(path_to_somfolder,"SOM_cluster")):
                        arcpy.AddMessage("File 'umatrix' successfully created.")
                        # load results
                        loadresults(path_to_geofolder, path_to_somfolder)                
                    
                        # delete intermediate results
                        if str(is_checked_del) == 'true':
                            arcpy.Delete_management(path_to_temp)
                            arcpy.Delete_management(join(workspace,"somspace.txt"))
                            arcpy.Delete_management(join(workspace,"geospace.txt"))
                            arcpy.Delete_management(join(workspace,"SOM.lrn"))
                            arcpy.Delete_management(join(workspace,"SOM.xml"))
                        else:
                            pass    
                    else:
                        arcpy.AddMessage("File 'umatrix' was not created.")
                        pass    
                else:
                    arcpy.AddMessage("File 'SOM_cluster' was not created.")
                    pass
            else:
                arcpy.AddMessage("File 'quant_error' was not created.")
                pass
        else:
            arcpy.AddMessage("File 'Geo_cluster' was not created.")
            pass
    else:
        arcpy.AddMessage ("The resolution or the projection of input files doesn't fit together")
        pass
    
    return None


try:
    # Check application running from ArcCatalog doesn't work and is not allowed

    app = os.path.basename(sys.executable)
    if app == "ArcCatalog.exe":
        raise ApplicationError
    
    # Abfrage der ArcGis Version
    v = arcpy.GetInstallInfo()['Version']
    if v != "10.6.1":
        raise VersionError
        

    # input 
    workspace = arcpy.GetParameterAsText(0) 
    input_raster = arcpy.GetParameterAsText(1)      # multiple value

    cellsize_x = arcpy.GetParameterAsText(2)        # number of cells in x-direction
    cellsize_y = arcpy.GetParameterAsText(3)        # number of cells in y-direction
    num_epochs = arcpy.GetParameterAsText(4)

    min_num_clusters = arcpy.GetParameterAsText(5)  # default 2, 
    max_num_clusters = arcpy.GetParameterAsText(6)  # default 25
    num_initital_centroids = arcpy.GetParameterAsText(7) # default 5

    map_type = arcpy.GetParameterAsText(8)             # toroid or planar
    grid_shape = arcpy.GetParameterAsText(9)           # rectangular or hexagonal

    is_checked_del = arcpy.GetParameterAsText(10)      # delete intermediate results

    inits = arcpy.GetParameterAsText(11)               # random or pca
    neigh_func = arcpy.GetParameterAsText(12)          # gaussian or bubble
    Gaussian_coeff = arcpy.GetParameterAsText(13)      # 0.5

    initial_neigh = arcpy.GetParameterAsText(14)       # 0
    final_neigh = arcpy.GetParameterAsText(15)         # 1
    radius_cooling = arcpy.GetParameterAsText(16)      # linear or exponential

    initial_trainingrate = arcpy.GetParameterAsText(17)# 0.1
    final_trainingrate = arcpy.GetParameterAsText(18)  # 0.01
    scale_cooling = arcpy.GetParameterAsText(19)       # linear or exponential

    # paths
    #path_to_Mainfolder = r"\\vs-daten\Projekte\2018\0051-0100\20180096_Praktikum_Softwareentwicklung\Andreas\NEXT\ArcGIS_SOM\Som_clustering_toolbox0910\Coding"
    path_to_Mainfolder = os.path.dirname(os.path.abspath(__file__))
    path_to_Run_CreateSOMLrnFile = join(path_to_Mainfolder, r"Release_CreateSOM_LrnFile\Run_CreateSOMLrnFile.exe")
    path_to_nextsom_wrap = join(path_to_Mainfolder, r"nextsom_wrap_neu\nextsom_wrap.exe")
    path_to_CreateSomResultRaster = join(path_to_Mainfolder,r"Release_CreateSOMResultRaster\CreateSOMResultRaster.exe")
    path_to_EmptyLayer = join(path_to_Mainfolder,r"EmptyLayer.lyr")
    path_to_ColorSource = join(path_to_Mainfolder,r"ColorSource.lyr")

    # hides cmd windows when running external process
    sinfo = subprocess.STARTUPINFO()
    sinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW #si.wShowWindow = subprocess.SW_HIDE # default

    # runs process
    check_data_and_run()

except ApplicationError:
        msg = "Please do ONLY use ArcMap as tool's execution application."
        arcpy.AddMessage(' ')
        arcpy.AddError(msg)
        arcpy.AddMessage(' ')

except VersionError:
    msg = "SOM toolbox requires ArcGIS 10.6.1."
    arcpy.AddMessage(' ')
    arcpy.AddMessage(msg)
    arcpy.AddMessage(' ')
