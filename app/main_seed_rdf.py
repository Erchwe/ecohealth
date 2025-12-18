
from flask import Flask, jsonify
from flask_cors import CORS

try:
    from app.openaq_client import fetch_all_cities_pm25
    from app.rdf_builder import build_graph_from_measurements, save_graph
except ImportError:
    from openaq_client import fetch_all_cities_pm25
    from rdf_builder import build_graph_from_measurements, save_graph

app = Flask(__name__)
CORS(app) 

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Ecohealth Semantic API is running",
        "endpoints": ["/generate-rdf"]
    })

@app.route('/generate-rdf')
def generate_rdf():
    try:
        ###

        measurements = fetch_all_cities_pm25()
        graph = build_graph_from_measurements(measurements)
        save_graph(graph)
        
        ###
        return jsonify({
            "status": "success",
            "message": "RDF graph has been generated in /tmp",
            "city_processed": len(measurements)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

