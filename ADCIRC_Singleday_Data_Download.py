"""
Download ADCIRC+SWAN ouput from a selected date and store the date for that day

Michael Itzkin, 5/7/2018
"""

import functions as func
#import plots as plot
import datetime as dt
import csv


# Print out an intro to the console
func.intro_prompt()

# Set the date to retrieve data for. This is set through the command line as
# user input values. Follow the prompts onscreen
date, use_gmt, use_navd88 = func.set_date()

# Keep a running log of any date that didn't work. To do this, open up the
# "bad_dates_log.txt" file in append mode (note that the open function has a "a"
# argument instead of "w+"). This allows the program to add a new date to the log
# without erasing what is already there. If the date you are working with works than
# nothing will happen with this file, if the date doesn't work than it will get
# written to the file.
bad_dates_log_fname = 'bad_dates_log.txt'
bad_dates_log = open(bad_dates_log_fname, 'a')

date_file_fname = 'adcirc_one_run_output_data_(' + date + ').csv'
with open(date_file_fname, 'w+') as adcirc_file:
    writer=csv.writer(adcirc_file, delimiter=',')

    # Write a header row for the .csv file. The "depth", "Max Hs",
    # and "Tp" columns are repeated for every well but the header will
    # only print for the first one
    writer.writerow(['Date', 'Depth', 'Elevation', 'Max Hs', 'Tp', 'Deep Node Lon', 'Deep Node Lat'])

    # Load the bounding box. You can change the bounding box by
    # going to this function in "functions.py" and changing the
    # values there
    bottom_lat, upper_lat, left_lon, right_lon = func.load_bounding_box()

    # Download the data
    hs_data, tp_data, z_data, status, grid = func.adcirc_full_data_download(date)

    # Before downloading the forecast data, check if a nowcast
    # exists for the current date. If so, collect the nowcast
    # data first before collecting the forecast data
    if func.find_nowcast(date):
        func.download_nowcast_data(date, bottom_lat, upper_lat, left_lon, right_lon, writer,
                                   bad_dates_log, use_gmt, use_navd88)

    if status == 'good':

        x = hs_data['x']
        y = hs_data['y']
        time = hs_data['time']

        # Setup the time
        base_time_dt = func.get_model_base_time(hs_data)

        # Narrow down the lat/lon
        start, end = func.find_search_indexes(left_lon, right_lon, x)
        x, y = func.x_y_refine(x, y, start, end)

        # Loop through every time step and record the value of that
        # variable at the current time
        for t in range(len(time)):

            # Calculate the "real" time from the model
            real_time, real_time_str = func.get_real_time(base_time_dt, time[t], use_gmt)

            # Print the current time step being worked on
            # Print the current time step being worked on
            if use_gmt:
                print('Currently working on nowcast time step %d of %d (Real time: %s GMT)' %
                      (t + 1, len(time), real_time))
            else:
                print('Currently working on nowcast time step %d of %d (Real time: %s EST)' %
                      (t + 1, len(time), real_time))

            # Download the appropriate Hs,TPS, depth values.
            # The indexes where the netCDF is using the "nc6b" url
            # path returns the start and end indexes in reverse order
            # so swap them here.
            # In the multiday script, the data can be thought of as
            # a 2D vector (i.e; 1x*length*); Here, the data can be thought of as a matrix
            # where there is a row for every time step and a column for every node. So, to
            # find the right points here, not only are the nodes indexed "[start:end]" but
            # the time is also indexed as "[t]"
            if start > end:
                Hs = hs_data['swan_HS'][t][end:start]
                swan_TPS = tp_data['swan_TPS'][t][end:start]
                depth = hs_data['depth'][end:start]
                elev = z_data['zeta'][t][end:start]
                # Put in vew variable here "[t][end:start]"
                # If "IndexError: invalid index to scalar variable." then try removing the "[t]"
                #   since not all variables (i.e; Depth) do not change with time
            elif start <= end:
                Hs = hs_data['swan_HS'][t][start:end]
                swan_TPS = tp_data['swan_TPS'][t][start:end]
                depth = hs_data['depth'][start:end]
                elev = z_data['zeta'][t][start:end]
                # Put in new variable here "[t][start:end]"
                # If "IndexError: invalid index to scalar variable." then try removing the "[t]"
                #   since not all variables (i.e; Depth) do not change with time

            # Find the nodes at the defined contour. These can be changed. Technically mhw should be 0.34 not
            # -0.34 but the contour function will still search in that range, the negative sign works better with it
            deep_contour = -20   # Default = -20
            mhw_contour = -0.34  # Default = -0.34
            if grid == 'nc6b':

                # Get deep water data
                deep_contour *= -1
                use_depths, use_indexes = func.deep_water_nodes(depth, deep_contour)
                Hs = Hs[use_indexes]
                swan_TPS = swan_TPS[use_indexes]
                elev = elev[use_indexes]
                deep_nodes_used = func.finding_well_points(use_indexes, x, y)

            elif grid == 'hsofs':

                # Get deep water data
                deep_nodes_used = func.hsofs_node_find(x, y)

                # Every time step is one hour. Here, the date is adjusted
                # using the dt.timedelta function by setting the "t" value
                # being looped over to hours and then adding it to the date
                # The date is briefly converted back into a datetime object
                # to do this and then reconverted back into a string. The
                # if-statement (if t != 0) makes sure that the time is correct
            if t != 0:
                time_step = dt.timedelta(hours=1)
                date = dt.datetime.strptime(date, '%Y%m%d%H')
                date += time_step
                date = date.strftime('%Y%m%d%H')


            line = []
            line.append(real_time_str)
            for deep_node in deep_nodes_used:

                # Convert the values to NAVD88 if desired
                msl_to_navd88 = 0.118  # Meters
                if use_navd88:
                    line.append(depth[deep_node] + msl_to_navd88)
                    line.append(elev[deep_node] + msl_to_navd88)
                    line.append(Hs[deep_node] + msl_to_navd88)
                    line.append(swan_TPS[deep_node])
                    # Add new variable here as "line.append(___[node])"
                    line.append(x[deep_node])
                    line.append(y[deep_node])
                else:
                    line.append(depth[deep_node])
                    line.append(elev[deep_node])
                    line.append(Hs[deep_node])
                    line.append(swan_TPS[deep_node])
                    # Add new variable here as "line.append(___[node])"
                    line.append(x[deep_node])
                    line.append(y[deep_node])

            writer.writerow(line)

    elif status != 'good':
        # Print the current date and status to the console
        print('ERROR: Could not load date for %s\r\n' % date)
        log_line = '\r\n' + date + '\tCould not load forecast data'
        bad_dates_log.write(log_line)
        print('Date stored in bad_dates_log.txt\r\n')

    # Clear the hour from the date string
    # Return to: yyyymmdd
    date = date[:-2]

# Close the ADCIRC .csv file and the bad_dates_log.txt file and then print
# closing messages to the console
func.finish_prompt(status, date_file_fname, bad_dates_log, adcirc_file)

