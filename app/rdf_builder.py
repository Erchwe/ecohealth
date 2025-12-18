from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD
from datetime import datetime
from config import BASE_URI, RDF_OUTPUT_PATH

EX = Namespace(BASE_URI)

def classify_pm25(pm25_value: float):
    """
    Kategori PM2.5 berdasarkan band standar AQI PM2.5 (µg/m3), disederhanakan:
    0–50      : Good
    51–100    : Moderate
    101–150   : Unhealthy for Sensitive Groups
    151–200   : Unhealthy
    201–300   : Very Unhealthy
    >300      : Hazardous
    """
    if pm25_value <= 50:
        return "Good"
    elif pm25_value <= 100:
        return "Moderate"
    elif pm25_value <= 150:
        return "UnhealthyForSensitiveGroups"
    elif pm25_value <= 200:
        return "Unhealthy"
    elif pm25_value <= 300:
        return "VeryUnhealthy"
    else:
        return "Hazardous"

def build_graph_from_measurements(measurements_per_city):
    """
    measurements_per_city: list of dict
    [
      {
        "city": "Jakarta",
        "raw": <json dari OpenAQ>
      },
      ...
    ]
    """
    g = Graph()
    g.bind("ex", EX)

    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    for item in measurements_per_city:
        city_name = item["city"]
        raw = item["raw"]

        city_id = city_name.replace(" ", "_")
        city_uri = EX[f"City/{city_id}"]
        g.add((city_uri, RDF.type, EX.City))
        g.add((city_uri, RDFS.label, Literal(city_name)))

        for result in raw.get("results", []):
            for m in result.get("measurements", []):
                if m.get("parameter") != "pm25":
                    continue

                value = m.get("value")
                unit = m.get("unit")
                ts = m.get("lastUpdated") or now_iso

                obs_id = f"{city_id}_{ts.replace(':', '').replace('-', '')}"
                obs_uri = EX[f"Observation/{obs_id}"]

                g.add((obs_uri, RDF.type, EX.AirQualityObservation))
                g.add((obs_uri, EX.observedCity, city_uri))
                g.add((obs_uri, EX.pm25Value, Literal(value, datatype=XSD.float)))
                g.add((obs_uri, EX.unit, Literal(unit)))
                g.add((obs_uri, EX.observedAt, Literal(ts, datatype=XSD.dateTime)))

                category = classify_pm25(value)
                g.add((obs_uri, EX.aqiCategory, Literal(category)))

    return g

def save_graph(g: Graph, path: str = RDF_OUTPUT_PATH):
    g.serialize(destination=path, format="turtle")
    print(f"[RDF] Saved graph to {path}")
