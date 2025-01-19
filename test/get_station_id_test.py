from typing import Tuple
import pytest
from main import get_station_id, Station


def test_get_station_id():
    station, distance = get_station_id(52.45340040000001,13.249524122469008) # Berlin
    assert station.id == "10389" and distance == 17.057376812589386