#!/usr/bin/python

#Version 0.6 -> provided by rop 07.05.2019

from sgp4.earth_gravity import wgs84
from sgp4.io import twoline2rv
import datetime
import time
from random import randint
import shutil
import os
import sys
from shutil import move
from tempfile import mkstemp
from os import fdopen, remove
from beyond.orbits import Tle
from beyond.frames import create_station
from beyond.dates import Date, timedelta
import numpy as np
from math import cos, radians, sin, sqrt, isnan
import uuid
import pandas as pd

'''
Global
'''
iterations = 288
trailings = 15
colours = 13
starttime_list = list()
WGS84_ellipsoid = 6378137, 298.257223563

'''
operational sats
'''
operational_list = ('BIROS.tle', 'EUCROPIS.tle', 'FLP.tle', 'GRACE-FO1.tle', 'GRACE-FO2.tle', 'TDX-1.tle', 'TET.tle', 'TSX-1.tle')

'''
rgba colours
'''
yellow = '["213", "255", "0", 255]'
gin_fizz = '["255", "249", "222", 255]'
green = '["46", "204", "113", 255]'
bright_green = '["0", "230", "64", 255]'
orange = '["248", "148", "6", 255]'
ecstasy = '["249", "105", "14", 255]'
red = '["217", "30", "24", 255]'
purple = '["165", "55", "253", 255]'
blue = '["52", "152", "219", 255]'
light_blue = '["228", "241", "254", 255]'
pink = '["224", "130", "131", 255]'
turquoise = '["0", "181", "204", 255]'
grey = '["232", "236", "241", 255]'
white = '["255", "255", "255", 255]'
galileo ='["66", "99", "189", 255]'
colour_list = [yellow, green, orange, red, purple, blue, pink, turquoise, grey, white, bright_green, light_blue, gin_fizz, ecstasy]

'''
paths
'''
czml_template = ':-)'
output_czml_path = ':-)'
TLE_source_path = ':-)'
#input_xls = ':-)'
input_xls = ':-)'
input_xls_template = ':-)'

'''
geographic coordinates to cartesian WGS84
'''
def geodetic_to_geocentric(ellipsoid, latitude, longitude, height):
    φ = radians(latitude)
    λ = radians(longitude)
    sin_φ = sin(φ)
    a, rf = ellipsoid                   # semi-major axis, reciprocal flattening
    e2 = 1 - (1 - 1 / rf) ** 2          # eccentricity squared
    n = a / sqrt(1 - e2 * sin_φ ** 2)   # prime vertical radius
    r = (n + height) * cos(φ)           # perpendicular distance from z axis
    x = r * cos(λ)
    y = r * sin(λ)
    z = (n * (1 - e2) + height) * sin_φ
    print(x, y, z)
    return x, y, z

'''
failsafe empty xlsx cells
'''
def check_nan(value):
    if not value == value or value == '-':
        value = 'unknown'
    else:
        value = value
    return value

'''
replace text in file
'''
def replace_txt(file_path, pattern, subst):
    fh, abs_path = mkstemp()
    with fdopen(fh, 'r+') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))
        old_file.close()
    remove(file_path)
    move(abs_path, file_path)
    #subprocess.call(['chmod', '777', file_path])
    new_file.close()

'''
safe copy files
'''
def scopy_file(source, target):
    copied = False
    while not copied:
        if os.path.isfile(target):
            copied = True
        else:
            shutil.copy(source, target)

'''
lookup index
'''
def lookup_index(file, string):
	with open(file) as myFile:
		for num, line in enumerate(myFile, 1):
			if string in line:
				index = num
	return index

'''
add line in text
'''
def add_line(file, index, line_text):
	f = open(file, "r")
	contents = f.readlines()
	f.close()
	contents.insert(index, line_text)
	f = open(file, "w")
	contents = "".join(contents)
	f.write(contents)
	f.close()

'''
remove line in text
'''
def remove_line(file, string):
	with open(file, "r+") as f:
		d = f.readlines()
		f.seek(0)
		for l in d:
			if l.lstrip().rstrip() != string:
				f.write(l)
		f.truncate()

'''
safe delete
'''
def sdelete_file(file):
    deleted = False
    while not deleted:
        try:
            os.remove(file)
            deleted = True
        except:
            deleted = True

'''
get latest timestamp
'''
def get_TLE_starttime(satellite):
    curr_epoch = satellite.epoch
    starttime_list.append(curr_epoch)
    return starttime_list

'''
get timestamp for current time in czml
'''
def get_latest_starttime(starttime):
    curr_day = starttime.strftime("%d")
    curr_month = starttime.strftime("%m")
    curr_year = starttime.strftime("%Y")
    curr_hour = starttime.strftime("%H")
    curr_minute = starttime.strftime("%M")
    curr_second = starttime.strftime("%S")
    curr_microsecond = starttime.strftime("%f")
    #curr_UTC_offset = satellite_epoch.strftime("%z")
    curr_time_czml = curr_year + '-' + curr_month + '-' + curr_day + 'T' + curr_hour + ':' + curr_minute + ':' + curr_second + '.' + curr_microsecond + '+00:00'
    return curr_time_czml, curr_day, curr_month, curr_year, curr_hour, curr_minute, curr_second, curr_microsecond


'''
get czml interval and availability
'''
def get_interval(curr_time_czml, satellite_epoch):
    month_from_now = (satellite_epoch + datetime.timedelta(days = 30)).strftime("%m")
    interval_time = curr_time_czml + '/' + curr_year + '-' + month_from_now + '-' + curr_day + 'T' + curr_hour + ':' + curr_minute + ':' + curr_second + '.' + curr_microsecond + '+00:00'
    end_time = curr_year + '-' + month_from_now + '-' + curr_day + 'T' + curr_hour + ':' + curr_minute + ':' + curr_second + '.' + curr_microsecond + '+00:00'
    return interval_time, end_time

'''
get time with increment
'''
def time_increment(satellite_epoch, k):
	next_time = satellite_epoch + k * datetime.timedelta(seconds = 300)
	next_day = int(next_time.strftime("%d"))
	next_month = int(next_time.strftime("%m"))
	next_year = int(next_time.strftime("%Y"))
	next_hour = int(next_time.strftime("%H"))
	next_minute = int(next_time.strftime("%M"))
	next_second = float(next_time.strftime("%S") + '.' + next_time.strftime("%f"))
	return next_year, next_month, next_day, next_hour, next_minute, next_second

'''
read TLE
'''
def read_TLE():
    f = open(os.path.join(TLE_source_path, files), 'r')
    a = 0
    for line in f:
        if a == 0:
            satellite_name = line.split()[0]
        if a == 1:
            line1_raw = line
        if a == 2:
            line2_raw = line
        a = a + 1
    f.close()
    return satellite_name, line1_raw, line2_raw


'''
TLE format check
'''
def check_tle_format(satellite_name, line1_raw, line2_raw):
	#line0_raw = ('FLP             Epoch 2019/04/23 09:01 UTC IRS                                  ')
	#satellite_name = line0_raw.split()[0]
	#line1_raw = ('1 38710U 12039D  19114.29166667 +.00004194  00000-0 +79295-4 0    05')
	#line1_raw = ('1 70062U 19999A   19113.37590278 0.00000000  00000-0 -34136-4 0    14')
    i = 0
    line1 = ''
    line1_improv = False
    for element in line1_raw.split():
        if i in (0,7):
            line1 = line1 + element + ' '
        if i == 1:
            while len(element) < 6:
                element = element + ' '
                line1_improv = True
            line1 = line1 + element + ' '
        if i == 2:
            while len(element) < 8:
                element = element + ' '
                line1_improv = True
            line1 = line1 + element + ' '
        if i == 3:
            while len(element) < 14:
                element = element + ' '
                line1_improv = True
            line1 = line1 + element + ' '
        if i == 4:
            if not element.startswith('-') and not element.startswith('+'):
                element = '+' + element
            while len(element) < 10:
                element = element + ' '
                line1_improv = True
            line1 = line1 + element + ' '
        if i in (5,8):
            while len(element) < 8:
                line1_improv = True
                element = ' ' + element
            line1 = line1 + element + ' '
        if i == 6:
            if not element.startswith('-') and not element.startswith('+'):
                element = '+' + element
            while len(element) < 8:
                element = element + ' '
                line1_improv = True
            line1 = line1 + element + ' '
        i = i + 1
    if line1_improv:
        print(satellite_name, ' TLE line 1 corrected')

	#line2_raw = ('2 38710  97.6195 98.1255 0001524 49.4987  155.2458 15.49196908376649')
	#line2_raw = ('2 70062  97.5700   8.6374 0127380 245.6119 204.9037 14.90980609    14')
    j = 0
    line2 = ''
    line2_improv = False
    for element in line2_raw.split():
        if j == 0:
            line2 = line2 + element + ' '
        if j == 1:
            while len(element) < 5:
                line2_improv = True
                element = element + ' '
            line2 = line2 + element + ' '
        if j in (2,3,5):
            while len(element) < 8:
                line2_improv = True
                element = ' ' + element
            line2 = line2 + element + ' '
        if j == 4:
            while len(element) < 7:
                line2_improv = True
                element = element + ' '
            line2 = line2 + element + ' '
        if j == 6:
            while len(element) < 8:
                line2_improv = True
                element = element + ' '
            if len(element.split('.')[0]) < 3:
                while len(element.split('.')[0]) < 3:
                    line2_improv = True
                    element = ' ' + element
            line2 = line2 + element + ' '
        if j == 7:
            while len(element) < 17:
                line2_improv = True
                element = element + ' '
            line2 = line2 + element + ' '
        j = j + 1
    if line2_improv:
        print(satellite_name, ' TLE line 2 corrected')
    satellite = twoline2rv(line1, line2, wgs84)
	#position, velocity = satellite.propagate(int(year), int(month), int(day), int(hour), int(minute), float(second + '.' + microsecond))
    return satellite, line2

'''
get position of current time
'''
def get_increment_pos(satellite, next_year, next_month, next_day, next_hour, next_minute, next_second):
	curr_position, velocity = satellite.propagate(next_year, next_month, next_day, next_hour, next_minute, next_second)
	return curr_position

'''
define trailing intervals
'''

def define_trailings(satellite_epoch, line2):
    end_trailing = satellite_epoch + datetime.timedelta(seconds = 86400)
    end_trailing_UNIX = time.mktime(end_trailing.timetuple())
    start_trailing_UNIX = time.mktime(satellite_epoch.timetuple())
    #readable = datetime.datetime.fromtimestamp(start_trailing_UNIX).isoformat()
    trailing_interval = (24/float(line2.split()[-1]))*3600
    #trailing_interval = (end_trailing_UNIX - start_trailing_UNIX)/15
    trailing_list = list()
    trailing = satellite_epoch
    for o in range (0, 16):
        if o == 0:
            trailing_str = str(trailing).replace(' ', 'T') + '+00:00'
            trailing_list.append(trailing_str)
        else:
            trailing = trailing + datetime.timedelta(seconds = trailing_interval)
            trailing_str = str(trailing).replace(' ', 'T') + '+00:00'
            trailing_list.append(trailing_str)
        o = o + 1
    trailing_interval_str = str(trailing_interval)
    return trailing_list, trailing_interval_str

'''
get next 3 passes over station xyz
'''

def next_3_passes(files, curr_day, curr_month, curr_year, curr_hour, curr_minute, curr_second, curr_microsecond, station_name, lat, lon, height):
    AOS_time_list = list()
    LOS_time_list = list()
    with open(os.path.join(TLE_source_path, files), 'r') as f:
        data = f.readlines()
    tle = Tle(data)
    station = create_station(station_name, (lat, lon, height))
    from datetime import datetime
    starttime = Date(datetime(int(curr_year), int(curr_month), int(curr_day), int(curr_hour), int(curr_second)))
    q = 0
    for orb in station.visibility(tle.orbit(), start= starttime, stop=timedelta(days=1), step=timedelta(minutes=2), events=True):
        azim = -np.degrees(orb.theta) % 360
        elev = np.degrees(orb.phi)
        r = orb.r / 1000.
        if orb.event and orb.event.info == "AOS":
            AOS_time = str(orb.date)[:-4] + 'Z'
            AOS_time_list.append(AOS_time)
            q = q + 1
        if orb.event and orb.event.info == "LOS":
            LOS_time = str(orb.date)[:-4] + 'Z'
            LOS_time_list.append(LOS_time)
            if q == 10:
                break
    more_AOS = True
    if len(AOS_time_list) > len(LOS_time_list):
        while more_AOS:
            AOS_time_list = AOS_time_list[:-1]
            q = q -1
            if not len(AOS_time_list) > len(LOS_time_list):
                more_AOS = False
    print(len(AOS_time_list), ' access events calculated')
    return AOS_time_list, LOS_time_list, q

'''
get stations from GSN list
'''
def get_station():
    df = pd.read_excel(input_xls, sheet_name='Sheet2')
    GSN_dict = dict()
    for t in df.index:
        placemark_dict = dict()
        id = df['ID'][t]
        GS_text = str(df['Ground Station'][t]) + ' ' + str(df['Antenna'][t])
        lat = df['Latitude'][t]
        lon = df['Longitude'][t]
        height = df['Altitude / m'][t]
        diameter = df['Diameter [m]'][t]
        Band = check_nan(df['Band'][t])
        Uplink = check_nan(df['Uplink Frequency [MHz]'][t])
        Downlink = check_nan(df['Downlink Frequency [MHz]'][t])
        if isnan(height):
            height = 0.0
        location = df['Location'][t]
        mount = df['Mount'][t]
        if not isnan(lat) and not isnan(lon) and mount != 'Spaceport':
            placemark_dict.update({'GS_text':GS_text, 'lat': lat, 'lon': lon, 'height': height, 'location': location, 'diameter': diameter, 'Band': Band, 'Uplink': Uplink, 'Downlink': Downlink})
            GSN_dict.update({id:placemark_dict})
    del df
    return GSN_dict

'''
get duration in seconds
'''
def get_duration(starttime, endtime):
    try:
        duration = (endtime - starttime).total_seconds()
    except:
        start = datetime.datetime.strptime(starttime, '%Y-%m-%dT%H:%M:%S.%fZ')
        end = datetime.datetime.strptime(endtime, '%Y-%m-%dT%H:%M:%S.%fZ')
        duration = str((end - start).total_seconds()) + 'Z'
    return duration

'''
start
'''
print('operation started')
print('\n')

'''
argument processing
'''
TLE_list_tmp = list()
TLE_list = os.listdir(TLE_source_path)
if len(sys.argv) > 1:                                                                       # if there is any argument, considered TLEs and/ or GSN input list will be adjusted
    argument_list = sys.argv[1:]
    for av_TLE in TLE_list:
        if av_TLE.split('.tle')[0] in argument_list:
            TLE_list_tmp.append(av_TLE)
            print('TLE for ', av_TLE.split('.tle')[0], ' available in source')
    TLE_list = TLE_list_tmp                                                                 # list of TLEs constructed from argument(s)
    if '-GSN' in argument_list:                                                             # GSN input list argument '-GSN'
        GSN_file = argument_list[argument_list.index('-GSN') + 1]
        input_xls = os.path.join(input_xls_template, GSN_file)                              # GSN input list adjustment
    if '-op' in argument_list:                                                              # argument to consider operational GSOC satellites' TLEs for TLE list
        TLE_list = operational_list

TLE_list_tmp = list()                                                                       # check if all TLE files are in source and readable files
for files in TLE_list:
    if os.path.isfile(os.path.join(TLE_source_path, files)):
        TLE_list_tmp.append(files)
TLE_list = TLE_list_tmp

if len(TLE_list) == 0:                                                                      # if satellites from arguments cannot be identified, script is stopped
    print('no TLE from argument sat not available in source ', TLE_source_path)
    sys.exit('please check source')

'''
main
'''

for files in TLE_list:                                                                      # determin start and end point of simulation from TLEs
    satellite_name, line1_raw, line2_raw = read_TLE()
    satellite, line2 = check_tle_format(satellite_name, line1_raw, line2_raw)
    starttime_list = get_TLE_starttime(satellite)
starttime_list.sort(reverse = True)
satellite_epoch = starttime_list[0]
curr_time_czml, curr_day, curr_month, curr_year, curr_hour, curr_minute, curr_second, curr_microsecond = get_latest_starttime(satellite_epoch)

GSN_dict = get_station()                                                                    # get dict of GSN
for files in TLE_list:                                                                      # read TLEs
    satellite_name, line1_raw, line2_raw = read_TLE()
    print('TLE for', satellite_name, 'found in source')
    output_czml = os.path.join(output_czml_path, (satellite_name + '.czml'))                # create output czml
    if os.path.isfile(output_czml):
    	sdelete_file(output_czml)
    scopy_file(czml_template, output_czml)
    satellite, line2 = check_tle_format(satellite_name, line1_raw, line2_raw)               # clean TLEs
    replace_txt(output_czml, '$satellite_name$', satellite_name)                            # write satellite name to output czml
    replace_txt(output_czml, '$current_time$', curr_time_czml)                              # write start point of simulation into output czml

    index = lookup_index(output_czml, '$position$')                                         # write satellite position propagation to output czml
    k = 0
    increment = -300.0
    for k in range (0, iterations):
    	increment = increment + 300.0
    	next_year, next_month, next_day, next_hour, next_minute, next_second = time_increment(satellite_epoch, k)
    	curr_position = get_increment_pos(satellite, next_year, next_month, next_day, next_hour, next_minute, next_second)
    	if k < iterations-1:
    		line_text = str(increment) + ', ' + str(curr_position[0]*1000) + ', ' + str(curr_position[1]*1000) + ', ' + str(curr_position[2]*1000) + ',\n'
    	else:
    		line_text = str(increment) + ', ' + str(curr_position[0]*1000) + ', ' + str(curr_position[1]*1000) + ', ' + str(curr_position[2]*1000) + '\n'
    	add_line(output_czml, index, line_text)
    	index = index + 1
    	k = k + 1
    remove_line(output_czml, '$position$')

    trailing_list, trailing_interval_str = define_trailings(satellite_epoch, line2)         # write trajectory trailing and leading to output czml
    index2 = lookup_index(output_czml, '$trailTime$')
    m = 0
    for m in range (0, trailings):
    	if m < trailings-1:
    		line_text = '{\n"epoch": "' + trailing_list[m] + '",\n"interval": "' + trailing_list[m] + '/' + trailing_list[m+1] + '",\n"number": [0, 0, ' + trailing_interval_str + ', ' + trailing_interval_str + ']\n},\n'
    	else:
    		line_text = '{\n"epoch": "' + trailing_list[m] + '",\n"interval": "' + trailing_list[m] + '/' + trailing_list[m+1] + '",\n"number": [0, 0, ' + trailing_interval_str + ', ' + trailing_interval_str + ']\n}\n'
    	add_line(output_czml, index2, line_text)
    	index2 = index2 + 5
    	m = m + 1
    remove_line(output_czml, '$trailTime$')
    index3 = lookup_index(output_czml, '$leadTime$')
    m = 0
    for m in range (0, trailings):
    	if m < trailings-1:
    		line_text = '{\n"epoch": "' + trailing_list[m] + '",\n"interval": "' + trailing_list[m] + '/' + trailing_list[m+1] + '",\n"number": [0, ' + trailing_interval_str + ', ' + trailing_interval_str + ', 0]\n},\n'
    	else:
    		line_text = '{\n"epoch": "' + trailing_list[m] + '",\n"interval": "' + trailing_list[m] + '/' + trailing_list[m+1] + '",\n"number": [0, ' + trailing_interval_str + ', ' + trailing_interval_str + ', 0]\n}\n'
    	add_line(output_czml, index3, line_text)
    	index3 = index3 + 5
    	m = m + 1
    remove_line(output_czml, '$leadTime$')

    if satellite_name.startswith('GSAT'):                                                   # if Galileo simulation trajectory colouring is constant
        new_colour = galileo
    if not satellite_name.startswith('GSAT'):                                               # get randomized trajectory colouring
        colour_index = randint(0, colours)
        new_colour = colour_list[colour_index]
        colour_list.remove(colour_list[colour_index])
        colours = colours - 1
    replace_txt(output_czml, '$colour$', new_colour)                                        # write trajectory colouring to output czml

    for key, value in GSN_dict.items():                                                     # write station and calculated station satellite access events to output czml
        AOS_time_list, LOS_time_list, q = next_3_passes(files, curr_day, curr_month, curr_year, curr_hour, curr_minute, curr_second, curr_microsecond, value['GS_text'], value['lat'], value['lon'], value['height'])   # calculate access events
        if len(AOS_time_list) < 1:                                                          # if no access event exists between current station and current satellite, the loop is skipped
            continue
        index_uuid = lookup_index(output_czml, '$uuid$')                                    # get access event unique identifier
        uuid_curr = str(uuid.uuid4())
        uuid_text = '{\n"id":"' + uuid_curr + '",\n"name":"Accesses",\n"description":"List of Accesses"\n},\n'
        x, y, z = geodetic_to_geocentric(WGS84_ellipsoid, value['lat'], value['lon'], value['height'])  # transform geographic station coordinates to cartesian coordinates
        antenna_text = ',{\n"id":"Facility/' + value['GS_text'] + '",\n"name":"' + value['GS_text'] + '",\n"availability":"$interval_time$",\n"description":"<!--HTML-->' + r'\r\n<p>\r\n' + value['GS_text'] + r'\n' + value['location'] + r'\ndiameter: ' + str(value['diameter']) + r'\nband: ' + value['Band'] + r'\nUplink Frequency [MHz]: ' + value['Uplink'] + r'\nDownlink Frequency [MHz]: ' + value['Downlink'] + r'\r\n<p>",' + '\n"billboard":{\n"eyeOffset":{\n"cartesian":[0,0,0]\n},\n"horizontalOrigin":"CENTER",\n"image":"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAACvSURBVDhPrZDRDcMgDAU9GqN0lIzijw6SUbJJygUeNQgSqepJTyHG91LVVpwDdfxM3T9TSl1EXZvDwii471fivK73cBFFQNTT/d2KoGpfGOpSIkhUpgUMxq9DFEsWv4IXhlyCnhBFnZcFEEuYqbiUlNwWgMTdrZ3JbQFoEVG53rd8ztG9aPJMnBUQf/VFraBJeWnLS0RfjbKyLJA8FkT5seDYS1Qwyv8t0B/5C2ZmH2/eTGNNBgMmAAAAAElFTkSuQmCC",\n"pixelOffset":\n{\n"cartesian2":[0,0]\n},\n"scale":1.5,\n"show":true,\n"verticalOrigin":"CENTER"\n},\n"label":{\n"fillColor":\n{\n"rgba":[0,255,255,255]\n},\n"font":"11pt Lucida Console",\n"horizontalOrigin":"LEFT",\n"outlineColor":\n{\n"rgba":[0,0,0,255]\n},\n"outlineWidth":2,\n"pixelOffset":\n{\n"cartesian2":[12,0]\n},\n"show":true,\n"style":"FILL_AND_OUTLINE",\n"text":"' + value['GS_text'] + '",\n"verticalOrigin":"CENTER"\n},\n"position":\n{\n"cartesian":[' + str(x) + ',' + str(y) + ',' + str(z) + ']\n}\n}\n'
        access_text = ',{\n"id":"Facility/' + value['GS_text'] + '-to-satellite/' + satellite_name + '",\n"name":"' + value['GS_text'] + ' to ' + satellite_name + '",\n"parent":"' + uuid_curr + '",\n"availability":\n[\n$AOS_LOS_time_av$\n],\n"description":"<h2>Access times</h2><table class=' + "'sky-infoBox-access-table'><tr><th>Start</th><th>End</th><th>Duration</th></tr>$durations$" + '</table>",\n"polyline":\n{\n"show":\n[\n$AOS_LOS_time$\n],\n"width":1,\n"material":\n{\n"solidColor":\n{\n"color":\n{\n"rgba":[0,255,255,255]\n}\n}\n},\n"arcType":"NONE",\n"positions":\n{\n"references":\n[\n"Facility/' + value['GS_text'] + '#position","Satellite/' + satellite_name + '#position"\n]\n}\n}\n}'
        add_line(output_czml, index_uuid, uuid_text)                                        # write access event identifier to output czml
        index_antenna = lookup_index(output_czml, '$antenna$')
        add_line(output_czml, index_antenna, antenna_text)                                  # write station to output czml
        index_access = lookup_index(output_czml, '$access_line$')
        add_line(output_czml, index_access, access_text)                                    # write access event to output czml
        index4 = lookup_index(output_czml, '$AOS_LOS_time_av$')
        Duration_list = list()
        p = 0                                                                               # write access event timings to output czml
        for p in range(0, q):
            if p < q-1:
                AOS_LOS_text_av = '"' + AOS_time_list[p] + '/' + LOS_time_list[p] + '",\n'
            else:
                AOS_LOS_text_av = '"' + AOS_time_list[p] + '/' + LOS_time_list[p] + '"\n'
            Duration_list.append(get_duration(AOS_time_list[p], LOS_time_list[p]))
            add_line(output_czml, index4, AOS_LOS_text_av)
            index4 = index4 + 1
            p = p + 1
        duration_text = ''
        print(Duration_list, 'Duration list')
        x = 0                                                                               # write durations and accesses into access description in output czml
        for x in range(0, len(Duration_list)-1):
            duration_text = duration_text + '<tr><td>' + AOS_time_list[x] + '</td><td>' + LOS_time_list[x] + '</td><td>' + Duration_list[x] + '</td></tr>'
            x = x + 1
        replace_txt(output_czml, '$durations$', duration_text)
        index5 = lookup_index(output_czml, '$AOS_LOS_time$')
        AOS_LOS_text = '{\n"interval":"' + curr_time_czml + '/' + AOS_time_list[0] + '",\n"boolean":false\n},\n'
        add_line(output_czml, index5, AOS_LOS_text)
        index5 = index5 + 4
        s = 0
        boolean_AOS = True
        interval_time, end_time = get_interval(curr_time_czml, satellite_epoch)
        for s in range(0, q-1):
            AOS_LOS_text = '{\n"interval":"' + AOS_time_list[s] + '/' + LOS_time_list[s] + '",\n"boolean":true\n},\n'
            add_line(output_czml, index5, AOS_LOS_text)
            index5 = index5 + 4
            AOS_LOS_text = '{\n"interval":"' + LOS_time_list[s] + '/' + AOS_time_list[s+1] + '",\n"boolean":false\n},\n'
            add_line(output_czml, index5, AOS_LOS_text)
            index5 = index5 + 4
            s = s + 1
        AOS_LOS_text = '{\n"interval":"' + AOS_time_list[-1] + '/' + LOS_time_list[-1] + '",\n"boolean":true\n},\n'
        add_line(output_czml, index5, AOS_LOS_text)
        index5 = index5 + 4
        AOS_LOS_text = '{\n"interval":"' + LOS_time_list[-1] + '/' + end_time + '",\n"boolean":false\n}\n'
        add_line(output_czml, index5, AOS_LOS_text)
        replace_txt(output_czml, '$interval_time$', interval_time)

        remove_line(output_czml, '$AOS_LOS_time_av$')                                       # remove all remaining locator strings from output czml
        remove_line(output_czml, '$AOS_LOS_time$')
    remove_line(output_czml, '$antenna$')
    remove_line(output_czml, '$access_line$')
    remove_line(output_czml, '$uuid$')

    print(satellite_name, ' czml created')                                                  # end operation
    print('\n')
print('operation ended')
