# from openaq_client import fetch_all_cities_pm25
# from rdf_builder import build_graph_from_measurements, save_graph

from openaq_client import fetch_all_cities_pm25
from rdf_builder import build_graph_from_measurements,save_graph

def main():
    measurements = fetch_all_cities_pm25()
    graph = build_graph_from_measurements(measurements)
    save_graph(graph)

if __name__ == "__main__":
    main()
