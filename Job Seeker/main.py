from flask import Flask, request, render_template
from model import NERExtractor
from jobs_query import query_jobs

app = Flask(__name__)

DB_PATH = 'jobs.db' 

print("Menginisialisasi aplikasi dan memuat model NER...")
model = NERExtractor()
print("Model NER siap digunakan. Aplikasi berjalan.")

@app.route("/")
def index():
    return render_template('match.html')

@app.route("/cari", methods=['POST'])
def cari():
    query = request.form['query']
    entities = model.extract(query)
    jobs_list = query_jobs(DB_PATH, entities) 
    return render_template('match.html', jobs=jobs_list, query=query, entities=entities)

if __name__ == "__main__":
    app.run(debug=True)
