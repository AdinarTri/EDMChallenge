import sqlite3
import pandas as pd

def query_jobs(db_path, entities):
    """
    Fungsi untuk melakukan query ke database SQLite berdasarkan entitas yang diekstrak.
    """
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if entities.get('location'):
        query += " AND LOWER(location_city) = ?"
        params.append(entities['location'].lower())

    if entities.get('location_area'):
        query += " AND LOWER(location_area) = ?"
        params.append(entities['location_area'].lower())

    if entities.get('salary_min') is not None:
        query += " AND salary_max >= ?"
        params.append(entities['salary_min'])
    
    if entities.get('salary_max') is not None:
        query += " AND salary_min <= ?"
        params.append(entities['salary_max'])

    if entities.get('keywords'):
        keyword_clauses = []
        for kw in entities['keywords']:
            like_kw = f"%{kw}%"
            # PERBAIKAN: Menambahkan pencarian di SEMUA kolom teks yang relevan
            keyword_clauses.append("(LOWER(title) LIKE ? OR LOWER(description) LIKE ? OR LOWER(skills) LIKE ? OR LOWER(job_type) LIKE ? OR LOWER(company_name) LIKE ?)")
            # Menambahkan parameter untuk kolom baru
            params.extend([like_kw, like_kw, like_kw, like_kw, like_kw])
        
        query += f" AND ({' OR '.join(keyword_clauses)})"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df.to_dict('records')
