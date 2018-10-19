"""
This script downloads ADCIRC+SWAN data from a specific node and date supplied
by the user

Michael Itzkin, 9/7/2018
"""

import functions as func
import csv


# Print out an intro to the console
func.intro_prompt()

# Set the dates, nodes, time zone, and datum to use
Start_date, Start_date_dt, End_date, End_date_dt, use_gmt, use_navd88, nodes_used = func.make_date_range()

# Keep a running log of any date that didn't work. This file appends dates that don't work
# if a dat works than nothing happens with it
bad_dates_log_fname = 'bad_dates_log.txt'
bad_dates_log = open(bad_dates_log_fname, 'a')

# Setup and open a .csv file to write data to. Add a header to the columns
# for the first node
date_file_fname = func.make_data_filename(Start_date, use_gmt, use_navd88, ext='csv')
with open(date_file_fname, 'w+') as adcirc_file:
    writer = csv.writer(adcirc_file, delimiter=',')
    writer.writerow(['Date', 'Depth', 'Elevation', 'Max Hs', 'Tp', 'Deep Node Lon', 'Deep Node Lat'])

    # Lood through every day in the range of dates used. Note that the start and end dates are returned as
    # a string type (*_date) and a datetime object (*_date_dt). Pass the datetime object to this loop
    for date in func.daterange(Start_date_dt, End_date_dt):
    
        # Convert the date into a string from a datetime object.
        # Format: yyyymmdd
        date = date.strftime('%Y%m%d')
    
        # Set a list of the hours to loop through. For every day in the
        # date range, this program will try to download the data for
        # every hour in this list. You can try adding new times;
        # Separate the values with a comma and put them in quotes
        hours = ['00', '06', '12', '18']
        for hour in hours:
    
            # Add the hour to the date string.
            # New Format: yyyymmddhh
            date += hour
        
            # Write a header row for the .csv file. The "depth", "Max Hs",
            # and "Tp" columns are repeated for every well but the header will
            # only print for the first one
        
            # Download the data
            hs_data, tp_data, z_data, status, grid = func.adcirc_full_data_download(date)
        
            # Before downloading the forecast data, check if a nowcast
            # exists for the current date. If so, collect the nowcast
            # data first before collecting the forecast data
            if func.find_nowcast(date):
                func.download_nowcast_data_known_node(date, nodes_used, writer, bad_dates_log, use_gmt, use_navd88)

            # Clear the hour from the date string
            # Return to: yyyymmdd
            date = date[:-2]
            
# Close the ADCIRC .csv file and the bad_dates_log.txt file and then print
# closing messages to the console
bad_dates_log.close()
adcirc_file.close()
print('\r\n\r\nData is finished downloading')
print('Data was stored in the file: %s\r\n' % date_file_fname)