import arcpy
import os
import numpy as np

# Set up environment
arcpy.env.overwriteOutput = True

# Get parameters
input_shapefile = arcpy.GetParameterAsText(0)  # Input Shapefile
output_shapefile = arcpy.GetParameterAsText(1)  # Output Shapefile

def create_output_feature_class(output_shapefile, spatial_ref):
    """Create the output feature class with necessary fields"""
    arcpy.management.CreateFeatureclass(os.path.dirname(output_shapefile), os.path.basename(output_shapefile), "POLYLINE", spatial_reference=spatial_ref)
    arcpy.management.AddField(output_shapefile, "LineID", "LONG")
    arcpy.management.AddField(output_shapefile, "AvgACDepth", "DOUBLE")
    arcpy.management.AddField(output_shapefile, "StdACDepth", "DOUBLE")

def process_group(points, depths, line_id, line_cursor, spatial_ref):
    """Process a group of points, create a line, and calculate statistics"""
    array = arcpy.Array(points)
    line = arcpy.Polyline(array, spatial_ref)
    
    arcpy.AddMessage(f"\nProcessing Line {line_id}")
    arcpy.AddMessage(f"Number of points: {len(points)}")
    arcpy.AddMessage(f"Depth values: {depths}")
    
    valid_depths = [d for d in depths if d is not None]
    
    if valid_depths:
        avg_depth = np.mean(valid_depths)
        arcpy.AddMessage(f"Average depth: {avg_depth}")
        
        if len(valid_depths) > 1:
            std_depth = np.std(valid_depths)
            arcpy.AddMessage(f"Standard deviation: {std_depth}")
        else:
            std_depth = 0
            arcpy.AddMessage("Only one valid depth value, standard deviation set to 0")
    else:
        avg_depth = None
        std_depth = None
        arcpy.AddMessage("No valid depth values for this line")
    
    line_cursor.insertRow([line_id, line, avg_depth, std_depth])

def handle_remaining_points(remaining_points, last_processed_point, line_id, line_cursor, spatial_ref):
    """Handle the remaining points that don't make a full group"""
    if remaining_points:
        points = [arcpy.Point(last_processed_point[0][0], last_processed_point[0][1])] + [arcpy.Point(row[0][0], row[0][1]) for row in remaining_points]
        depths = [last_processed_point[1]] + [row[1] for row in remaining_points]
        process_group(points, depths, line_id, line_cursor, spatial_ref)

def points_to_lines(input_shapefile, output_shapefile):
    """Convert groups of four points to continuous lines with overlapping"""
    try:
        spatial_ref = arcpy.Describe(input_shapefile).spatialReference
        create_output_feature_class(output_shapefile, spatial_ref)
        
        line_cursor = arcpy.da.InsertCursor(output_shapefile, ["LineID", "SHAPE@", "AvgACDepth", "StdACDepth"])
        
        fields = ["SHAPE@XY", "Bottom_AC_Depth__in__"]
        with arcpy.da.SearchCursor(input_shapefile, fields) as point_cursor:
            all_points = list(point_cursor)
        
        line_id = 1
        last_processed_point = None
        for i in range(0, len(all_points) - 3, 3):
            group = all_points[i:i+4]
            points = [arcpy.Point(row[0][0], row[0][1]) for row in group]
            depths = [row[1] for row in group]
            
            process_group(points, depths, line_id, line_cursor, spatial_ref)
            line_id += 1
            last_processed_point = group[-1]

        handle_remaining_points(all_points[i+3:], last_processed_point, line_id, line_cursor, spatial_ref)
        
        del line_cursor
        arcpy.AddMessage(f"Points to Line operation completed. Output saved at {output_shapefile}")
    except arcpy.ExecuteError:
        arcpy.AddError(arcpy.GetMessages(2))
    except Exception as ex:
        arcpy.AddError(f"An error occurred: {str(ex)}")

try:
    points_to_lines(input_shapefile, output_shapefile)
except ValueError as ve:
    arcpy.AddError(f"Input Error: {ve}")
except arcpy.ExecuteError:
    arcpy.AddError(arcpy.GetMessages(2))
except Exception as ex:
    arcpy.AddError(f"An error occurred: {str(ex)}")
