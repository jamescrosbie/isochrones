#Imports
import configparser
import json
from urllib.parse import urlparse
from urllib.request import Request as urlrequest
from urllib.request import build_opener
from math import pi, cos, sin, radians, degrees, asin, atan2, ceil
import os


#set constants
config_path = '/home/james/Documents/Projects/DataViz/'
output_path = '/home/james/Documents/Projects/DataViz/isochrones/data/'
travel_methods = ['driving', 'bicycling', 'transit', 'walking']

#my parameters
home_string = ['HD1+1BA']
travel_method = travel_methods[2]
travel_time_limit = 40 # mins
tolerance = 5 #mins


def initialise():
#remove response logger
    try:
        os.remove(output_path+'statusFile.csv')
    except:
        print("No response logger")

 
def build_url(address_str='', config_path='/home/'):
    #read in api_key
    config = configparser.ConfigParser()
    config.read('{}googleMapsApiKey.ini'.format(config_path))  
    key = config['api']['api_number']

    #set up address
    prefix = 'https://maps.googleapis.com/maps/api/geocode/json'
    url = urlparse('{0}?address={1}&key={2}'.format(prefix, address_str, key))
    full_url = url.scheme + '://' + url.netloc + url.path + '?' + url.query
    return full_url


def geocode_home(url=''):
    #get geocode of address
    req = urlrequest(url)
    opener = build_opener()
    f = opener.open(req)
    d = json.load(f)
    geocode = [d['results'][0]['geometry']['location']['lat'],
               d['results'][0]['geometry']['location']['lng']]
    return geocode


def parse_destination_json(d):
    if d['status'] != 'OK':
        raise Exception('Error. Google Maps API return status: {}'.format(d['status']))

    addresses = d['destination_addresses']

    print(addresses)
    i = 0
    durations = [0] * len(addresses)
    for row in d['rows'][0]['elements']:
        if row['status'] != 'OK':
            print('Error. Google Maps API return status: {}'.format(row['status']))
            durations[i] = 9999
        else:
            if 'duration_in_traffic' in row:
                durations[i] = row['duration_in_traffic']['value'] / 60
            else:
                durations[i] = row['duration']['value'] / 60
        i += 1
    return [addresses, durations]


def write_response_file(d, c):
    myString = ''
    row = d['rows'][0]['elements']

    for i in range(len(row)):
        myList = []
        tmp = ''
        myList.append(str(c))
        myList.append(travel_method)
        myList.append(d['origin_addresses'])
        myList.append(row[i]['status'])

        myList.append(d['destination_addresses'][i].split())
        if row[i]['status'] == 'OK':
            myList.append(row[i]['distance']['value'])
            myList.append(row[i]['duration']['value'])
        tmp = ','.join(map(str, myList))
        myString = myString + tmp + '\n'

    with open(output_path+"statusFile.csv", "a") as text_file:
        text_file.write(myString)


def select_destination(origin='', angle=30, radius=20):
    '''
    Find the location on a sphere a distance 'radius' along a bearing 'angle' from origin
    This uses haversines rather than simple Pythagorean distance in Euclidean space
    because spheres are more complicated than planes.
    '''
    r = 3963.1676  # Radius of the Earth in miles

    bearing = radians(angle)  # Bearing in radians converted from angle in degrees

    lat1 = radians(origin[0])
    lng1 = radians(origin[1])

    lat2 = asin(sin(lat1) * cos(radius / r) + cos(lat1) * sin(radius / r) * cos(bearing))
    lat2 = degrees(lat2)

    lng2 = lng1 + atan2(sin(bearing) * sin(radius / r) * cos(lat1), cos(radius / r) - sin(lat1) * sin(lat2))
    lng2 = degrees(lng2)
    return [lat2, lng2]


def geocode_destinations(origin=[0,0], angles=[0,180], radii = 5 ):
    destinations = []
    for angle, radius in zip(angles,radii):
        lat2, lng2 = select_destination(origin, angle, radius)
        print(str(lat2) + "," + str(lng2))
        destinations.append([lat2, lng2])
    return destinations


def get_travel_times(origin=[0,0], destinations=[0, 0], travel_method='DRIVING', config_path='/home/'):
    #read in api_key
    config = configparser.ConfigParser()
    config.read('{}googleMapsApiKey.ini'.format(config_path))
    key = config['api']['api_number']

    #set up query strings - origin
    origin_str = ','.join(map(str, origin))

    #set up destination string
    destination_str = ''
    for element in destinations:
        destination_str = '{0}|{1}'.format(destination_str, ','.join(map(str, element)))
    destination_str = destination_str.strip('|')

    prefix = 'https://maps.googleapis.com/maps/api/distancematrix/json?mode='
    url = urlparse('{0}{1}&units=imperial&avoid=tolls|ferries&origins={2}&destinations={3}&key={4}'
                    .format(prefix, travel_method, origin_str, destination_str, key))
    full_url = url.scheme + '://' + url.netloc + url.path + '?' + url.query

    req = urlrequest(full_url)
    opener = build_opener()
    f = opener.open(req)
    d = json.load(f)
    return d


def get_bearing(origin='', destination=''):
    """
    Calculate the bearing from origin to destination
    """
    bearing = atan2(sin((destination[1] - origin[1]) * pi / 180) * cos(destination[0] * pi / 180),
                    cos(origin[0] * pi / 180) * sin(destination[0] * pi / 180) -
                    sin(origin[0] * pi / 180) * cos(destination[0] * pi / 180) * cos((destination[1] - origin[1]) * pi / 180))
    bearing = bearing * 180 / pi
    bearing = (bearing + 360) % 360
    return bearing


def sort_points(origin='', iso=''):
    """
    Put the isochrone points in a proper order
    """
    bearings = []
    for row in iso:
        bearings.append(get_bearing(origin, row))

    points = zip(bearings, iso)
    sorted_points = sorted(points)
    sorted_iso = [point[1] for point in sorted_points]
    return sorted_iso

def resolution(r):
    #based on 12 angles at 30 mins
    #Each angle has arc length
    arcLength = 30 * (2 * pi / 12) # 30 mins is my radius, 12 my angles
    #Length of my circle 
    circ = 2 * pi * r
    #number of angles is ratio of two
    numTheta = ceil(circ / arcLength)
    return numTheta


def main():
    initialise()
    iso = []
    for home in home_string:
        url = build_url(address_str=home, config_path=config_path)
        origin = geocode_home(url)
        print(str(origin[0]) + "," + str(origin[1]))

        #make inital destination points
        no_of_angles = resolution(travel_time_limit) 
        angles =[360 / no_of_angles * i for i in range(no_of_angles)]
        r = [float(travel_time_limit * 10 / 60) for _ in range(no_of_angles)]  # at 5mph

        r_min = [0] * no_of_angles
        r_max = [float(travel_time_limit * 75 / 60) for _ in range(no_of_angles)]# at 75mph

        counter = 0
        change = True
        while change and counter < 10:
            print("Iteration {c}".format(c=counter))
            change = False

            destinations = geocode_destinations(origin, angles, r)
            jsonFile = get_travel_times(origin, destinations, travel_method, config_path)
            write_response_file(jsonFile, counter)
            travel_times = parse_destination_json(jsonFile)

            for i in range(no_of_angles):
                if travel_times[1][i] < travel_time_limit - tolerance:
                    r_min[i] = r[i]
                    r[i] = (r_max[i] + r[i]) / 2
                    change = True
                elif travel_times[1][i] > travel_time_limit + tolerance:
                    r_max[i] = r[i]
                    r[i] = (r_min[i] + r[i]) / 2
                    change = True
            counter += 1

        destinations = geocode_destinations(origin, angles, r)
        destinations = sort_points(origin, destinations)
        iso.append(destinations)

    #make output file for rendering
    mystring = ''
    for el in iso:
        for i in el:
            mystring = mystring + '\n' + str(i) + ','
        mystring = mystring[:-1] + '\n], \n['
    mystring = 'var bounds = [[' + mystring[:-6] + '\n]];'

    with open(output_path+"/bounds.js", "w") as text_file:
        text_file.write(mystring)
#end


main()