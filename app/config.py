API_KEY = "dcee643f4369616080bf4177ea5c2e8051d74cee84d00a091826798172b2de2e"

OPENAQ_V3_URL = "https://api.openaq.org/v3/locations"


CITY_COORDINATES = {
    "Jakarta":    {"lat": -6.2088, "lon": 106.8456, "radius": 12000},
    "Bandung":    {"lat": -6.9175, "lon": 107.6191, "radius": 12000},
    "Surabaya":   {"lat": -7.2575, "lon": 112.7521, "radius": 12000},
    "Medan":      {"lat": 3.5952,  "lon": 98.6722,  "radius": 12000},
    "Denpasar":   {"lat": -8.6500, "lon": 115.2167, "radius": 12000},
}

PM25_PARAMETER = "pm25"

RAW_DATA_DIR = "../../data_raw/openaq_v3"
RDF_OUTPUT_PATH = "ecohealth-Backend/semantic/ontology.ttl"

BASE_URI = "http://example.org/ecohealth/"
