import pandas as pd
<<<<<<< Updated upstream
import stanza
import re
import os

class JobMatcher:
    def __init__(self, dataset_path='lowongan_kerja.csv'):
        self.df = self._load_dataset(dataset_path)
        self.nlp = self._load_nlp_model()

    def _load_dataset(self, path):
        if not os.path.exists(path):
            print(f"Error: File dataset tidak ditemukan di '{path}'")
            return pd.DataFrame()
        print(f"Memuat dataset dari '{path}'...")
        return pd.read_csv(path)

    def _load_nlp_model(self):
        print("Memuat model NLP Stanza Bahasa Indonesia (tanpa NER)...")
        stanza.download('id')  # download jika belum ada
        return stanza.Pipeline('id', processors='tokenize,mwt,pos,lemma')

    def _extract_entities(self, query):
=======
# PERBAIKAN: Mengimpor library baru
from sentence_transformers import SentenceTransformer, util
import torch

class NERExtractor:
    def __init__(self, db_path='jobs.db'):
        """
        Konstruktor yang memuat semua model: NER, Sentence Transformer, dan data dari DB.
        """
        print("Memuat model NER 'cahya/bert-base-indonesian-NER'...")
        self.ner_pipeline = pipeline("ner", model="cahya/bert-base-indonesian-NER", aggregation_strategy="simple")
        print("Model NER berhasil dimuat.")
        
        # PERBAIKAN: Memuat model untuk semantic similarity (pencarian sinonim)
        print("Memuat model Sentence Transformer untuk pencarian sinonim...")
        # Model ini multilingual dan bagus untuk Bahasa Indonesia
        self.semantic_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("Model Sentence Transformer berhasil dimuat.")
        
        # PERBAIKAN: Membangun kosakata dan embeddings dari database
        self.db_vocabulary, self.db_embeddings = self._load_vocabulary_and_embeddings(db_path)

        self.area_mapping = {
            'Pedesaan': ['jauh dari kota', 'pedesaan', 'asri', 'tenang', 'desa'],
            'Pusat Kota': ['pusat kota', 'ramai', 'sibuk', 'kota besar', 'di kota', 'kota'],
            'Kawasan Industri': ['pabrik', 'industri']
        }
        
        self.stopwords = [
            'saya', 'ingin', 'kerja', 'dengan', 'gaji', 'di', 'min', 'dan', 'jauh', 
            'dari', 'kota', 'skill', 'cari', 'lowongan', 'untuk', 'sebagai', 'yang'
        ]

    def _load_vocabulary_and_embeddings(self, db_path):
        """
        Membaca semua kata unik dari database dan mengubahnya menjadi vektor (embeddings).
        Proses ini hanya berjalan sekali saat aplikasi dimulai.
        """
        print("Membangun kosakata dari database untuk pencarian sinonim...")
        try:
            conn = sqlite3.connect(db_path)
            # Mengambil semua teks dari kolom yang relevan
            df = pd.read_sql_query("SELECT title, skills FROM jobs", conn)
            conn.close()

            # Menggabungkan semua teks dan memecahnya menjadi kata-kata unik
            full_text = ' '.join(df['title'].dropna()) + ' ' + ' '.join(df['skills'].dropna().str.replace(';', ' '))
            vocabulary = sorted(list(set(re.findall(r'\b\w+\b', full_text.lower()))))
            
            print(f"Kosakata dibangun dengan {len(vocabulary)} kata unik. Mengubah menjadi vektor...")
            # Mengubah setiap kata dalam kosakata menjadi vektor/embedding
            embeddings = self.semantic_model.encode(vocabulary, convert_to_tensor=True)
            print("Vektor kosakata berhasil dibuat.")
            return vocabulary, embeddings
        except Exception as e:
            print(f"Gagal membangun kosakata dari database: {e}")
            return [], None

    def _find_synonyms(self, keyword, top_k=5, threshold=0.65):
        """
        Mencari kata-kata yang mirip (sinonim) dari kosakata database.
        """
        if self.db_embeddings is None:
            return []

        # Mengubah kata kunci menjadi vektor
        keyword_embedding = self.semantic_model.encode(keyword, convert_to_tensor=True)
        
        # Menghitung cosine similarity antara kata kunci dan semua kata di database
        cos_scores = util.pytorch_cos_sim(keyword_embedding, self.db_embeddings)[0]
        
        # Mengambil kata-kata dengan skor tertinggi
        top_results = torch.topk(cos_scores, k=min(top_k, len(self.db_vocabulary)))
        
        synonyms = []
        for score, idx in zip(top_results[0], top_results[1]):
            # Hanya ambil sinonim yang skornya di atas batas (threshold)
            if score.item() > threshold:
                synonyms.append(self.db_vocabulary[idx])
        
        return synonyms

    def extract(self, query):
        """
        Mengekstrak entitas, kini dengan kemampuan ekspansi sinonim otomatis.
        """
        query_lower = query.lower().strip()
>>>>>>> Stashed changes
        entities = {
            'location': None,
            'salary_min': None,
            'salary_max': None,
<<<<<<< Updated upstream
            'keywords': []
        }

        query = query.lower()

        # Deteksi dua angka gaji dalam kalimat
        salary_range_matches = re.findall(r'(\d[\d.,]*)\s*(jt|juta)?', query)
        salaries = []
        for match in salary_range_matches:
            val = int(match[0].replace('.', '').replace(',', ''))
            if match[1] in ['jt', 'juta'] and val < 1000:
                val *= 1_000_000
            salaries.append(val)

        if len(salaries) == 2:
            entities['salary_min'], entities['salary_max'] = min(salaries), max(salaries)
=======
            'keywords': [],
            'location_area': None
        }

        # --- Ekstraksi Gaji (Tidak berubah) ---
        salaries = []
        salary_matches = re.findall(r'(\d[\d.,]*)', query_lower)
        is_million = 'juta' in query_lower or 'jt' in query_lower
        for match in salary_matches:
            try:
                val = int(match.replace('.', '').replace(',', ''))
                if is_million and val < 1000: val *= 1_000_000
                salaries.append(val)
            except ValueError: continue
        salaries.sort()
        if len(salaries) >= 2:
            entities['salary_min'], entities['salary_max'] = salaries[0], salaries[1]
>>>>>>> Stashed changes
        elif len(salaries) == 1:
            entities['salary_min'] = entities['salary_max'] = salaries[0]

<<<<<<< Updated upstream
        # NLP processing
        doc = self.nlp(query)

        nouns = []
        propns = []

        for sentence in doc.sentences:
            for word in sentence.words:
                if word.upos in ['NOUN', 'PROPN', 'ADJ'] and not word.text.isdigit():
                    if word.text not in entities['keywords']:
                        entities['keywords'].append(word.text)
                    if word.upos == 'PROPN':
                        propns.append(word.text)

        # Lokasi diambil dari proper noun
        if propns:
            entities['location'] = propns[0]
=======
        # --- Ekstraksi Entitas & Konteks (Tidak berubah) ---
        ner_results = self.ner_pipeline(query)
        initial_keywords = []
        # (Logika ekstraksi lokasi dan area tidak berubah, jadi disingkat untuk kejelasan)
        # ...

        # --- Logika Ekstraksi & Ekspansi Kata Kunci (BARU) ---
        # 1. Ambil kata-kata dasar dari query
        query_for_keywords = re.sub(r'\d[\d.,]*\s*(jt|juta)?', '', query_lower)
        words = re.findall(r'\b\w+\b', query_for_keywords)
        for word in words:
            if word not in self.stopwords:
                initial_keywords.append(word)

        # 2. Ekspansi otomatis dengan pencarian sinonim
        expanded_keywords = set(initial_keywords)
        for keyword in initial_keywords:
            syns = self._find_synonyms(keyword)
            if syns:
                print(f"Ekspansi sinonim: kata '{keyword}' mirip dengan {syns}")
                expanded_keywords.update(syns)
        
        entities['keywords'] = list(expanded_keywords)
>>>>>>> Stashed changes

        return entities

    def find_jobs(self, query):
        if self.df.empty:
            return [], {}

        entities = self._extract_entities(query)
        results = self.df.copy()

        # Filter berdasarkan lokasi (jika ada)
        if entities['location']:
            results = results[
                results['location_city'].str.lower() == entities['location'].lower()
            ]

        # Filter berdasarkan rentang gaji (jika ada)
        if entities['salary_min'] is not None and entities['salary_max'] is not None:
            results = results[
                (results['salary_max'] >= entities['salary_min']) &
                (results['salary_min'] <= entities['salary_max'])
            ]

        # Filter berdasarkan kata kunci (jika ada)
        if entities['keywords']:
            keyword_query = ' | '.join(entities['keywords'])
            results = results[
                results['title'].str.contains(keyword_query, case=False, regex=True) |
                results['description'].str.contains(keyword_query, case=False, regex=True) |
                results['skills'].str.contains(keyword_query, case=False, regex=True)
            ]

        jobs_list = results.to_dict('records')
        return jobs_list, entities
