# py_dwd_weather 

Functions for accessing the DWD data MOSMIX_L and MOSMIX_S.

A station ID is required, which can be determined via geo-coordinates.

```python
station, distance = get_station_id(52.45340040000001,13.249524122469008) # Berlin

```

You can then use this ID to determine the current DWD data:

```python
get_mosmix_data(station.id, dataset="S", pa_to_hpa=True, k_to_c=True)
```
The 'dataset' can be specified here and optionally the pressure can be changed from 'Pa' to 'hPa' or Kelvin 'K' to '°C'.

The attributes 'IssueTime', 'interval' and 'next_update' are calculated for the data set so that new data can be determined regularly if required.

The result is in 'data' and is of the type 'pandas.DataFrame'.
The data for a station is read and decoded. In addition, the units for the measured values are made available as a 'parameter' list.

```python
    station, distance = get_station_id(51.5007,0.1246) # London
    if station:
        print(f'id {station.id} name {station.name} disntance {distance}')
        result = get_mosmix_data(station.id, dataset="L", pa_to_hpa=True, k_to_c=True)
        print(result["data"].iloc[0].head(20))
        print("issue time: "+result["IssueTime"]+'\n'+"next update: "+result["next_update"])
```
Result:
```
id 03683 name STANSTED             disntance 1.0688250003445938
time     2025-01-19T10:00:00.000Z
PPPP                       1020.4
E_PPP                         0.2
TX                            NaN
TTT                           1.2
E_TTT                         1.3
Td                           -0.9
E_Td                          0.5
TN                            NaN
TG                            NaN
TM                            NaN
T5cm                         None
DD                          167.0
E_DD                         24.0
FF                           2.06
E_FF                         0.51
FX1                          4.12
FX3                          4.63
FX625                         NaN
FX640                         NaN
Name: 0, dtype: object
issue time: 2025-01-19T09:00:00.000Z
next update: 2025-01-19T15:00:00.000000Z
{'ShortName': 'TTT', 'UnitOfMeasurement': 'K', 'Description': 'Temperature 2m above surface'}
```
