from transformers import pipeline
import re
import sqlite3
import pandas as pd

class NERExtractor:
    def __init__(self, db_path='jobs.db'):
        """
        Konstruktor untuk memuat pipeline NER, daftar kota, dan daftar kata kunci.
        """
        print("Memuat model NER 'cahya/bert-base-indonesian-NER'...")
        self.ner_pipeline = pipeline(
            "ner", 
            model="cahya/bert-base-indonesian-NER", 
            aggregation_strategy="simple"
        )
        print("Model NER berhasil dimuat.")
        
        self.known_cities = self._load_known_cities(db_path)
        
        self.common_keywords = [
            'remote', 'full-time', 'part-time', 'fulltime', 'parttime', 
            'python', 'java', 'javascript', 'sql', 'go', 'docker', 'kubernetes', 
            'react', 'vue', 'angular', 'seo', 'marketing', 'sales', 'penjualan', 
            'pemasaran', 'data', 'analis', 'analyst', 'designer', 'desainer', 
            'engineer', 'developer', 'akuntan', 'administrasi'
        ]
        
        # PERBAIKAN 4: Menambahkan pemetaan untuk area lokasi
        self.area_mapping = {
            'Pedesaan': ['jauh dari kota', 'pedesaan', 'asri', 'tenang', 'desa'],
            'Pusat Kota': ['pusat kota', 'ramai', 'sibuk', 'kota besar'],
            'Kawasan Industri': ['pabrik', 'industri']
        }

    def _load_known_cities(self, db_path):
        """Memuat semua nama kota unik dari database."""
        try:
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query("SELECT DISTINCT location_city FROM jobs", conn)
            conn.close()
            cities = [city.lower() for city in df['location_city'].tolist()]
            print(f"Berhasil memuat {len(cities)} kota dari database.")
            return cities
        except Exception as e:
            print(f"Gagal memuat daftar kota dari database: {e}")
            return []

    def extract(self, query):
        """
        Mengekstrak lokasi, gaji, dan kata kunci dari query.
        """
        query_lower = query.lower().strip()
        entities = {
            'location': None,
            'salary_min': None,
            'salary_max': None,
            'keywords': [],
            'location_area': None # Menambahkan entitas baru
        }

        # --- Ekstraksi Gaji ---
        salaries = []
        salary_matches = re.findall(r'(\d[\d.,]*)', query_lower)
        is_million = 'juta' in query_lower or 'jt' in query_lower
        for match in salary_matches:
            try:
                val = int(match.replace('.', '').replace(',', ''))
                if is_million and val < 1000:
                    val *= 1_000_000
                salaries.append(val)
            except ValueError:
                continue
        salaries.sort()
        if len(salaries) >= 2:
            entities['salary_min'], entities['salary_max'] = salaries[0], salaries[1]
        elif len(salaries) == 1:
            entities['salary_min'] = salaries[0]

        # --- Ekstraksi Entitas dengan Model BERT & Fallback ---
        ner_results = self.ner_pipeline(query)
        locations = []
        bert_keywords = []
        for ent in ner_results:
            if ent['entity_group'] == 'LOC':
                locations.append(ent['word'])
            elif ent['entity_group'] in ['ORG', 'PER', 'MISC']:
                bert_keywords.append(ent['word'])

        if locations:
            entities['location'] = locations[0].title()
        elif self.known_cities: # Fallback Lokasi
            for city in self.known_cities:
                if city in query_lower:
                    entities['location'] = city.title()
                    break

        # --- PERBAIKAN 4: Ekstraksi Konteks Area Lokasi ---
        for area, context_words in self.area_mapping.items():
            for word in context_words:
                if word in query_lower:
                    print(f"Fallback: Mengenali '{word}' sebagai preferensi area '{area}'.")
                    entities['location_area'] = area
                    break
            if entities['location_area']:
                break

        # --- Logika Ekstraksi Kata Kunci Gabungan ---
        all_keywords = bert_keywords
        for keyword in self.common_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', query_lower):
                all_keywords.append(keyword)

        entities['keywords'] = list(set(all_keywords))

        return entities
