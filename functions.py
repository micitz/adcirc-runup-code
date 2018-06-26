"""
User created functions for the daily ADCIRC viewer scripts

Michael Itzkin, 2/21/2018
"""

import netCDF4 as nc
import numpy as np
import datetime as dt
from bs4 import BeautifulSoup
import requests


def listFD(url):
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


def set_date():
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
    print('---------------------\r\n')

    return date


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

    bottom_lat = 34.206229
    upper_lat = 35.132368
    left_lon = -78.148505
    right_lon = -75.245367
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


def deep_water_nodes(depths,contour):
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
        if (depths[i] > search_low and depths[i] < search_high):
            use_depths.append(depths[i])
            use_indexes.append(i)

    # If the provided lat/lon ranges do not contain any nodes at the
    # 20m contour, expand the contour range and try again
    if not use_depths:
        for i in range(1, len(depths)):
            if depths[i] > (search_lower) and depths[i] < (search_higher):
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
    # well_lat is for Shackleford than the first orientation should be "EW")
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

    url_1 = 'http://opendap.renci.org:1935/thredds/dodsC/daily/nam/'
    directory_url = url_1 + date + '/catalog.html'

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

    # Print out which grid is being used
    print('Using %s grid\n' % grid)

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

    return hs_data, tp_data, z_data, status