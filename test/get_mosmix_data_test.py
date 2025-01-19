import pytest
from main import get_mosmix_data

def test_get_mosmix_data():
    result = get_mosmix_data("10389", dataset="S", pa_to_hpa=False, k_to_c=False)
    assert len(result["data"]) > 0 and result["dataset"] == "MOSMIX_S" and result["id"] == "10389"