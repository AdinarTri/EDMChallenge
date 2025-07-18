from transformers import pipeline
import re
import sqlite3
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch

class NERExtractor:
    def __init__(self, db_path='jobs.db'):
        
        print("Memuat model NER 'cahya/bert-base-indonesian-NER'...")
        self.ner_pipeline = pipeline("ner", model="cahya/bert-base-indonesian-NER", aggregation_strategy="simple")
        print("Model NER berhasil dimuat.")
        
        print("Memuat model Sentence Transformer untuk pencarian sinonim...")
        self.semantic_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("Model Sentence Transformer berhasil dimuat.")
        
        self.known_cities = self._load_known_cities(db_path)
        self.db_vocabulary, self.db_embeddings = self._load_vocabulary_and_embeddings(db_path)

        self.area_mapping = {
            'Pedesaan': ['jauh dari kota', 'pedesaan', 'asri', 'tenang', 'desa'],
            'Pusat Kota': ['pusat kota', 'ramai', 'sibuk', 'kota besar', 'di kota', 'kota'],
            'Kawasan Industri': ['pabrik', 'industri']
        }
        
        self.stopwords = [
            'saya', 'ingin', 'kerja', 'bekerja', 'dengan', 'gaji', 'di', 'min', 'dan', 'jauh', 
            'dari', 'kota', 'skill', 'cari', 'lowongan', 'untuk', 'sebagai', 'yang'
        ]

    def _load_known_cities(self, db_path):
        """Memuat semua nama kota unik dari database untuk fallback."""
        try:
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query("SELECT DISTINCT location_city FROM jobs", conn)
            conn.close()
            return [city.lower() for city in df['location_city'].tolist()]
        except Exception as e:
            print(f"Gagal memuat daftar kota: {e}")
            return []

    def _load_vocabulary_and_embeddings(self, db_path):
        print("Membangun kosakata dari database untuk pencarian sinonim...")
        try:
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query("SELECT title, skills, description, company_name FROM jobs", conn)
            conn.close()
            full_text = ' '.join(df.stack().dropna())
            vocabulary = sorted(list(set(re.findall(r'\b\w+\b', full_text.lower()))))
            
            print(f"Kosakata dibangun dengan {len(vocabulary)} kata unik. Mengubah menjadi vektor...")
            embeddings = self.semantic_model.encode(vocabulary, convert_to_tensor=True)
            print("Vektor kosakata berhasil dibuat.")
            return vocabulary, embeddings
        except Exception as e:
            print(f"Gagal membangun kosakata dari database: {e}")
            return [], None

    def _find_synonyms(self, keyword, top_k=5, threshold=0.65):
        """Mencari sinonim dari kosakata database menggunakan kemiripan vektor."""
        if self.db_embeddings is None or not self.db_vocabulary:
            return []
        keyword_embedding = self.semantic_model.encode(keyword, convert_to_tensor=True)
        cos_scores = util.pytorch_cos_sim(keyword_embedding, self.db_embeddings)[0]
        top_results = torch.topk(cos_scores, k=min(top_k, len(self.db_vocabulary)))
        synonyms = []
        for score, idx in zip(top_results[0], top_results[1]):
            if score.item() > threshold:
                synonyms.append(self.db_vocabulary[idx])
        return synonyms

    def extract(self, query):
        query_lower = query.lower().strip()
        entities = {
            'location': None, 'salary_min': None, 'salary_max': None,
            'keywords': [], 'location_area': None
        }
        
        used_for_context = set()

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
        elif len(salaries) == 1:
            entities['salary_min'] = salaries[0]

        ner_results = self.ner_pipeline(query)
        locations = []
        bert_keywords = []
        for ent in ner_results:
            if ent['entity_group'] == 'LOC': locations.append(ent['word'])
            elif ent['entity_group'] in ['ORG', 'PER', 'MISC']: bert_keywords.append(ent['word'])

        if locations:
            entities['location'] = locations[0].title()
        elif self.known_cities:
            for city in self.known_cities:
                if city in query_lower:
                    entities['location'] = city.title(); break
        
        for area, context_words in self.area_mapping.items():
            for word in context_words:
                if re.search(r'\b' + re.escape(word) + r'\b', query_lower):
                    entities['location_area'] = area
                    used_for_context.add(word) 
                    print(f"Fallback: Mengenali '{word}' sebagai preferensi area '{area}'.")
                    break
            if entities['location_area']: break

        initial_keywords = bert_keywords
        query_for_keywords = re.sub(r'\d[\d.,]*\s*(jt|juta)?', '', query_lower)
        if entities['location']:
            query_for_keywords = query_for_keywords.replace(entities['location'].lower(), '')

        words = re.findall(r'\b\w+\b', query_for_keywords)
        for word in words:
            if word not in self.stopwords and word not in used_for_context:
                initial_keywords.append(word)

        expanded_keywords = set(initial_keywords)
        for keyword in initial_keywords:
            syns = self._find_synonyms(keyword)
            if syns:
                print(f"Ekspansi sinonim: kata '{keyword}' mirip dengan {syns}")
                expanded_keywords.update(syns)
        
        entities['keywords'] = list(expanded_keywords)

        return entities
