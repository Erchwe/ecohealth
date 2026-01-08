import os
from rdflib import Graph

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
BASE_TTL = os.path.join(BASE_DIR, "semantic", "seeds", "cities_pm25.ttl")
RISK_MAP_TTL = os.path.join(BASE_DIR, "semantic", "seeds", "risk_disease_map.ttl")
DISEASES_TTL = os.path.join(BASE_DIR, "semantic", "seeds", "diseases.ttl")
OUTPUT_TTL = os.path.join(BASE_DIR, "semantic", "seeds", "cities_pm25_reasoned.ttl")
RULE_DIR = os.path.join(BASE_DIR, "sparql")

RULE_FILES = [
    "rule_pm25_low.sparql",
    "rule_pm25_medium.sparql",
    "rule_pm25_high.sparql",
    "rule_pm25_veryhigh.sparql",
    "rule_risk_to_disease.sparql",
]

def run_reasoning(output_path: str | None = None):
    g = Graph()

    # load base data
    g.parse(BASE_TTL, format="turtle")
    g.parse(RISK_MAP_TTL, format="turtle")
    if os.path.exists(DISEASES_TTL):
        g.parse(DISEASES_TTL, format="turtle")

    before = len(g)

    # load SPARQL rule
    for file in RULE_FILES:
        rule_path = os.path.join(RULE_DIR, file)
        if not os.path.exists(rule_path):
            continue

        with open(rule_path, encoding="utf-8") as f:
            rule = f.read()

        inferred = g.query(rule)
        for triple in inferred:
            g.add(triple)

    after = len(g)
    output = output_path or OUTPUT_TTL
    g.serialize(destination=output, format="turtle")

    return {
        "status": "success",
        "triples_before": before,
        "triples_after": after,
        "inferred_triples": after - before,
        "output": output
    }

if __name__ == "__main__":
    result = run_reasoning()
    print(result)
