"""
User created functions for the daily ADCIRC viewer scripts

Michael Itzkin, 2/21/2018
"""

import netCDF4 as nc
import numpy as np
import datetime as dt
from bs4 import BeautifulSoup
import requests
import haversine
import os
import time


def listFD(url):
    """
    Return folders from a URL

    https://stackoverflow.com/questions/11023530/python-to-list-http-files-and-directories
    """
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    return [url + '/' + node.get('href') for node in soup.find_all('a')]


def find_nearest(array, value):
    """
    Find the nearest value in an array

    https://stackoverflow.com/questions/2566412/find-nearest-value-in-numpy-array/2566508
    """
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx


def intro_prompt():
    """
    Print an introductory prompt to the command line
    """
    print('\r\n\r\nThis program downloads all the data for single ADCIRC run,')
    print('follow the prompts below:\r\n')


def set_date(known_node=False):
    """
    Have the user input the date and time to download data for
    """
    print('---------------------')
    Year = input('Enter the year (YYYY): ')
    Month = input('Enter the month (do not include a leading 0): ')
    Day = input('Enter the date (do not include a leading 0): ')
    Hour = input('Enter the hour (hh): ')
    date = dt.datetime(int(Year), int(Month), int(Day), int(Hour))
    date = date.strftime('%Y%m%d%H')
    print('---------------------')
    use_gmt = bool(input('Use GMT (T) or EST (F): '))
    use_navd88 = bool(input('Use NAVD88 (T) or MSL (F): '))

    if known_node:
        print('---------------------')
        nodes_used = []
        num_nodes = int(input('How many nodes to look at: '))
        for i in range(num_nodes):
            prompt = 'Enter node id ' + str(i+1) + ' of ' + str(num_nodes) + ': '
            node = input(prompt)
            nodes_used.append(int(node))    # Add 1 to match Python's indexing
        print('---------------------\r\n')
        return date, use_gmt, use_navd88, nodes_used
    else:
        print('---------------------\r\n')
        return date, use_gmt, use_navd88


def make_data_filename(date, gmt, navd, ext='csv'):
    """
    This function generates a filename to use
    for the current run using the ADCIRC run date,
    the time method (GMT/EST), and the vertical
    datum (MSL, NAVD88).

    The gmt and msl values should be passed as
    bools (true/false)

    The extension defaults to csv, this can be changed but
    really shouldn't
    """

    # Set the time method
    if gmt:
        time_val = 'GMT'
    else:
        time_val = 'EST'

    # Set the vertical datum
    if navd:
        vdatum = 'NAVD88'
    else:
        vdatum = 'MSL'

    # Construct the filename
    fname = 'adcirc_one_run_output_data_' +\
            date + '_' + time_val + '_' +\
            vdatum + '.' + ext

    return fname


def finish_prompt(status, date_file_fname, bad_dates_log, adcirc_file):
    """
    When the data is finished downloading, print out a message to the
    command line directing the user to the output files. Close the files
    regardless of status, print the messages only if the status was good
    """
    bad_dates_log.close()
    adcirc_file.close()

    if status == 'good':
        print('\r\n\r\nData is finished downloading')
        print('Data was stored in the file: %s\r\n' %(date_file_fname))


def make_adcirc_date():
    """
    Creates a date string in the right format to pass to the ADCIRC URL
    """
    #Prompt the user to input the date (not necessary for my dates)
    m = 8
    d = 3
    y = 2017
    h = 0

    # Print a warning message about bad dates
    print('\nWARNING: If there is an ADCIRC netCDF error, check the server')
    # Make all the inputs strings
    month = str(m)
    day = str(d)
    year = str(y)
    hour = str(h)

    # Make a title hour
    if hour == '0':
        title_hour = 'Midnight'
    elif hour == '12':
        title_hour = 'Noon'

    # Check that the inputs are all the right length
    if len(month) is 1:
        month = '0' + month
    if len(day) is 1:
        day = '0' + day
    if len(hour) is 1:
        hour = '0' + hour
    if len(year) is not 4:
        print('ERROR: Year must be four digits')

    # Make an "ADCIRC Date" and aa "Title Date"
    adcirc_date = year + month + day + hour
    title_date = month + '-' + day + '-' + year + ' (' + title_hour + ')'

    return adcirc_date, title_date


def load_bounding_box():
    """
    Loads the bounding box variables
    """

    bottom_lat = 32.942688  # 34.206229
    upper_lat = 35.377735  # 35.132368
    left_lon = -78.148505
    right_lon = -74.469147  # -75.245367
    #this can be changed if add onslow-make sure at 20m countour 
    #don't forget the negative sign 
    return bottom_lat, upper_lat, left_lon, right_lon


def adcirc_data_download(date):
    """
    Go into the OpenDAP server and get date for the specified date
    """
    url_1 = 'http://opendap.renci.org:1935/thredds/dodsC/daily/nam/'
    url_2 = '/hsofs/hatteras.renci.org/namhsofs/namforecast/swan_HS_max.63.nc'
    url_3 = '/hsofs/hatteras.renci.org/namhsofs/namforecast/swan_TPS_max.63.nc'
    url_4 = '/hsofs/hatteras.renci.org/namhsofs/namforecast/maxele.63.nc'
    # url_1= website
    # url_2= significant wave height (sawn_Hs_max)
    # url_3= peak period (swan_TPS_max)
    # url_4 = Elevation
    # add in URL from file if add new variable
    
    # trying to make earielr dates work-keep#
    # if date eariler than 8/3/2017 then will use these website links
    test_date=dt.datetime(2017, 8, 3, 00)
    cur_date=dt.datetime.strptime(date, "%Y%m%d%H")

    except_dates = [dt.datetime(2017,9,15,00)]

    # This is a list of dates that have an hsofs URL but come after the test_date. You can add/remove dates
    # from this list by adding another element (separate with a comma) to the list "dt.datetime(year,month,day,hour)"
    if cur_date<test_date and cur_date not in except_dates:
        url_2 = '/nc6b/hatteras.renci.org/dailyv6c/namforecast/swan_HS_max.63.nc'
        url_3 = '/nc6b/hatteras.renci.org/dailyv6c/namforecast/swan_TPS_max.63.nc'
        url_4 = '/nc6b/hatteras.renci.org/dailyv6c/namforecast/maxele.63.nc'
    
    tp_url = url_1 + date + url_3
    hs_url = url_1 + date + url_2
    z_url = url_1 + date + url_4
    #add new url for new variable here 

    try:
        # Return the dataset from the netCDF file
        hs_data = nc.Dataset(hs_url, 'r')
        tp_data = nc.Dataset(tp_url, 'r')
        z_data = nc.Dataset(z_url, 'r')
        status="good" 
        #add in new dataset here
        
    except IOError:
        hs_data=0
        tp_data=0
        z_data=0
        status="fail"
        #add new variable here and set equal to 0

    return hs_data, tp_data, z_data, status


def find_search_indexes(left_lon, right_lon, x):
    """
    Loop through the x and y coordinates and return the indexes for
    the first and last nodes in the study area
    """

    # Make arrays of the x and y values-easier to do math
    #finds nodes within your box
    #do not change 
    x_array = np.asarray(x)

    # Find the start index
    start_vals = abs(left_lon - x_array)
    start = np.nanmax(np.where(start_vals == np.nanmin(start_vals)))

    # Find the end index
    end_vals = abs(right_lon - x_array)
    end = np.nanmax(np.where(end_vals == np.nanmin(end_vals)))

    return start, end


def x_y_refine(x, y, start, end):
    """
    Take the x and y vectors and return only values between "start" and "end"
    """

    if start > end:
        temp = start
        start = end
        end = temp

    return x[start:end], y[start:end]


def deep_water_nodes(depths, contour):
    """ 
    Find nodes nearest to the indicated countour 
    """

    # Pad the contour by searching for all points within 0.5m. use_indexes will be the indexes of
    # the nodes at the contour, use_depths is the depths of the nodes at the contour.
    # You can change "low_pad" and "high_pad" but there is no real reason to
    low_pad = 0.5
    high_pad = 3
    search_low = contour - low_pad
    search_lower = contour - high_pad
    search_high = contour + low_pad
    search_higher = contour + high_pad
    use_depths = []
    use_indexes = []

    # Try looking for nodes within the +-0.5m range of the contour
    for i in range(1, len(depths)):
        if search_low < depths[i] < search_high:
            use_depths.append(depths[i])
            use_indexes.append(i)

    # If the provided lat/lon ranges do not contain any nodes at the
    # 20m contour, expand the contour range and try again
    if not use_depths:
        for i in range(1, len(depths)):
            if search_lower < depths[i] < search_higher:
                    use_depths.append(depths[i])
                    use_indexes.append(i)

    return use_depths, use_indexes


def finding_well_points_DEFUNCT(use_indexes, x, y):
    """
    Pulling lat long from csv file match every well location to the nearest node
    X = long Y = lat 
    """
    #gives closest node to lat long points
    well_long=[-76.552499,-76.496324]
    well_lat=[34.64928,34.661199]
    #If add new location - onslow- add extra data
    
    nodes_used=[]
    min_dists=[]
    for i in range(0, len(well_long)):
        temp_dist = []
        for j in range(1, len(use_indexes)):
            dist = np.sqrt((float(well_long[i]) - float(x[j])) ** 2
                           + (float(well_lat[i]) - float(y[j])) ** 2)
            temp_dist.append(dist)
        min_dist = min(temp_dist)
        min_dists.append(min_dist)

        # The temp_dist vector is equal in length to the number of ADCIRC
        # nodes in the study location. Loop through the temp_dist vector
        # until min_dist is found, the index of this match will be equal
        # to the number of the ADCIRC node to be used for the profile
        for j in range(0, len(temp_dist)):
            if temp_dist[j] == min_dist:
                nodes_used.append(j)
    
    return nodes_used


def finding_well_points(use_indexes, x, y):
    """
    Pulling lat long from csv file match every well location to the nearest node
    X = long Y = lat.

    Wells:
    1. Shackleford Banks (DIAG)
    2. South Core Banks (NS)
    """

    # Can add new well locations, put the lat and lon in the appropriate list below
    # CAN BE CHANGED !!
    well_long = [-76.552499, -76.496324]
    well_lat = [34.64928, 34.661199]

    # This list store the general shoreline orientation of the beach where the wells
    # are located. Make sure that this list is equal in number of items as well_long and
    # well_lat. The values should correspond to the wells (i.e; if the first well_lon and
    # well_lat is for Shackleford than the first orientation should be "DIAG", "NS" for Core)
    # CAN BE CHANGED !!
    orientation = ['DIAG', 'NS']

    min_dists = []
    nodes_used = []
    for i in range(0, len(well_long)):

        if orientation[i] == 'EW':
            # If the orientation is EW than match the node that has the closest x-coordinate
            # to that of the well. This function only considers nodes at the appropriate depth
            # contour so the one at a similar x-coordinate should be good
            temp_dist = []
            for j in range(0, len(use_indexes)):
                dist = abs(float(x[j]) - float(well_long[i]))
                temp_dist.append(dist)
            min_dist = min(temp_dist)
            min_dists.append(min_dist)

        elif orientation[i] == 'NS':
            # If the orientation is EW than match the node that has the closest y-coordinate
            # to that of the well. This function only considers nodes at the appropriate depth
            # contour so the one at a similar y-coordinate should be good
            temp_dist = []
            for j in range(0, len(use_indexes)):
                dist = abs(float(y[j]) - float(well_lat[i]))
                temp_dist.append(dist)
            min_dist = min(temp_dist)
            min_dists.append(min_dist)

        elif orientation[i] == 'DIAG':
            # Setting the orientation to EW or NS will find a node in a straight X/Y line from the well, by
            # setting the orientation to DIAG, a node will be found that is more considerate of the actual
            # curvature of Earth
            temp_dist = []
            for j in range(1, len(use_indexes)):
                dist = np.sqrt((float(well_long[i]) - float(x[j])) ** 2
                               + (float(well_lat[i]) - float(y[j])) ** 2)
                temp_dist.append(dist)
            min_dist = min(temp_dist)
            min_dists.append(min_dist)

        # The temp_dist vector is equal in length to the number of ADCIRC
        # nodes in the study location. Loop through the temp_dist vector
        # until min_dist is found, the index of this match will be equal
        # to the number of the ADCIRC node to be used for the profile
        for j in range(0, len(temp_dist)):
            if temp_dist[j] == min_dist:
                nodes_used.append(j)

    return nodes_used


def retrieve_data(grid, depth, contour, Hs, swan_TPS, elev, x, y):
    """
    Download Hs, Tp, depth, and elevation from the specified contour line
    """

    # Flip the depth sign if using the nc6b grid
    if grid == 'nc6b':
        contour *= -1

    # Identify the correct nodes to use based on the contour
    use_depths, use_indexes = deep_water_nodes(depth, contour)
    print(use_depths)

    # Get the data
    Hs = Hs[use_indexes]
    swan_TPS = swan_TPS[use_indexes]
    depth = depth[use_indexes]
    elev = elev[use_indexes]
    lon = x[use_indexes]
    lat = y[use_indexes]

    # Identify the correct nodes within the use_indexes
    nodes_used = finding_well_points(use_indexes, x, y)

    # Get the data
    Hs = Hs[nodes_used]
    swan_TPS = swan_TPS[nodes_used]
    depth = depth[nodes_used]
    elev = elev[nodes_used]
    lon = x[nodes_used]
    lat = y[nodes_used]

    # Return the data as a tuple
    print(Hs, swan_TPS, depth, elev, lon, lat)


def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + dt.timedelta(n)
     #figuring out the start and end dates --yielding how many days in range
     #n is adding days 


def adcirc_full_data_download_OLD(date):
    """
    Go into the OpenDAP server and get date for the specified date
    """
    url_1 = 'http://opendap.renci.org:1935/thredds/dodsC/daily/nam/'
    url_2 = '/hsofs/hatteras.renci.org/namhsofs/namforecast/swan_HS.63.nc'
    url_3 = '/hsofs/hatteras.renci.org/namhsofs/namforecast/swan_TPS.63.nc'
    url_4 = '/hsofs/hatteras.renci.org/namhsofs/namforecast/fort.63.nc'
    # url_1= website
    # url_2= significant wave height (swan_Hs)
    # url_3= peak period (swan_TPS)
    # add in URL from file if add new variable

    # trying to make earlier dates work
    # if date earlier than 8/3/2017 then will use these website links
    test_date = dt.datetime(2017, 8, 3, 00)
    cur_date = dt.datetime.strptime(date, "%Y%m%d%H")

    # This is a list of dates that have an hsofs URL but come after the test_date. You can add/remove dates
    # from this list by adding another element (separate with a comma) to the list "dt.datetime(year,month,day,hour)"
    except_dates = [dt.datetime(2017, 9, 15, 00)]

    if cur_date < test_date or cur_date in except_dates:
        url_2 = '/nc6b/hatteras.renci.org/dailyv6c/namforecast/swan_HS.63.nc'
        url_3 = '/nc6b/hatteras.renci.org/dailyv6c/namforecast/swan_TPS.63.nc'
        url_4 = '/nc6b/hatteras.renci.org/dailyv6c/namforecast/fort.63.nc'

    tp_url = url_1 + date + url_3
    hs_url = url_1 + date + url_2
    z_url = url_1 + date + url_4
    # add new url for new variable here

    try:
        # Return the dataset from the netCDF file
        hs_data = nc.Dataset(hs_url, 'r')
        tp_data = nc.Dataset(tp_url, 'r')
        z_data = nc.Dataset(z_url, 'r')
        status = "good"
        # add in new dataset here

    except IOError:
        hs_data = 0
        tp_data = 0
        z_data = 0
        status = "fail"
        # add new variable here and set equal to 0

    return hs_data, tp_data, z_data, status


def adcirc_full_data_download(date):
    """
    Go into the OpenDAP server and get date for the specified date

    url_1: Generic path to data
    url_2: Significant wave heights
    url_3: Peak periods
    url_4: Depths
    """

    catalog_url = 'http://tds.renci.org:8080/thredds/catalog/daily/nam/'
    url_1 = 'http://tds.renci.org:8080/thredds/dodsC/daily/nam/'
    directory_url = catalog_url + date + '/catalog.html'

    # Check if an nc6b grid exists for the date, if so use it.
    # You can add more urls to these lists!
    for file in listFD(directory_url):
        if file.find('nc6b') != -1:
            url_2 = '/nc6b/hatteras.renci.org/dailyv6c/namforecast/swan_HS.63.nc'
            url_3 = '/nc6b/hatteras.renci.org/dailyv6c/namforecast/swan_TPS.63.nc'
            url_4 = '/nc6b/hatteras.renci.org/dailyv6c/namforecast/fort.63.nc'
            grid = 'nc6b'
            break
        else:
            url_2 = '/hsofs/hatteras.renci.org/namhsofs/namforecast/swan_HS.63.nc'
            url_3 = '/hsofs/hatteras.renci.org/namhsofs/namforecast/swan_TPS.63.nc'
            url_4 = '/hsofs/hatteras.renci.org/namhsofs/namforecast/fort.63.nc'
            grid = 'hsofs'

    tp_url = url_1 + date + url_3
    hs_url = url_1 + date + url_2
    z_url = url_1 + date + url_4
    # Can add more data here, make sure the addresses are correct

    try:
        # Return the dataset from the netCDF file
        hs_data = nc.Dataset(hs_url, 'r')
        tp_data = nc.Dataset(tp_url, 'r')
        z_data = nc.Dataset(z_url, 'r')
        status = "good"
        # add in new dataset here

    except IOError:
        hs_data = 0
        tp_data = 0
        z_data = 0
        status = "fail"
        # add new variable here and set equal to 0

    return hs_data, tp_data, z_data, status, grid


def hsofs_node_find(x, y):
    """
    Find the appropiate nodes in the hsofs grid using the locations of the nodes used
    from the nc6b grid. Similar to the finding_well_points function, you'll have to
    enter in the general shoreline orientation of the well locations (DIAG, NS, EW)
    """

    # Store the locations of the nc6b nodes used in a dictionary (Python data structure type)
    # Add more locations using the format: 'Location': [lat, lon],
    # Don't forget the comma at the end!
    nc6b_nodes = {
        'Shackleford': [-76.6601, 34.482],
        'South Core': [-76.10741, 34.66574],
    }

    # Loop through the locations in the dictionaries
    nodes_used = []
    for key in nc6b_nodes:

        # Set the lat/lon of the current nc6b location as a tuple (Python data structure type)
        # of (lat, lon). The haversine function in Python uses lat, lon while all the other
        # methods used here are lon, lat
        curr_loc = (float(nc6b_nodes[key][1]), float(nc6b_nodes[key][0]))

        # Initialize the min_dist variable with some number. It doesn't matter what the
        # number is, it just has to be very big so that there is at least one node in the
        # hsofs mesh that is closer to the nc6b node location than this number. It will get
        # overwritten in the for-loop below immediately.
        min_dist = 1000000

        # Loop through the nodes in the box
        for i in range(len(x)):

            # Set a tuple of the (lat, lon) of the current hsofs node being looked at
            search_location = (float(y[i]), float(x[i]))

            # Use the haversine function to calculate the distance between the nc6b node
            # location and the current node being looked at. The function defaults to calculating
            # distance in miles, by setting miles=False it calculates in kilometers.
            dist = haversine.haversine(search_location, curr_loc, miles=False)

            if dist < min_dist:
                # If the distance calculated above is less than the current value
                # of min_dist, set min_dist to the current value of dist. Store the
                # index of the current hsofs node too.
                min_dist = dist
                index = i

        # Append the index of the closest hsofs node to the nodes_used list
        nodes_used.append(index)

    return nodes_used


def get_model_base_time(nc_file):
    """
    Retrieve the base date for the model run and return
    it as a datetime object
    """

    # Loop through the attributes of the time variable
    # in the nc_file until "base_date" is found. Then
    # store it as a string
    for attr in nc_file['time'].ncattrs():
        if attr == 'base_date':
            base_time_str = getattr(nc_file['time'], attr)
            break

    # Convert the base_time string into a datetime object
    dt_format = '%Y-%m-%d %H:%M:%S'
    base_time_dt = dt.datetime.strptime(base_time_str, dt_format)

    return base_time_dt


def dst_start_end(year):
    """
    Return the start and end times of daylight
    savings based on the year being looked at
    """

    # Can add more years, just follow the pattern of the top
    # year as "if year == ____:" and the rest as
    # "elif year == ____:"
    if year == 2016:
        dst_start = dt.datetime(year, 3, 13, 2, 00)
        dst_end = dt.datetime(year, 11, 6, 2, 00)
    elif year == 2017:
        dst_start = dt.datetime(year, 3, 12, 2, 00)
        dst_end = dt.datetime(year, 11, 5, 2, 00)
    elif year == 2018:
        dst_start = dt.datetime(year, 3, 11, 2, 00)
        dst_end = dt.datetime(year, 11, 4, 2, 00)

    return dst_start, dst_end


def get_real_time(base_time, time, gmt):
    """
    Use the base time and the current time value to
    determine the real time represented by the current
    model time step

    The time in ADCIRC is in GMT, the optional GMT argument will convert the time to
    Eastern time if set to true

    Returns the real time as a string and as a datetime object
    """

    # The time argument comes from ADCIRC, it is equal to the number
    # of seconds since the reference time included in the metadata. Set
    # it as the timestep and then add it to the base time to calculate
    # the real time in GMT
    real_time_step = dt.timedelta(seconds=time)
    real_time = base_time + real_time_step
    real_time_str = real_time.strftime('%Y-%m-%d %H:%M:%S')

    # If gmt is set to false than the time will convert to EDT
    if ~gmt:

        # Check if the date is during daylight savings time
        use_year = int(real_time_str[0:4])  # Get the year
        dst_start, dst_end = dst_start_end(use_year)
        if (dst_start < real_time < dst_end):
            gmt_adjust = dt.timedelta(hours=4)
            real_time = real_time - gmt_adjust
            real_time_str = real_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            gmt_adjust = dt.timedelta(hours=5)
            real_time = real_time - gmt_adjust
            real_time_str = real_time.strftime('%Y-%m-%d %H:%M:%S')

    return real_time, real_time_str


def find_nowcast(date):
    """
    See if a nowcast run exists for the current data and return a
    "True"/"False". This uses the same listFD function that checks
    for an nc6b grid in the adcirc_full_data_download() function but
    here a different URL is passed to listFD() which allows it to check
    if a folder named "nowcast" exists
    """

    gen_url = 'http://tds.renci.org:8080/thredds/catalog/daily/nam/'
    casts_url = gen_url + date + '/hsofs/hatteras.renci.org/namhsofs/catalog.html'

    for cast in listFD(casts_url):
        if cast.find('nowcast') != -1:
            res = True
            break
        else:
            res = False

    return res


def adcirc_full_nowcast_data_download(date):
    """
    Go into the OpenDAP server and get date for the specified date

    url_1: Generic path to data
    url_2: Significant wave heights
    url_3: Peak periods
    url_4: Depths

    8/10/18: All nowcasts are on the hsofs grid so this function will just
             assume an hsofs grid
    """

    url_1 = 'http://tds.renci.org:8080/thredds/dodsC/daily/nam/'
    url_2 = '/hsofs/hatteras.renci.org/namhsofs/nowcast/swan_HS.63.nc'
    url_3 = '/hsofs/hatteras.renci.org/namhsofs/nowcast/swan_TPS.63.nc'
    url_4 = '/hsofs/hatteras.renci.org/namhsofs/nowcast/fort.63.nc'
    grid = 'hsofs'

    # Print out which grid is being used
    print('Using %s grid for nowcast data\n' % grid)

    tp_url = url_1 + date + url_3
    hs_url = url_1 + date + url_2
    z_url = url_1 + date + url_4
    # Can add more data here, make sure the addresses are correct

    try:
        # Return the dataset from the netCDF file
        hs_data = nc.Dataset(hs_url, 'r')
        tp_data = nc.Dataset(tp_url, 'r')
        z_data = nc.Dataset(z_url, 'r')
        status = "good"
        # add in new dataset here

    except IOError:
        hs_data = 0
        tp_data = 0
        z_data = 0
        status = "fail"
        # add new variable here and set equal to 0

    return hs_data, tp_data, z_data, status, grid


def download_nowcast_data(date, bottom_lat, upper_lat, left_lon, right_lon, writer, bad_dates_log, use_gmt, use_navd88):
    """
    If a nowcast exists for the current date, this function will download
    all the nowcast data first before the main program runs. This function
    is essentially the main program with nowcast URLs.

    Any variable in the main program that needs a "now" version is passed to
    this function this way variable names could technically be shared without
    causing an issue
    """

    # Download the data
    hs_data, tp_data, z_data, status, grid = adcirc_full_nowcast_data_download(date)

    if status == 'good':

        x = hs_data['x']
        y = hs_data['y']
        time = hs_data['time']

        # Setup the time
        base_time_dt = get_model_base_time(hs_data)

        # Narrow down the lat/lon
        start, end = find_search_indexes(left_lon, right_lon, x)
        x, y = x_y_refine(x, y, start, end)

        # Loop through every time step and record the value of that
        # variable at the current time
        for t in range(len(time)):

            # Calculate the "real" time from the model
            real_time, real_time_str = get_real_time(base_time_dt, time[t], gmt=use_gmt)

            # Print the current time step being worked on
            if use_gmt:
                print('Currently working on forecast time step %d of %d (Real time: %s GMT)' %
                      (t + 1, len(time), real_time))
            else:
                print('Currently working on forecast time step %d of %d (Real time: %s EST)' %
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

            # Find the nodes at the defined contour. This can be changed but should be kept at -20
            deep_contour = -20
            mhw_contour = 0.34
            if grid == 'nc6b':

                # Get deep water data
                deep_contour *= -1
                use_depths, use_indexes = deep_water_nodes(depth, deep_contour)
                Hs = Hs[use_indexes]
                swan_TPS = swan_TPS[use_indexes]
                elev = elev[use_indexes]
                deep_nodes_used = finding_well_points(use_indexes, x, y)

            elif grid == 'hsofs':

                # Get deep water data
                deep_nodes_used = hsofs_node_find(x, y)

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
                msl_to_navd88 = -0.112  # Meters
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
        log_line = '\r\n' + date + '\tCould not load nowcast data'
        bad_dates_log.write(log_line)
        print('Date stored in bad_dates_log.txt\r\n')

    # Clear the hour from the date string
    # Return to: yyyymmdd
    date = date[:-2]


def download_nowcast_data_known_node(date, nodes_used, writer, bad_dates_log, use_gmt, use_navd88):
    """
    If a nowcast exists for the current date, this function will download
    all the nowcast data first before the main program runs. This function
    is essentially the main program with nowcast URLs.

    Any variable in the main program that needs a "now" version is passed to
    this function this way variable names could technically be shared without
    causing an issue
    """

    # Download the data
    hs_data, tp_data, z_data, status, grid = adcirc_full_nowcast_data_download(date)

    if status == 'good':

        x = hs_data['x']
        y = hs_data['y']
        time = hs_data['time']

        # Setup the time
        base_time_dt = get_model_base_time(hs_data)

        # Loop through every time step and record the value of that
        # variable at the current time
        for t in range(len(time)):

            # Calculate the "real" time from the model
            real_time, real_time_str = get_real_time(base_time_dt, time[t], gmt=use_gmt)

            # Print the current time step being worked on
            if use_gmt:
                print('Currently working on nowcast time step %d of %d (Real time: %s GMT)' %
                      (t + 1, len(time), real_time))
            else:
                print('Currently working on nowcast time step %d of %d (Real time: %s EST)' %
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
        log_line = '\r\n' + date + '\tCould not load nowcast data'
        bad_dates_log.write(log_line)
        print('Date stored in bad_dates_log.txt\r\n')

    # Clear the hour from the date string
    # Return to: yyyymmdd
    date = date[:-2]


def make_date_range():
    """
    Set the start and end date for the Known_Node_Multiday_Data_Download
    file
    """

    # Enter the start date
    Start_Year = input('Enter the start_year (YYYY): ')
    Start_Month = input('Enter the start_month (do not include a leading 0): ')
    Start_Day = input('Enter the start_date (do not include a leading 0): ')
    Start_date_dt = dt.datetime(int(Start_Year), int(Start_Month), int(Start_Day))
    Start_date = Start_date_dt.strftime('%Y%m%d')

    print('\r\n')

    # Enter the end date
    End_Year = input('Enter the end_year (YYYY): ')
    End_Month = input('Enter the end_month (do not include a leading 0): ')
    End_Day = input('Enter the end_date (do not include a leading 0): ')
    End_date_dt = dt.datetime(int(End_Year), int(End_Month), int(End_Day))
    End_date = End_date_dt.strftime('%Y%m%d')

    print('---------------------')

    # Set the time zone and vertical datum
    use_gmt = bool(input('Use GMT (T) or EST (F): '))
    use_navd88 = bool(input('Use NAVD88 (T) or MSL (F): '))

    # Enter the node IDs
    print('---------------------')
    nodes_used = []
    num_nodes = int(input('How many nodes to look at: '))
    for i in range(num_nodes):
        prompt = 'Enter node ID ' + str(i + 1) + ' of ' + str(num_nodes) + ': '
        node = input(prompt)
        nodes_used.append(int(node))
    print('---------------------\r\n')

    return Start_date, Start_date_dt, End_date, End_date_dt, use_gmt, use_navd88, nodes_used
