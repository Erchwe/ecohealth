from flask import Flask, jsonify, Response, request
from flask_cors import CORS
from rdflib import Graph
import sys
import os

# Menambahkan direktori saat ini ke path agar import berfungsi
sys.path.append(os.path.dirname(__file__))

try:
    from app.converter import convert_csv_to_rdf
except ImportError:
    from converter import convert_csv_to_rdf

app = Flask(__name__)
CORS(app)

# Konfigurasi Path
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# Folder /tmp wajib untuk penulisan file di Vercel (Read-only protection)
TTL_OUTPUT = "/tmp/ontology.ttl"

@app.route('/')
def home():
    """Halaman Utama: Menampilkan daftar fitur yang sudah aktif."""
    return jsonify({
        "status": "online",
        "project": "EcoHealth Semantics",
        "features": {
            "1. Generate Knowledge Graph": "/generate-rdf",
            "2. View Full RDF (Turtle)": "/view-rdf",
            "3. Ask AI (RAG System)": "/ask?city=Jakarta"
        }
    })

@app.route('/generate-rdf')
def generate_rdf():
    """
    LUARAN: POPULASI DATA & VALIDASI SYNTAX.
    Mengonversi 10 kota (CSV) dan data medis (XML) menjadi RDF.
    """
    try:
        CSV_INPUT = os.path.join(BASE_DIR, "semantic", "seeds", "openaq_sample_pm25.csv")
        XML_INPUT = os.path.join(BASE_DIR, "semantic", "seeds", "diseases.xml")
        
        status_konversi = convert_csv_to_rdf(CSV_INPUT, XML_INPUT, TTL_OUTPUT)
        
        return jsonify({
            "status": "success",
            "message": "Knowledge Graph (.ttl) berhasil dibuat di memori sementara.",
            "detail": status_konversi
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/view-rdf')
def view_rdf():
    """MENAMPILKAN FULL RDF: Membuktikan file .ttl valid dan lengkap."""
    if os.path.exists(TTL_OUTPUT):
        with open(TTL_OUTPUT, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(content, mimetype='text/turtle')
    return jsonify({"error": "Jalankan /generate-rdf dulu"}), 404

@app.route('/ask')
def ask_ai():
    city = request.args.get('city', 'Jakarta')
    city_formatted = city.replace(" ", "_")
    
    try:
        if not os.path.exists(TTL_OUTPUT):
            return jsonify({"error": "Jalankan /generate-rdf dulu"}), 400
        
        g = Graph()
        g.parse(TTL_OUTPUT, format="turtle")
        
        # PERBAIKAN: Nama variabel di SELECT harus sama dengan yang di row.namaVariabel
        query = f"""
        PREFIX ex: <http://ecohealth.org/schema#>
        PREFIX sosa: <http://www.w3.org/ns/sosa/>
        SELECT ?pmValue ?risk ?diseaseName ?symptoms ?advice WHERE {{
            ?obs sosa:hasFeatureOfInterest ex:{city_formatted} .
            ?obs sosa:hasSimpleResult ?pmValue .
            OPTIONAL {{ ?obs ex:hasRiskLevel ?risk . }}
            OPTIONAL {{ ?obs ex:recommendation ?advice . }}
            OPTIONAL {{ 
                ?obs ex:triggersRiskFor ?d .
                ?d ex:hasName ?diseaseName .
                ?d ex:symptoms ?symptoms .
            }}
        }}
        """
        results = g.query(query)
        
        context = []
        for row in results:
            context.append({
                "city": city,
                "pm25": str(row.pmValue),
                "risk": str(row.risk).split("#")[-1] if row.risk else "Normal",
                "disease": str(row.diseaseName) if row.diseaseName else "Umum",
                "symptoms": str(row.symptoms) if row.symptoms else "N/A",
                "recommendation": str(row.advice) if row.advice else "Waspada"
            })

        if not context:
            return jsonify({"message": "Data tidak ditemukan"}), 404

        ai_prompt = f"Data kesehatan {city}: PM2.5 {context[0]['pm25']} ({context[0]['risk']}). Risiko: {context[0]['disease']}. Gejala: {context[0]['symptoms']}."

        return jsonify({
            "status": "RAG_Ready",
            "retrieved_context": context,
            "final_ai_prompt": ai_prompt
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(debug=True, port=5000)