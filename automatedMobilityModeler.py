# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# AutomatedMobilityModeler.py
# Created by: Eric W. Adams
# Version and Date: 1.4 - last updated 28 March 2022
# Usage: Deteremine mobility through automated analysis - educational use only. 
# Description: 
# Generate Mobility Assessment from various input layers and user input.
# ---------------------------------------------------------------------------

# Import arcpy module
import arcpy

# Set environment settings
arcpy.env.overwriteOutput = True


arcpy.AddMessage("Beginning the processing of automated mobility...")
print(arcpy.GetMessages())
try: 
    # Collect and set user inputs
    Buffer_Distance = arcpy.GetParameterAsText(0)
    slp_min = arcpy.GetParameterAsText(1)
    slp_max = arcpy.GetParameterAsText(2)

    # SQL Statement
    SQL = "gridcode >= {:s} AND gridcode <= {:s}".format(slp_min,slp_max) # provide a default value if unspecified

    # Local variables:
    arcpy.AddMessage("Setting all variables..")
    print "Setting local variables....\n"
    SLP_GridCoded = r"C:\Users\ewadams\AppData\Roaming\ESRI\Desktop10.8\ArcCatalog\as_ewadams.sde\ewadams_capstone.ewadams.slp_with_gridcode"
    Selected_SLP_Out = "%SCRATCHWORKSPACE%\\slp_Select.shp"
    Roads = r"C:\Users\ewadams\AppData\Roaming\ESRI\Desktop10.8\ArcCatalog\as_ewadams.sde\ewadams_capstone.ewadams.roads"
    Buffer_Out = "%SCRATCHWORKSPACE%\\roads_Buffer.shp"
    Sel__SLP_Clip_Out = "%SCRATCHWORKSPACE%\\slp_Clip.shp"
    soils =  r"C:\Users\ewadams\AppData\Roaming\ESRI\Desktop10.8\ArcCatalog\as_ewadams.sde\ewadams_capstone.ewadams.soils_clip"
    Selected_Soils_Out = "%SCRATCHWORKSPACE%\\soils_clip_Select.shp"
    Sel__Soils_Clip_Out = "%SCRATCHWORKSPACE%\\soils_clip.shp"
    SLP_Soil_Intersect_Out = "%SCRATCHWORKSPACE%\\slp_soil_intersect.shp"
    Hydro_Area =  r"C:\Users\ewadams\AppData\Roaming\ESRI\Desktop10.8\ArcCatalog\as_ewadams.sde\ewadams_capstone.ewadams.hydro_area"
    SLP_Soil_Int_Final = "%SCRATCHWORKSPACE%\\slp_soil_int_final.shp"
    veg =  r"C:\Users\ewadams\AppData\Roaming\ESRI\Desktop10.8\ArcCatalog\as_ewadams.sde\ewadams_capstone.ewadams.vegetation"
    Veg_Clip_Out = "%SCRATCHWORKSPACE%\\vegetation_Clip.shp"
    Veg_Erased_by_Hydro = "%SCRATCHWORKSPACE%\\hydro_erased_veg.shp"
    Final = "%SCRATCHWORKSPACE%\\final.shp"

    # Process: Buffer
    arcpy.AddMessage("Processing the buffer...")
    arcpy.Buffer_analysis(Roads, Buffer_Out, Buffer_Distance, "FULL", "ROUND", "ALL", "", "PLANAR")

    # Process: Select Soils
    arcpy.AddMessage("Processing the soils selection...")
    arcpy.Select_analysis(soils, Selected_Soils_Out, "soil_code IN( 'Fair' , 'Good' )")

    # Process: Clip Soils
    arcpy.AddMessage("Processing of clipping the soils...")
    arcpy.Clip_analysis(Selected_Soils_Out, Buffer_Out, Sel__Soils_Clip_Out, "0.1 Meters")

    # Process: Select Slope
    arcpy.AddMessage("Processing the slope selection based on user inputs...")
    arcpy.Select_analysis(SLP_GridCoded, Selected_SLP_Out, SQL)

    # Process: Clip SLP
    arcpy.AddMessage("Processing clipping the slope...")
    arcpy.Clip_analysis(Selected_SLP_Out, Buffer_Out, Sel__SLP_Clip_Out, "0.1 Meters")

    # Process: Clip Veg
    arcpy.AddMessage("Processing clipping the vegetation...")
    arcpy.Clip_analysis(veg, Buffer_Out, Veg_Clip_Out, "0.1 Meters")

    # Process: Hydro Erases Veg
    arcpy.AddMessage("Erasing the hydrology areas with the vegetation...")
    arcpy.Erase_analysis(Veg_Clip_Out, Hydro_Area, Veg_Erased_by_Hydro, "0.1 Meters")

    # Process: Soil and SLP Intersect
    arcpy.AddMessage("Intersection of the slope and soils layers...")
    arcpy.Intersect_analysis("%SCRATCHWORKSPACE%\\slp_Clip.shp #;%SCRATCHWORKSPACE%\\soils_clip.shp #", SLP_Soil_Intersect_Out, "ALL", "0.1 Meters", "INPUT")

    # Process: Erase SLP with Hydro
    arcpy.AddMessage("Erasing slope with hydrology areas...")
    arcpy.Erase_analysis(SLP_Soil_Intersect_Out, Hydro_Area, SLP_Soil_Int_Final, "0.1 Meters")

    # Process: Erase Soil Slp with Veg
    arcpy.AddMessage("Erasing the soils with the vegetation layer...")
    arcpy.Erase_analysis(SLP_Soil_Int_Final, Veg_Erased_by_Hydro, Final, "0.1 Meters")

    # Process: Add Field
    arcpy.AddMessage("Adding the field 'mobCode'...")
    arcpy.AddField_management(Final, "mobCode", "TEXT", "", "", "12", "", "NULLABLE", "NON_REQUIRED", "")

    # Field assignment
    fields = ['gridcode', 'soil_code', 'mobCode']

    # Process: Calculate Field using UpdateCursor
    arcpy.AddMessage("Calculating the mobCode field based on conditions...")
    with arcpy.da.UpdateCursor(Final, fields) as cursor:
        for row in cursor:
            if row[0] >0 and row[0] <=15 and row[1] == 'Good':
                row[2] = 'Go'
                cursor.updateRow(row)
            elif row[0] >15 and row[0] <45 and row[1] == 'Good':
                row[2] = 'Slow Go'
                cursor.updateRow(row)
            elif row[0] >0 and row[0] <=15 and row[1] == 'Fair':
                row[2] = 'Slow Go'
                cursor.updateRow(row)
            elif row[0] >15 and row[0] <45 and row[1] == 'Fair':
                row[2] = 'No Go'
                cursor.updateRow(row)
            elif row[0] >45:
                row[2] = 'No Go'
                cursor.updateRow(row)
            else:
                row[2] = 'No Go'
                cursor.updateRow(row)

    arcpy.AddMessage("Processing as completed.")
        
    # Set output FC
    OutLayer = "%SCRATCHWORKSPACE%\\final.shp"

    # Make a feature layer to apply symbology to
    flayer = arcpy.MakeFeatureLayer_management(OutLayer, "mobility_lyr")

    # Apply symbology to the output
    layerFile = r"C:\EWADAMS_Capstone\Scratch\final.lyr"
    finalOut = arcpy.ApplySymbologyFromLayer_management(flayer, layerFile)
    arcpy.SetParameter(3,finalOut) # creates the parameter to display via script tool
except:
    print("There was an error. Please contact the developer.")
