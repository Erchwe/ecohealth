from flask import Flask, jsonify, Response, request
from flask_cors import CORS
from rdflib import Graph
import sys
import os

# Menambahkan direktori saat ini ke path agar import berfungsi
sys.path.append(os.path.dirname(__file__))

try:
    from app.converter import convert_csv_to_rdf
    from app.run_reasoning import run_reasoning
except ImportError:
    from converter import convert_csv_to_rdf
    from run_reasoning import run_reasoning

app = Flask(__name__)
CORS(app)

# Konfigurasi Path
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SEEDS_DIR = os.path.join(BASE_DIR, "semantic", "seeds")
CITIES_TTL = os.path.join(SEEDS_DIR, "cities_pm25.ttl")
REASONED_TTL = os.path.join(SEEDS_DIR, "cities_pm25_reasoned.ttl")
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
            "3. Ask AI (RAG System)": "/ask?city=Jakarta",
            "4. Run Reasoning": "/run-reasoning",
            "5. SPARQL SELECT": "/sparql-select?query=SELECT%20*%20WHERE%20%7B%20%3Fs%20%3Fp%20%3Fo%20%7D%20LIMIT%2010"
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

def _select_dataset_path():
    if os.path.exists(REASONED_TTL):
        return REASONED_TTL
    if os.path.exists(CITIES_TTL):
        return CITIES_TTL
    if os.path.exists(TTL_OUTPUT):
        return TTL_OUTPUT
    return None

def _is_select_query(query: str) -> bool:
    for line in query.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lowered = stripped.lower()
        if lowered.startswith("prefix ") or lowered.startswith("base "):
            continue
        return lowered.startswith("select")
    return False

@app.route('/run-reasoning')
def run_reasoning_endpoint():
    if not os.path.exists(CITIES_TTL):
        return jsonify({"error": "cities_pm25.ttl belum ada, generate dulu"}), 400
    try:
        result = run_reasoning()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sparql-select', methods=["GET", "POST"])
def sparql_select():
    payload = request.get_json(silent=True) or {}
    query = request.args.get("query") or payload.get("query")
    if not query:
        return jsonify({"error": "Query kosong", "example": "SELECT * WHERE { ?s ?p ?o } LIMIT 10"}), 400
    if not _is_select_query(query):
        return jsonify({"error": "Hanya query SELECT yang diizinkan"}), 400

    data_path = _select_dataset_path()
    if not data_path:
        return jsonify({"error": "Dataset belum tersedia"}), 400

    try:
        g = Graph()
        g.parse(data_path, format="turtle")
        results = g.query(query)
        rows = []
        for row in results:
            row_dict = {}
            for key, value in row.asdict().items():
                row_dict[str(key)] = str(value) if value is not None else None
            rows.append(row_dict)
        return jsonify({
            "dataset": data_path,
            "count": len(rows),
            "results": rows
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        PREFIX ex: <https://ecohealth-xi.vercel.app/>
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
