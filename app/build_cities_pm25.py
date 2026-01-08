import os
import sys

sys.path.append(os.path.dirname(__file__))

try:
    from app.rdf_builder import build_graph_from_csv, build_graph_from_measurements, save_graph
    from app.openaq_client import fetch_all_cities_pm25
except ImportError:
    from rdf_builder import build_graph_from_csv, build_graph_from_measurements, save_graph
    from openaq_client import fetch_all_cities_pm25

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CSV_INPUT = os.path.join(BASE_DIR, "semantic", "seeds", "openaq_sample_pm25.csv")
CITIES_TTL = os.path.join(BASE_DIR, "semantic", "seeds", "cities_pm25.ttl")

def build_from_csv():
    g = build_graph_from_csv(CSV_INPUT)
    save_graph(g, CITIES_TTL)
    return CITIES_TTL

def build_from_openaq():
    measurements = fetch_all_cities_pm25()
    g = build_graph_from_measurements(measurements)
    save_graph(g, CITIES_TTL)
    return CITIES_TTL

def main():
    source = os.environ.get("CITY_SOURCE", "csv").lower()
    if source == "openaq":
        output = build_from_openaq()
    else:
        output = build_from_csv()
    print(f"[OK] cities_pm25.ttl generated at {output}")

if __name__ == "__main__":
    main()
