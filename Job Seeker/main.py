from flask import Flask, request, render_template
from model import JobMatcher 

app = Flask(__name__)

print("Menginisialisasi aplikasi dan memuat model...")
model = JobMatcher(dataset_path='lowongan_kerja.csv')
print("Model siap digunakan. Aplikasi berjalan.")

@app.route("/")
def index():
    return render_template('match.html')

@app.route("/cari", methods=['POST'])
def cari():
    query = request.form['query']
    jobs_list, entities = model.find_jobs(query)
    return render_template('match.html', jobs=jobs_list, query=query, entities=entities)

if __name__ == "__main__":
    app.run(debug=True)
