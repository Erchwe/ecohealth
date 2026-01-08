import xml.etree.ElementTree as ET
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS

# XML_PATH = "../../semantic/seeds/diseases.xml"
# OUTPUT_TTL = "../../semantic/seeds/diseases.ttl"
XML_PATH = "ecohealth/semantic/seeds/diseases.xml"
OUTPUT_TTL = "ecohealth/semantic/seeds/diseases.ttl"

EX = Namespace("https://ecohealth-xi.vercel.app/")

def normalize(text):
    return text.strip().replace(" ", "").replace("-", "")

def main():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    g = Graph()
    g.bind("ex", EX)

    for d in root.findall("disease"):
        disease_id = d.attrib["id"]
        disease_uri = EX[f"Disease/{disease_id}"]

        g.add((disease_uri, RDF.type, EX.Disease))
        g.add((disease_uri, RDFS.label, Literal(d.findtext("name"))))
        g.add((disease_uri, EX.description, Literal(d.findtext("description"))))

        # Risk level
        risk_text = d.findtext("riskLevel")
        risk_uri = EX[f"RiskLevel/{normalize(risk_text)}"]
        g.add((risk_uri, RDF.type, EX.RiskLevel))
        g.add((risk_uri, RDFS.label, Literal(risk_text)))
        g.add((disease_uri, EX.hasRiskLevel, risk_uri))

        # Symptoms
        symptoms = d.findtext("symptoms").split(",")
        for s in symptoms:
            s_clean = s.strip()
            sym_uri = EX[f"Symptom/{normalize(s_clean)}"]
            g.add((sym_uri, RDF.type, EX.Symptom))
            g.add((sym_uri, RDFS.label, Literal(s_clean)))
            g.add((disease_uri, EX.hasSymptom, sym_uri))

    g.serialize(destination=OUTPUT_TTL, format="turtle")
    print(f"[OK] diseases.ttl generated at {OUTPUT_TTL}")

if __name__ == "__main__":
    main()
