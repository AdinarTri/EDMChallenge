import pandas as pd
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
        entities = {
            'location': None,
            'salary_min': None,
            'salary_max': None,
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
        elif len(salaries) == 1:
            entities['salary_min'] = entities['salary_max'] = salaries[0]

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
