"""
This script downloads ADCIRC+SWAN data from a specific node and date supplied
by the user

Michael Itzkin, 9/7/2018
"""

import functions as func
#import plots as plot
import datetime as dt
import csv


# Print out an intro to the console
func.intro_prompt()

# Set the date to retrieve data for. This is set through the command line as
# user input values. Follow the prompts onscreen
date, use_gmt, use_navd88, nodes_used = func.set_date(known_node=True)

# Keep a running log of any date that didn't work. To do this, open up the
# "bad_dates_log.txt" file in append mode (note that the open function has a "a"
# argument instead of "w+"). This allows the program to add a new date to the log
# without erasing what is already there. If the date you are working with works than
# nothing will happen with this file, if the date doesn't work than it will get
# written to the file.
bad_dates_log_fname = 'bad_dates_log.txt'
bad_dates_log = open(bad_dates_log_fname, 'a')

date_file_fname = func.make_data_filename(date, use_gmt, use_navd88, ext='csv')
with open(date_file_fname, 'w+') as adcirc_file:
    writer = csv.writer(adcirc_file, delimiter=',')

    # Write a header row for the .csv file. The "depth", "Max Hs",
    # and "Tp" columns are repeated for every well but the header will
    # only print for the first one
    writer.writerow(['Date', 'Depth', 'Elevation', 'Max Hs', 'Tp', 'Deep Node Lon', 'Deep Node Lat'])

    # Download the data
    hs_data, tp_data, z_data, status, grid = func.adcirc_full_data_download(date)

    # Before downloading the forecast data, check if a nowcast
    # exists for the current date. If so, collect the nowcast
    # data first before collecting the forecast data
    if func.find_nowcast(date):
        func.download_nowcast_data_known_node(date, nodes_used, writer, bad_dates_log, use_gmt, use_navd88)

    if status == 'good':

        x = hs_data['x']
        y = hs_data['y']
        time = hs_data['time']

        # Setup the time
        base_time_dt = func.get_model_base_time(hs_data)

        # Loop through every time step and record the value of that
        # variable at the current time
        for t in range(len(time)):

            # Calculate the "real" time from the model
            real_time, real_time_str = func.get_real_time(base_time_dt, time[t], use_gmt)

            # Print the current time step being worked on
            # Print the current time step being worked on
            if use_gmt:
                print('Currently working on forecast time step %d of %d (Real time: %s GMT)' %
                      (t + 1, len(time), real_time))
            else:
                print('Currently working on forecast time step %d of %d (Real time: %s EST)' %
                      (t + 1, len(time), real_time))

            # Grab data from the node
            Hs, swan_TPS, depth, elev, X, Y = [], [], [], [], [], []
            for node in nodes_used:
                Hs.append(hs_data['swan_HS'][t][node])
                swan_TPS.append(tp_data['swan_TPS'][t][node])
                depth.append(hs_data['depth'][node])
                elev.append(z_data['zeta'][t][node])
                X.append(x[node])
                Y.append(y[node])

            if t != 0:
                time_step = dt.timedelta(hours=1)
                date = dt.datetime.strptime(date, '%Y%m%d%H')
                date += time_step
                date = date.strftime('%Y%m%d%H')

            line = []
            line.append(real_time_str)
            for node in range(len(nodes_used)):

                # Convert the values to NAVD88 if desired
                msl_to_navd88 = 0.118  # Meters
                if use_navd88:
                    line.append(depth[node] + msl_to_navd88)
                    line.append(elev[node] + msl_to_navd88)
                    line.append(Hs[node] + msl_to_navd88)
                    line.append(swan_TPS[node])
                    # Add new variable here as "line.append(___[node])"
                    line.append(X[node])
                    line.append(Y[node])
                else:
                    line.append(depth[node])
                    line.append(elev[node])
                    line.append(Hs[node])
                    line.append(swan_TPS[node])
                    # Add new variable here as "line.append(___[node])"
                    line.append(X[node])
                    line.append(Y[node])

            writer.writerow(line)

    elif status != 'good':
        # Print the current date and status to the console
        print('ERROR: Could not load date for %s\r\n' % date)
        log_line = '\r\n' + date + '\tCould not load forecast data'
        bad_dates_log.write(log_line)
        print('Date stored in bad_dates_log.txt\r\n')\

    # Clear the hour from the date string
    # Return to: yyyymmdd
    date = date[:-2]

# Close the ADCIRC .csv file and the bad_dates_log.txt file and then print
# closing messages to the console
func.finish_prompt(status, date_file_fname, bad_dates_log, adcirc_file)