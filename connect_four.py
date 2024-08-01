import arcpy
import os
import numpy as np

# Set up environment
arcpy.env.overwriteOutput = True

# Get parameters
input_shapefile = arcpy.GetParameterAsText(0)  # Input Shapefile
output_shapefile = arcpy.GetParameterAsText(1)  # Output Shapefile

def points_to_lines(input_shapefile, output_shapefile):
    """
    Convert groups of four points to lines and calculate average and standard deviation of Bottom AC Depth
    """
    try:
        # Create a new feature class for the output lines
        spatial_ref = arcpy.Describe(input_shapefile).spatialReference
        arcpy.management.CreateFeatureclass(os.path.dirname(output_shapefile), os.path.basename(output_shapefile), "POLYLINE", spatial_reference=spatial_ref)
        
        # Add necessary fields to the output feature class
        arcpy.management.AddField(output_shapefile, "LineID", "LONG")
        arcpy.management.AddField(output_shapefile, "AvgACDepth", "DOUBLE")
        arcpy.management.AddField(output_shapefile, "StdACDepth", "DOUBLE")
        
        # Create a cursor to insert new line features
        line_cursor = arcpy.da.InsertCursor(output_shapefile, ["LineID", "SHAPE@", "AvgACDepth", "StdACDepth"])
        
        # Create a search cursor to iterate through the input points
        fields = ["SHAPE@XY", "Bottom_AC_Depth__in__"]
        point_cursor = arcpy.da.SearchCursor(input_shapefile, fields)
        
        points = []
        depths = []
        line_id = 1
        for row in point_cursor:
            point = arcpy.Point(row[0][0], row[0][1])
            depth = row[1]
            points.append(point)
            depths.append(depth)
            
            # When we have four points, create a line and calculate statistics
            if len(points) == 4:
                array = arcpy.Array(points)
                line = arcpy.Polyline(array, spatial_ref)
                
                arcpy.AddMessage(f"\n\nProcessing Line {line_id}\n")
                arcpy.AddMessage(f"Depth values: {depths}\n")
                
                # Filter out None values for calculations
                valid_depths = [d for d in depths if d is not None]
                
                if valid_depths:
                    avg_depth = np.mean(valid_depths)
                    arcpy.AddMessage(f"Average depth calculation:")
                    arcpy.AddMessage(f"Sum of depths: {sum(valid_depths)}")
                    arcpy.AddMessage(f"Number of valid depths: {len(valid_depths)}")
                    arcpy.AddMessage(f"Average depth: {sum(valid_depths)} / {len(valid_depths)} = {avg_depth}\n")
                    
                    if len(valid_depths) > 1:
                        # Calculate standard deviation
                        squared_diff = [(d - avg_depth)**2 for d in valid_depths]
                        arcpy.AddMessage(f"Squared differences from mean:")
                        for i, diff in enumerate(squared_diff):
                            arcpy.AddMessage(f"  Point {i+1}: ({valid_depths[i]} - {avg_depth})^2 = {diff}")
                        
                        mean_squared_diff = np.mean(squared_diff)
                        arcpy.AddMessage(f"\nMean of squared differences: {mean_squared_diff}")
                        
                        std_depth = np.sqrt(mean_squared_diff)
                        arcpy.AddMessage(f"Standard deviation: sqrt({mean_squared_diff}) = {std_depth}\n")
                    else:
                        std_depth = 0
                        arcpy.AddMessage("Only one valid depth value, standard deviation set to 0\n")
                else:
                    avg_depth = None
                    std_depth = None
                    arcpy.AddMessage("No valid depth values for this line\n")
                
                line_cursor.insertRow([line_id, line, avg_depth, std_depth])
                
                points = []
                depths = []
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
