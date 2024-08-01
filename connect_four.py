import arcpy
import os

# Set up environment
arcpy.env.overwriteOutput = True

# Get parameters
input_shapefile = arcpy.GetParameterAsText(0)  # Input Shapefile
output_shapefile = arcpy.GetParameterAsText(1)  # Output Shapefile

def points_to_lines(input_shapefile, output_shapefile):
    """
    Convert groups of four points to lines
    """
    try:
        # Create a new feature class for the output lines
        spatial_ref = arcpy.Describe(input_shapefile).spatialReference
        arcpy.management.CreateFeatureclass(os.path.dirname(output_shapefile), os.path.basename(output_shapefile), "POLYLINE", spatial_reference=spatial_ref)
        
        # Add necessary fields to the output feature class if needed
        arcpy.management.AddField(output_shapefile, "LineID", "LONG")
        
        # Create a cursor to insert new line features
        line_cursor = arcpy.da.InsertCursor(output_shapefile, ["LineID", "SHAPE@"])
        
        # Create a search cursor to iterate through the input points
        point_cursor = arcpy.da.SearchCursor(input_shapefile, ["SHAPE@XY"])
        
        points = []
        line_id = 1
        for row in point_cursor:
            point = arcpy.Point(row[0][0], row[0][1])
            points.append(point)
            # When we have four points, create a line
            if len(points) == 4:
                array = arcpy.Array(points)
                line = arcpy.Polyline(array, spatial_ref)
                line_cursor.insertRow([line_id, line])
                points = []
                line_id += 1
        
        del line_cursor
        del point_cursor

        arcpy.AddMessage(f"Points to Line operation completed. Output saved at {output_shapefile}")

    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as ex:
        arcpy.AddError(f"An error occurred: {str(ex)}")

try:
    # Execute the function
    points_to_lines(input_shapefile, output_shapefile)

except ValueError as ve:
    arcpy.AddError(f"Input Error: {ve}")
except arcpy.ExecuteError:
    arcpy.AddError(arcpy.GetMessages(2))
except Exception as ex:
    arcpy.AddError(f"An error occurred: {str(ex)}")
