import pytest
from main import get_measurment_by_parameter


def test_get_measurment_by_parameter():
    assert get_measurment_by_parameter("TTT") == {'ShortName': 'TTT', 'UnitOfMeasurement': 'K', 'Description': 'Temperature 2m above surface'}