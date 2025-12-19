import csv
import os
import xml.etree.ElementTree as ET
from rdflib import Graph, URIRef, Literal, Namespace, RDF, OWL

def convert_csv_to_rdf(csv_path, xml_path, output_path):
    g = Graph()
    SOSA = Namespace("http://www.w3.org/ns/sosa/")
    EX = Namespace("http://ecohealth.org/schema#")
    g.bind("sosa", SOSA)
    g.bind("ex", EX)

    diseases = {}
    if os.path.exists(xml_path):
        tree = ET.parse(xml_path)
        for d in tree.getroot().findall('disease'):
            d_id = d.get('id').capitalize()
            diseases[d_id] = {
                "uri": URIRef(EX + d_id),
                "name": d.find('name').text,
                "group": d.find('sensitiveGroup').text
            }
            g.add((diseases[d_id]["uri"], RDF.type, EX.Disease))
            g.add((diseases[d_id]["uri"], EX.sensitiveGroup, Literal(diseases[d_id]["group"])))

    if not os.path.exists(csv_path): return "Error: CSV tidak ditemukan."
    
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 10: break 
            
            city_name = row['city'].replace(" ", "_")
            obs_uri = URIRef(EX + f"Obs_{city_name}")
            city_uri = URIRef(EX + city_name)
            pm_val = float(row['value'])

            g.add((obs_uri, RDF.type, SOSA.Observation))
            g.add((obs_uri, SOSA.hasSimpleResult, Literal(pm_val)))
            g.add((obs_uri, SOSA.hasFeatureOfInterest, city_uri))
            
            if pm_val > 150:
                g.add((obs_uri, EX.hasRiskLevel, EX.HighRisk))
                g.add((obs_uri, EX.triggersRiskFor, EX.Asma))
                g.add((obs_uri, EX.recommendation, Literal("Gunakan Masker N95")))
            elif pm_val > 50:
                g.add((obs_uri, EX.hasRiskLevel, EX.ModerateRisk))
                g.add((obs_uri, EX.triggersRiskFor, EX.Ispa))
            else:
                g.add((obs_uri, EX.hasRiskLevel, EX.LowRisk))

    g.serialize(destination=output_path, format="turtle")
    return "Berhasil mengonversi 10 entitas CSV ke RDF."