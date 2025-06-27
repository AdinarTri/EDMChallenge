from flask import Flask, request, render_template
# Mengimpor kelas NERExtractor dari file model.py
from model import NERExtractor
# Mengimpor fungsi query dari file jobs_query.py
from jobs_query import query_jobs

app = Flask(__name__)

DB_PATH = 'jobs.db' # Definisikan path database di sini

print("Menginisialisasi aplikasi dan memuat model NER...")
model = NERExtractor()
print("Model NER siap digunakan. Aplikasi berjalan.")

@app.route("/")
def index():
    return render_template('match.html')

@app.route("/cari", methods=['POST'])
def cari():
    query = request.form['query']
    # 1. Ekstrak entitas menggunakan model BERT
    entities = model.extract(query)
    
    # 2. Lakukan query ke database dengan entitas yang ditemukan
    # PERBAIKAN: Melewatkan DB_PATH ke fungsi query_jobs
    jobs_list = query_jobs(DB_PATH, entities) 
    
    # 3. Tampilkan hasilnya
    return render_template('match.html', jobs=jobs_list, query=query, entities=entities)

if __name__ == "__main__":
    app.run(debug=True)
