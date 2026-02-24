import math
import json
from urllib.request import Request, urlopen
import fnmatch

# default vars
g_total_val = 0

# Fetch data from dynmap marker_new.json marker as dataset
print("Fetching data...")
request = Request('https://dynmap.minecartrapidtransit.net/main/tiles/_markers_/marker_new.json')
response = urlopen(request)
data = json.loads(response.read().decode("utf-8"))
print("Done.\n")


# Input category available
category = input(f"Input a valid category without quotations. Available options are listed below:\n{list(data['sets'].keys())}\n")

search = input(f"Input line(s) to be measured.\nIf you want to measure multiple categories together, input an asterisk at the end to get all that match (Example: b80-*). For all markers, input '*'.\n\nCategories available: {list(data['sets'][category]['lines'].keys())}\n")

# assume * if search is empty
if search == "":
    print("empty")

# Get all coordinates of all drawn lines
road_label = [data['sets'][category]['lines']][0]
road_coords = [data['sets'][category]['lines']]

# Get list containing only matching strings
filtered_list = fnmatch.filter(road_label, search)

# Main Loop
for l in filtered_list:
    # reset default coords
    coord_list = []; list_calc = []; total_val = 0

    # Get x and z coords of line
    x_coords = road_coords[0][l]['x']
    z_coords = road_coords[0][l]['z']

    # Append rounded coordinates into coodinates list
    for x in range(0, len(x_coords)):
        coord_list.append([(math.floor(x_coords[x])), (math.floor(z_coords[x]))])

    # Calculate utilizing pythagorean theorem from coord_list#1 to coord_list#2, then 2 -> 3, etc.
    # Append into list_calc when done
    for i in range(0, len(x_coords) + 1):
        try:
            coord_calc = ((coord_list[0 + i][0] - coord_list[1 + i][0]) ** 2) + (
                    (coord_list[0 + i][1] - coord_list[1 + i][1]) ** 2)
            list_calc.append(math.sqrt(coord_calc))
        except:
            pass

    # Add all of list_calc together for final marker distance
    for d in range(0, len(list_calc) + 1):
        try:
            total_val += list_calc[0 + d]
            total_val = math.floor(total_val)
        except:
            pass

    # (Optional) Print line result
    print(f'Distance of {l}: {total_val}m')

    # Add result to grand total
    g_total_val += total_val

# Print grand total result:
print(f'Total Distance of {search}: {g_total_val}m\n')

# Do not immediately quit, halting input
wait = input("Press any key to exit...")