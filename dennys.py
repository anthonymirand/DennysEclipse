#!/usr/bin/env python

''' Scrape location data from URL '''
import urllib2
from bs4 import BeautifulSoup
''' Find coordinates given scraped locations '''
from geopy.geocoders import Nominatim, GoogleV3
''' Read addresses and coordinates from CSV '''
import csv
''' Create map from coordinates '''
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from mpl_toolkits.basemap import Basemap as Basemap
import shapefile as sf
from shapely.geometry import shape, Point

DEBUG = False

def get_dennys_addresses():
  location_url = 'https://locations.dennys.com/'

  print 'Parsing state URLS...'
  page = urllib2.urlopen(location_url)
  soup = BeautifulSoup(page, 'html.parser')
  states = soup.find_all('a', attrs={'class': 'c-directory-list-content-item-link'})
  states_link = []
  for s in states:
    states_link.append(s.get('href'))

  print 'Parsing city URLS...'
  cities_link = []
  for state in states_link:
    state_url = location_url + state
    if DEBUG: print state_url
    state_page = urllib2.urlopen(state_url)
    soup = BeautifulSoup(state_page, 'html.parser')
    cities = soup.find_all('a', attrs={'class': 'c-directory-list-content-item-link'})
    for city in cities:
      cities_link.append(city.get('href'))

  print 'Finding Denny\'s locations...'
  cities = []
  for i, city in enumerate(cities_link):
    try:
      city_url = location_url + city
      city_page = urllib2.urlopen(city_url)
      soup = BeautifulSoup(city_page, 'html.parser')
      addresses = soup.find_all('div', attrs={'class': 'c-address'})
      for address in addresses:
        total = address.text
        full_address = '{} {}'.format(total[3:], total[:2])
        if DEBUG: print full_address
        cities.append(full_address)
    except:
      continue

  # hard-code 'empty' states
  cities.append('1250 Bladensburg Rd NE Washington, DC  20002 US') # DC/WASHINGTON
  cities.append('4445 Benning Rd NE Washington, DC  20019 US')     # DC/WASHINGTON
  cities.append('80 Macintosh Plaza Newark, DE  19713 US')         # DE/NEWARK/248777

  return cities

def find_coordinates(addresses):
  coordinates = []
  geolocator_n, geolocator_g = Nominatim(), GoogleV3()

  print 'Finding coordinates for addresses...'
  for address in addresses:
    latitude, longitude = None, None
    try:
      location_n = geolocator_n.geocode(address)
      latitude, longitude = location_n.latitude, location_n.longitude
    except:
      pass
    try:
      if latitude is None or longitude is None:
        location_g = geolocator_g.geocode(address)
        latitude, longitude = location_g.latitude, location_g.longitude
    except:
      pass
    if latitude is not None or longitude is not None:
      if DEBUG: print address
      coordinates.append((latitude, longitude))

  return coordinates

def map_dennys_locations(coordinates):
  m = Basemap(llcrnrlon=-119,
              llcrnrlat=22,
              urcrnrlon=-64,
              urcrnrlat=49,
              projection='lcc',
              lat_1=33,
              lat_2=45,
              lon_0=-95)
  m.readshapefile('basemap/st99_d00', 'states', drawbounds=False)

  # Unzip, convert to coordinates, rezip
  upath17 = sf.Reader('basemap/upath17')
  eclipse, = upath17.shapes()
  eclipse_x, eclipse_y = zip(*eclipse.points)
  x, y = m(eclipse_x, eclipse_y)
  xy = zip(x,y)

  eclipse_outline = Polygon(xy,
                            color='#C8C8C8',
                            alpha=0.4,
                            linewidth=0.2)
  eclipse_polygon = shape(eclipse)

  ax = plt.gca()
  ax.axis('off')

  for state in m.states:
    state_polygon = Polygon(state,
                            facecolor='#E4E4E4',
                            edgecolor='white',
                            linewidth=0.2)
    ax.add_patch(state_polygon)

  ax.add_patch(eclipse_outline)

  for latitude, longitude in coordinates:
    if eclipse_polygon.contains(Point(longitude, latitude)):
      marker_color = '#EE3338'
      marker_zorder = 2
    else:
      marker_color = '#CECECE'
      marker_zorder = 1

    x, y = m(longitude, latitude)
    m.plot(x, y,
           marker='o',
           markeredgecolor='white',
           markeredgewidth=0.3,
           markersize=3,
           color=marker_color,
           alpha=0.8,
           zorder=marker_zorder)

  if DEBUG: plt.show()
  else: plt.savefig('dennys_eclipse.png',
                    format='png',
                    dpi=2000,
                    bbox_inches='tight')


def _write_location_data(addresses, coordinates):
  with open('dennys_locations.csv', 'wb') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    writer.writerow(['Address', 'Latitude', 'Longitude'])
    for location in zip(addresses, coordinates):
      writer.writerow([location[0], location[1][0], location[1][1]])

def _read_location_data():
  addresses, coordinates = [], []
  with open('dennys_locations.csv') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for i, row in enumerate(reader):
      if i == 0: continue
      addresses.append(row[0])
      coordinates.append((float(row[1]), float(row[2])))
  return addresses, coordinates

if __name__ == '__main__':
  # addresses = get_dennys_addresses()
  # coordinates = find_coordinates(addresses)
  # _write_location_data(addresses, coordinates)

  # Read pre-computed data from csv
  addresses, coordinates = _read_location_data()

  map_dennys_locations(coordinates)
