#from urllib import request as urlrequest
import os
import pandas as pd
#import datetime
#from datetime import timedelta
#from urllib.error import HTTPError

#global

output_template = 'D:\\working\\ROP_legacy\\GSN\\template.kml'
output_file = 'D:\\working\\ROP_legacy\\GSN\\output.kml'
input_xls = 'C:\\GSN_list\\121115 ground_stations_list_updated.xls'

placemark='''
<Placemark>
			<name>$Name$</name>
			<styleUrl>#GroundStation</styleUrl>
			<Point>
				<coordinates>$longitude$, $latitude$</coordinates>
			</Point>
			<ExtendedData>
				<Data name="Role">
					<value>Ground Station</value>
				</Data>
				<Data name="Status">
					<value>Active</value>
				</Data>
				<Data name="Country">
					<value>$location$</value>
				</Data>
			</ExtendedData>
		</Placemark>
'''

kml_end='''
	</Document>
</kml>
'''

#round datetime

def format_time():
	t = datetime.datetime.now()
	t2 = t + timedelta(days= 7)
	s = t.strftime('%Y-%m-%d_%H:%M:%S.%f')
	s2 = t2.strftime('%Y-%m-%d_%H:%M:%S.%f')
	tail = s[-7:]
	tail2 = s2[-7:]
	f = round(float(tail), 3)
	f2 = round(float(tail2), 3)
	temp = "%.3f" % f
	temp2 = "%.3f" % f2
	return "%s%s" % (s[:-7], temp[1:]), "%s%s" % (s2[:-7], temp2[1:])

def get_placemark(placemark_dict):
	print ('nothing')
	placemark_entry = placemark.replace('$Name$', placemark_dict['GS_text']).replace('$longitude$', str(placemark_dict['lon'])).replace('$latitude$', str(placemark_dict['lat'])).replace('$location$', placemark_dict['location'])
	return placemark_entry
#main
fh = open(output_template, 'r')
try:
	os.remove(output_file)
except:
	print('no previous output-file...continue')

with open(output_file, "a") as output:
	for line in fh.read():
		output.write(line)
	df = pd.read_excel(input_xls, sheetname='Sheet2')
	for i in df.index:
		placemark_dict = dict()
		id = df['ID'][i]
		GS_text = df['Ground Station'][i] + ' ' + df['Antenna'][i]
	#type(df['Latitude'])
		lat = df['Latitude'][i]
		lon = df['Longitude'][i]
		location = df['Location'][i]
		placemark_dict.update({'ID':id, 'GS_text':GS_text, 'lat': lat, 'lon': lon, 'location':location})
		print(placemark_dict)
		placemark_entry = get_placemark(placemark_dict)
		output.write(placemark_entry)
	output.write(kml_end)
fh.close()
output.close()
	#print(id, GS_text, lat, lon, location)
#print(df.columns)
