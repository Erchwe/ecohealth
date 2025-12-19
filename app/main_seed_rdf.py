from flask import Flask, jsonify, Response
from flask_cors import CORS
import sys
import os

# Menambahkan direktori saat ini ke path agar import berfungsi dengan baik
sys.path.append(os.path.dirname(__file__))

try:
    # Mengimpor fungsi konversi dari converter.py
    from app.converter import convert_csv_to_rdf
except ImportError:
    from converter import convert_csv_to_rdf

app = Flask(__name__)
CORS(app) # Mengizinkan akses dari domain lain (penting untuk web app)

# Menentukan path absolut untuk folder utama proyek
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Path output di folder /tmp (Wajib untuk Vercel karena folder lain bersifat Read-Only)
TTL_OUTPUT = "/tmp/ontology.ttl"

@app.route('/')
def home():
    """Endpoint utama untuk mengecek status server."""
    return jsonify({
        "status": "online",
        "message": "Ecohealth Semantic API is running",
        "endpoints": {
            "generate_rdf": "/generate-rdf",
            "view_full_rdf": "/view-rdf"
        }
    })

@app.route('/generate-rdf')
def generate_rdf():
    """
    Endpoint untuk menjalankan proses transformasi data mentah (CSV & XML) 
    menjadi Knowledge Graph (RDF) serta menjalankan Reasoning Engine.
    """
    try:
        # Tentukan path file input (Bahan Baku di folder semantic/seeds)
        CSV_INPUT = os.path.join(BASE_DIR, "semantic", "seeds", "openaq_sample_pm25.csv")
        XML_INPUT = os.path.join(BASE_DIR, "semantic", "seeds", "diseases.xml")
        
        # Jalankan fungsi konversi (Data Wrapper + Reasoning)
        status_konversi = convert_csv_to_rdf(CSV_INPUT, XML_INPUT, TTL_OUTPUT)
        
        return jsonify({
            "status": "success",
            "message": "RDF graph has been generated successfully in temporary storage",
            "details": {
                "source_data": "openaq_sample_pm25.csv",
                "medical_data": "diseases.xml",
                "status_konversi": status_konversi,
                "next_step": "Akses /view-rdf untuk melihat isi lengkap file RDF"
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Terjadi kesalahan: {str(e)}",
            "hint": "Pastikan file CSV dan XML sudah ada di folder semantic/seeds/"
        }), 500

@app.route('/view-rdf')
def view_rdf():
    """Endpoint khusus untuk menampilkan FULL RDF dalam format Turtle (.ttl)."""
    try:
        if os.path.exists(TTL_OUTPUT):
            with open(TTL_OUTPUT, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Mengembalikan teks murni dengan mimetype turtle agar rapi di browser
            return Response(content, mimetype='text/turtle')
        else:
            return jsonify({
                "status": "error",
                "message": "File RDF belum tersedia. Silakan jalankan /generate-rdf terlebih dahulu."
            }), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Menjalankan server di port 5000 (Localhost)
    app.run(debug=True, port=5000)