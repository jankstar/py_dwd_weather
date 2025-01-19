import numpy as np
import pandas as pd

import urllib.request
import io
import zipfile

from lxml import etree # type: ignore[import]
import re
import math

from typing import  Dict, Tuple
from datetime import datetime, timedelta

import logging

from pandas.io.formats.style_render import DataFrame
logger = logging.getLogger(__name__)

cardinal_direction = [
    {'Name': 'Norden', 'Bearing': 'N', 'Azimuth': 0.00, 'Azimuth2': 0.00, 'Azimuth3': 11.25},
    {'Name': 'Nordnordost', 'Bearing': 'NNO', 'Azimuth': 22.50, 'Azimuth2': 11.26, 'Azimuth3': 33.75},
    {'Name': 'Nordost', 'Bearing': 'NO', 'Azimuth': 45.00, 'Azimuth2': 33.76, 'Azimuth3': 56.25},
    {'Name': 'Ostnordost', 'Bearing': 'ONO', 'Azimuth': 67.50, 'Azimuth2': 56.26, 'Azimuth3': 78.75},
    {'Name': 'Osten', 'Bearing': 'O', 'Azimuth': 90.00, 'Azimuth2': 78.76, 'Azimuth3': 101.25},
    {'Name': 'Ostsüdost', 'Bearing': 'OSO', 'Azimuth': 112.50, 'Azimuth2': 101.26, 'Azimuth3': 123.75},
    {'Name': 'Südost', 'Bearing': 'SO', 'Azimuth': 135.00, 'Azimuth2': 123.76, 'Azimuth3': 146.25},
    {'Name': 'Südsüdost', 'Bearing': 'SSO', 'Azimuth': 157.50, 'Azimuth2': 146.26, 'Azimuth3': 168.75},
    {'Name': 'Süden', 'Bearing': 'S', 'Azimuth': 180.00, 'Azimuth2': 168.76, 'Azimuth3': 191.25},
    {'Name': 'Südsüdwest', 'Bearing': 'SSW', 'Azimuth': 202.50, 'Azimuth2': 191.26, 'Azimuth3': 213.75},
    {'Name': 'Südwest', 'Bearing': 'SW', 'Azimuth': 225.00, 'Azimuth2': 213.76, 'Azimuth3': 236.25},
    {'Name': 'Westsüdwest', 'Bearing': 'WSW', 'Azimuth': 247.50, 'Azimuth2': 236.26, 'Azimuth3': 258.75},
    {'Name': 'Westen', 'Bearing': 'W', 'Azimuth': 270.00, 'Azimuth2': 258.76, 'Azimuth3': 281.25},
    {'Name': 'Westnordwest', 'Bearing': 'WNW', 'Azimuth': 292.50, 'Azimuth2': 281.26, 'Azimuth3': 303.75},
    {'Name': 'Nordwest', 'Bearing': 'NW', 'Azimuth': 315.00, 'Azimuth2': 303.76, 'Azimuth3': 326.25},
    {'Name': 'Nordnordwest', 'Bearing': 'NNW', 'Azimuth': 337.50, 'Azimuth2': 326.26, 'Azimuth3': 348.75},
    {'Name': 'Norden', 'Bearing': 'N', 'Azimuth': 360.00, 'Azimuth2': 348.76, 'Azimuth3': 360.00},
]

pattern_digit = r'^\d'
URl_MOSMIX_STATIONS = "https://www.dwd.de/EN/ourservices/met_application_mosmix/mosmix_stations.cfg?view=nasPublication" # station list
URl_MOSMIX_S = "https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_S/all_stations/kml/MOSMIX_S_LATEST_240.kmz" # latest MOSMIX S for all stations
#URl_MOSMIX_L = "https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/all_stations/kml/MOSMIX_L_LATEST.kmz " # latest MOSMIX L for all stations
URl_MOSMIX_L = "https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/single_stations/{}/kml/MOSMIX_L_LATEST_{}.kmz" # latest MOSMIX L for one stations
URL_MEASUREMENT = "https://opendata.dwd.de/weather/lib/MetElementDefinition.xml"

global_root_measurement = None #for buffering

def get_measurment_by_parameter(parameter:str) -> dict:
    """get the measurment from DWD server and extract it by parameter"""
    result = {}
    if_fount = False
    global global_root_measurement

    try:
        if global_root_measurement is None:
            with urllib.request.urlopen(URL_MEASUREMENT) as response:
                inhalt = response.read()
            global_root_measurement = etree.fromstring(inhalt)

        for xml_child in global_root_measurement.xpath('//ShortName[text()="{}"]'.format(parameter), 
            namespaces=global_root_measurement.nsmap):
            result[etree.QName(xml_child).localname] = xml_child.text.replace( '\n', '').replace('  ',' ').strip()
            if_fount = True
            for xml_data in xml_child.itersiblings():
                result[etree.QName(xml_data).localname] = xml_data.text.replace( '\n', '').replace('  ',' ').strip()

    except Exception as e:
        logger.error(e)

    if not if_fount:
        return {'ShortName': '"'+parameter+'"', 'UnitOfMeasurement': '-', 'Description': ''}
    return result

def get_cardinal_direction_by_angle(angle) -> dict:
    """get the cardinal direction by angle"""
    for direction in cardinal_direction:
        if direction["Azimuth2"] <= angle and direction["Azimuth3"] > angle:
            return direction
    return  {'Name': '', 'Bearing': '', 'Azimuth': 0.00, 'Azimuth2': 0.00, 'Azimuth3': 0.0}

class Station:
    def __init__(self, *args, **kwargs):
        try:
            if len(args) == 1:
                self.id = args[0][:5]
                self.isao = args[0][6:10]
                self.name = args[0][11:31]
                self.lat = float(args[0][32:37])
                self.long = float(args[0][39:46])
                self.elev = float(args[0][47:54])
            else:
                self.id = args[0]
                self.isao = args[1]
                self.name = args[2]
                self.lat = args[3]
                self.long = args[4]
                self.elev = args[5]
        except Exception as e:
            logger.error(e)

    def __str__(self):
        return f"{self.id} {self.isao} {self.name} {self.lat} {self.long} {self.elev}"

def haversine_distance(station1: Station, lat, long) -> float:
    """calculate the distance between two points by Haversine-Formel"""
    R = 6371  #Earth radius in kilometers

    # Conversion to radiants
    lat1, lon1, lat2, lon2 = map(math.radians, [station1.lat, station1.long, lat, long])

    # Haversine-Formel
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = R * c

    return distance

def get_station_id(lat: float, long: float) -> Tuple[Station, float]:
    '''get the nearest station by geo-location from station-file DWD server '''

    find_station = None
    find_distance = 999999

    with urllib.request.urlopen(URl_MOSMIX_STATIONS) as response:
        while True:
            line = response.readline().decode('Windows-1252', errors='ignore')
            if not line:
                break

            if bool(re.match(pattern_digit, line)):
                station = Station(line)
                if not find_station:
                    find_station = station
                    continue

                distance = abs(haversine_distance(station, lat, long))
                if distance < find_distance:
                    find_distance = distance
                    find_station = station


    if not find_station:
        raise Exception("no station found")
    return find_station, float(find_distance)


def get_mosmix_data(station_id:str, dataset="S", pa_to_hpa=False, k_to_c=False) -> Dict:
    """get the mosmix data from DWD server by ID"""
    result = {}
    dataframe = pd.DataFrame()

    if dataset == "S":
        result["dataset"] = "MOSMIX_S"
        result["interval"] = "60" # 60 min aka 1h
        URl_MOSMIX = URl_MOSMIX_S #short
    else:
        result["dataset"] = "MOSMIX_L"
        result["interval"] = "360" # 360 min aka 6h
        URl_MOSMIX = URl_MOSMIX_L.format(station_id, station_id)   #long

    with urllib.request.urlopen(URl_MOSMIX) as response:
        inhalt = response.read()
        datei_im_speicher = io.BytesIO(inhalt)
    with zipfile.ZipFile(datei_im_speicher) as zip_file:
        logger.info(zip_file.namelist()[0])
        xml_content = zip_file.read(zip_file.namelist()[0])

    root = etree.fromstring(xml_content)
    #print(root.tag)

    #extract issuer
    for xml_child in root.find('.//dwd:ProductDefinition', namespaces=root.nsmap):
        result[etree.QName(xml_child).localname] = xml_child.text.replace( '\n', '').replace('  ',' ').strip()
        if etree.QName(xml_child).localname == 'IssueTime':
            #calculate next update
            issue_time = datetime.strptime(result[etree.QName(xml_child).localname], '%Y-%m-%dT%H:%M:%S.%fZ')
            result["next_update"] = issue_time + timedelta(minutes=float(result["interval"]))
            result["next_update"] = result["next_update"].strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    #extract time
    xml_time = []
    for xml_child in root.find('.//dwd:ForecastTimeSteps', namespaces=root.nsmap):
        xml_time.append(xml_child.text)

    dataframe["time"] = xml_time

    #search station data
    xml_station = None
    for xml_child in root.xpath('.//kml:name[text()="{}"]'.format(station_id), namespaces=root.nsmap):
        if xml_child.tag.endswith('name') and xml_child.text == station_id:
            xml_station = xml_child
            break

    parameter_descriptions = []
    #extract station data
    if not xml_station is None:
        result["id"] = station_id

        for xml_tag in xml_station.itersiblings():
            if xml_tag.tag.endswith('description'):
                result["description"] = xml_tag.text
            if xml_tag.tag.endswith('ExtendedData'):
                xml_data_attrib = None
                for xml_data in xml_tag.iterchildren():
                    if xml_data.tag.endswith('Forecast') and len(xml_data.attrib) > 0:
                        _, xml_data_attrib = xml_data.attrib.items()[0] #name of parameter as attribute
                        if not xml_data_attrib: # or not is_parameter_valide(xml_data_attrib):
                            continue #only define parameter from list
                        for xml_value in xml_data.iterchildren():
                            if xml_value.tag.endswith('value'):
                                dataframe[xml_data_attrib] = [
                                    float(x) if bool(re.match(pattern_digit, x)) else x if not x == '-' else None for x in xml_value.text.split()]
                                parameter_descriptions.append(get_measurment_by_parameter(xml_data_attrib))

                        dataframe = dataframe.copy() #for defragmentation

    else:
        raise Exception("station {} not found".format(station_id))

    #wind cardinal direction
    dataframe["_wcd"] = [
        get_cardinal_direction_by_angle(x)["Name"]+" ("+get_cardinal_direction_by_angle(x)["Bearing"]+")" if not np.isnan(x) else  None
            for x in dataframe["DD"] ]

    if pa_to_hpa or k_to_c:
        #all pressure from Pa to hPa
        for i,_ in enumerate(parameter_descriptions):
            if pa_to_hpa and parameter_descriptions[i]["UnitOfMeasurement"] == "Pa":
                dataframe[parameter_descriptions[i]["ShortName"]] = [ (x / 100.0) if type(x) == float else x for x in dataframe[parameter_descriptions[i]["ShortName"]]]
                parameter_descriptions[i]["UnitOfMeasurement"] = "hPa"
            if k_to_c and parameter_descriptions[i]["UnitOfMeasurement"] == "K" and not parameter_descriptions[i]["ShortName"].startswith("E_"):
                dataframe[parameter_descriptions[i]["ShortName"]] = [ (x - 273.15) if type(x) == float else x for x in dataframe[parameter_descriptions[i]["ShortName"]]]
                parameter_descriptions[i]["UnitOfMeasurement"] = "°C"

    result["count"] = dataframe.shape[0]
    result["date_from"] = dataframe["time"].min()
    result["date_to"] = dataframe["time"].max()
    result["data"] = dataframe
    result["parameter"] = parameter_descriptions
    return result

if __name__ == "__main__":
    station, distance = get_station_id(52.45340040000001,13.249524122469008) # Berlin
    if station:
        print(f'id {station.id} name {station.name} disntance {distance}')
        print(get_mosmix_data(station.id, dataset="S", pa_to_hpa=True, k_to_c=True)["data"].iloc[0].head(20))

    station, distance = get_station_id(51.5007,0.1246) # London
    if station:
        print(f'id {station.id} name {station.name} disntance {distance}')
        result = get_mosmix_data(station.id, dataset="L", pa_to_hpa=True, k_to_c=True)
        print(result["data"].iloc[0].head(20))
        print("issue time: "+result["IssueTime"]+'\n'+"next update: "+result["next_update"])

    print(get_measurment_by_parameter("TTT"))
