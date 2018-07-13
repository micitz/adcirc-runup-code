"""
Download ADCIRC+SWAN ouput from a selected date range and store the maximum
values for the desired variables

Michael Itzkin, 2/21/2018
"""

import functions as func
#import plots as plot
import datetime as dt
import csv 

# Create a .txt file with the dates that didn't work in it.
bad_dates_file = open('bad_dates.txt', 'w+')
bad_date_count = 0

date_file = 'adcirc_output_data.csv'
with open(date_file, 'w', newline='') as adcirc_file:
    writer=csv.writer(adcirc_file, delimiter=',')

    # Write a header row for the .csv file. The "depth", "Max Hs",
    # and "Tp" columns are repeated for every well but the header will
    # only print for the first one
    writer.writerow(['Date', 'Depth', 'Elevation', 'Max Hs', 'Tp', 'Node Lon', 'Node Lat'])

    # Load the bounding box. You can change the bounding box by
    # going to this function in "functions.py" and changing the
    # values there
    bottom_lat, upper_lat, left_lon, right_lon = func.load_bounding_box()

    # Set the start and end date
    # YOU CAN CHANGE THE VALUES IN THESE FUNCTION CALLS!!
    # Format: dt.date(YYYY, mm, dd)
    start_date = dt.date(2017,4,30)     # Default: 2017,4,30
    end_date = dt.date(2018,5,4)        # Default: 2018,5,4
    
    for date in func.daterange(start_date, end_date):

        # Convert the date into a string from a datetime object.
        # Format: yyymmdd
        date=date.strftime('%Y%m%d')

        # Set a list of the hours to loop through. For every day in the
        # date range, this program will try to download the data for
        # every hour in this list. You can try adding new times;
        # Separate the values with a comma and put them in quotes
        hours = ['00', '12']
        for hour in hours:

            # Add the hour to the date string.
            # New Format: yyyymmddhh
            date += hour

            # Download the data
            hs_data, tp_data, z_data, status = func.adcirc_data_download(date)
            
            if status == 'good':

                # Print the date and status to the console
                print('Current Date: %s (Status = %s)' % (date, status))
        
                x = hs_data['x']
                y = hs_data['y']

                # Narrow down the lat/lon
                start, end = func.find_search_indexes(left_lon, right_lon, x)
                x, y = func.x_y_refine(x, y, start, end)

                # Download the appropriate Hs,TPS, depth values.
                # The indexes where the netCDF is using the "nc6b" url
                # path returns the start and end indexes in reverse order
                # so swap them here
                if start > end:
                    max_Hs = hs_data['swan_HS_max'][end:start]
                    swan_TPS_max = tp_data['swan_TPS_max'][end:start]
                    depth = hs_data['depth'][end:start]
                    elev = z_data['zeta_max'][end:start]
                    # Put in vew variable here "end:start"
                elif start <= end:
                    max_Hs = hs_data['swan_HS_max'][start:end]
                    swan_TPS_max = tp_data['swan_TPS_max'][start:end]
                    depth = hs_data['depth'][start:end]
                    elev = z_data['zeta_max'][start:end]
                    # Put in new variable here "start:end"

                #find 20m contour nodes, 20m is standard 
                contour = 20 #this value can be changed 
                use_depths, use_indexes = func.deep_water_nodes(depth, contour)
                max_Hs = max_Hs[use_indexes]
                swan_TPS_max = swan_TPS_max[use_indexes]
                max_elev = elev[use_indexes]
                nodes_used=func.finding_well_points(use_indexes, x, y)
                # Add new variable here-just copy and change variable names
            
                line=[]
                line.append(date)
                for node in nodes_used:
                    line.append(depth[node])
                    line.append(max_elev[node])
                    line.append(max_Hs[node])
                    line.append(swan_TPS_max[node])
                    # Add new variable here as "line.append(___[node])"
                    line.append(x[node])
                    line.append(y[node])

                    
                writer.writerow(line)
            
            elif status!='good':
                # Print the current date and status to the console
                print('Current Date: %s (Status = %s)' % (date, status))

                bad_dates_file.write('%s fail \r\n'%(date))
                bad_date_count+=1
                line=[]
                line.append(date)
                for node in nodes_used:
                    line.append(0)
                    line.append(0)
                    line.append(0)
                    line.append(0)
                    line.append(0)
                    line.append(0)
                    #add new variable as "line.append(0)"
                    
                writer.writerow(line)

            # Clear the hour from the date string
            # Return to: yyyymmdd
            date=date[:-2]

# At the end of the data collection, write the total amount of bad dates
# at the end of the .txt file
bad_dates_file.write('\r\ntotal %d'%(bad_date_count))

# Close the ADCIRC .csv file and the bad dates .txt file and then print
# "done" to the console
adcirc_file.close()
bad_dates_file.close()
print('done')
       
        







