from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.dirname(__file__))

try:
    from app.converter import convert_csv_to_rdf
except ImportError:
    from converter import convert_csv_to_rdf

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

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
@app.route('/generate-rdf')
def generate_rdf():
    """
    Endpoint untuk menjalankan proses transformasi data mentah (CSV & XML) 
    menjadi Knowledge Graph (RDF) serta menjalankan Reasoning Engine.
    Menggunakan direktori /tmp agar kompatibel dengan Read-only file system Vercel.
    """
    try:
        CSV_INPUT = os.path.join(BASE_DIR, "semantic", "seeds", "openaq_sample_pm25.csv")
        XML_INPUT = os.path.join(BASE_DIR, "semantic", "seeds", "diseases.xml")
        
        TTL_OUTPUT = "/tmp/ontology.ttl"

        status_konversi = convert_csv_to_rdf(CSV_INPUT, XML_INPUT, TTL_OUTPUT)
        
        rdf_content = ""
        if os.path.exists(TTL_OUTPUT):
            with open(TTL_OUTPUT, 'r', encoding='utf-8') as f:
                rdf_content = f.read()

        return jsonify({
            "status": "success",
            "message": "RDF graph has been generated successfully in temporary storage",
            "details": {
                "source_data": "openaq_sample_pm25.csv",
                "medical_data": "diseases.xml",
                "status_konversi": status_konversi,
                "output_location": TTL_OUTPUT,
                "rdf_preview": rdf_content[:1000] + "..." if rdf_content else "No content"
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Terjadi kesalahan: {str(e)}",
            "hint": "Pastikan file CSV dan XML sudah ada di folder semantic/seeds/"
        }), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)