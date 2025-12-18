from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.dirname(__file__))

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
    """Endpoint utama untuk mengecek status server."""
    return jsonify({
        "status": "online",
        "message": "Ecohealth Semantic API is running",
        "endpoints": {
            "generate_rdf": "/generate-rdf"
        }
    })

@app.route('/generate-rdf')
def generate_rdf():
    """
    Endpoint untuk menjalankan proses pengambilan data dari OpenAQ 
    dan membangun graf RDF.
    """
    try:
        measurements = fetch_all_cities_pm25()
        graph = build_graph_from_measurements(measurements)
        
        save_graph(graph)
        
        return jsonify({
            "status": "success",
            "message": "RDF graph has been generated successfully",
            "details": {
                "cities_processed": [m['city'] for m in measurements],
                "output_path": "Check /tmp/ontology.ttl in server environment"
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)