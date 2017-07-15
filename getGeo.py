#Imports
import configparser
import simplejson
from urllib.parse import urlparse
from urllib.request import Request as urlrequest
from urllib.request import build_opener
from math import cos, sin, radians, degrees, asin, atan2


#set constants
home_string = '25+Wellfield+Road+Huddersfield'
config_path ='/home/james/'
no_of_angles = 12  # best multipal of 12
travel_methods = ['driving','bicycling','transit','walking']
travel_method = travel_methods[2]
travel_time_limit = 20 # mins
tolerance = 5 #mins


def build_url(address_str='', config_path='/home/' ):
    #read in api_key
    config = configparser.ConfigParser()
    config.read('{}example.ini'.format(config_path))
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
    d = simplejson.load(f)
    geocode = [d['results'][0]['geometry']['location']['lat'],
               d['results'][0]['geometry']['location']['lng']]
    return geocode


def parse_destination_json(d):
    if d['status'] != 'OK':
        raise Exception('Error. Google Maps API return status: {}'.format(d['status']))

    addresses = d['destination_addresses']

    print (addresses)
    i = 0
    durations = [0] * len(addresses)
    for row in d['rows'][0]['elements']:
        if not row['status'] == 'OK':
            # raise Exception('Error. Google Maps API return status: {}'.format(row['status']))
            durations[i] = 9999
        else:
            if 'duration_in_traffic' in row:
                durations[i] = row['duration_in_traffic']['value'] / 60
            else:
                durations[i] = row['duration']['value'] / 60
        i += 1
    return [addresses, durations]


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


def get_travel_times(origin=[0,0], destinations=[0,0], travel_method='DRIVING', config_path='/home/' ):
    #read in api_key
    config = configparser.ConfigParser()
    config.read('{}example.ini'.format(config_path))
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
    d = simplejson.load(f)
    return d










def main():
    url = build_url(address_str = home_string, config_path = config_path )
    origin =  geocode_home(url)
    print (str(origin[0]) + "," + str(origin[1]))

    #make inital destination points
    angles =[360/no_of_angles * i for i in range(no_of_angles)]

    r_min = [0]*no_of_angles
    rad0 = [(travel_time_limit / 60) * 5 for _ in range(no_of_angles)]# at 5mph
    r_max = [(travel_time_limit / 60) * 75 for _ in range(no_of_angles)]# at 75mph

    locations = ['']* no_of_angles

    destinations =[]


    for i in angles:
        #select my initial possible points
        lat2,lng2 = select_destination(origin,i,rad0[i])
        print (str(lat2) + "," + str(lng2))
        destinations.append([lat2,lng2])

        #get travel times
        jsonFile = get_travel_times(origin,destinations,travel_method,config_path)
        travel_times = parse_destination_json(jsonFile)

        if (travel_times[1][i] < (travel_time_limit - tolerance)) & (locations[i] != travel_times[0][i]):
            rad2[i] = (r_max[i] + rad0[i]) / 2
            r_min[i] = rad0[i]
        elif (travel_times[1][i] > (travel_time_limit + tolerance)) & (locations[i] != travel_times[0][i]):
            rad2[i] = (r_min[i] + rad0[i]) / 2
            r_max[i] = rad0[i]
        else:
            rad2[i] = rad0[i]
            locations[i] = travel_times[0][i]


        rad0 = rad1
        rad1 = rad2




    '''
    Make a radius list, one element for each angle,
    whose elements will update until the isochrone is found
    '''
    rad1 = [duration / 12] * number_of_angles  # initial r guess based on 5 mph speed
    phi1 = [i * (360 / number_of_angles) for i in range(number_of_angles)]
    data0 = [0] * number_of_angles
    rad0 = [0] * number_of_angles
    rmin = [0] * number_of_angles
    rmax = [1.25 * duration] * number_of_angles  # rmax based on 75 mph speed
    iso = [[0, 0]] * number_of_angles

    # Counter to ensure we're not getting out of hand
    j = 0

    # Here's where the binary search starts
    while sum([a - b for a, b in zip(rad0, rad1)]) != 0:
        rad2 = [0] * number_of_angles
        for i in range(number_of_angles):
            iso[i] = select_destination(origin, phi1[i], rad1[i], access_type, config_path)
            time.sleep(0.1)
        url = build_url(origin, iso, access_type, config_path)
        data = parse_json(url)
        for i in range(number_of_angles):
            if (data[1][i] < (duration - tolerance)) & (data0[i] != data[0][i]):
                rad2[i] = (rmax[i] + rad1[i]) / 2
                rmin[i] = rad1[i]
            elif (data[1][i] > (duration + tolerance)) & (data0[i] != data[0][i]):
                rad2[i] = (rmin[i] + rad1[i]) / 2
                rmax[i] = rad1[i]
            else:
                rad2[i] = rad1[i]
            data0[i] = data[0][i]
        rad0 = rad1
        rad1 = rad2
        j += 1
        if j > 30:
            raise Exception("This is taking too long, so I'm just going to quit.")

    for i in range(number_of_angles):
        iso[i] = geocode_address(data[0][i], access_type, config_path)
        time.sleep(0.1)

    #iso = sort_points(origin, iso, access_type, config_path)
    return iso









#make inital destination points



main