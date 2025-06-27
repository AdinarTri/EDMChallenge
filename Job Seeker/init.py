import sqlite3
import pandas as pd
import os

DB_FILE = "jobs.db"
CSV_FILE = "lowongan_kerja.csv"

def create_database():
    """
    Script untuk membuat database SQLite dari file CSV.
    Hanya perlu dijalankan sekali.
    """
    if not os.path.exists(CSV_FILE):
        print(f"Error: File '{CSV_FILE}' tidak ditemukan. Unduh atau buat file tersebut terlebih dahulu.")
        return

    # Hapus file database lama jika ada, untuk memulai dari awal
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Database lama '{DB_FILE}' dihapus.")

    # Load data dari CSV
    df = pd.read_csv(CSV_FILE)
    print(f"Membaca {len(df)} baris dari '{CSV_FILE}'.")

    # Hubungkan ke SQLite
    conn = sqlite3.connect(DB_FILE)
    
    # Masukkan data dari DataFrame ke tabel 'jobs' di SQLite
    df.to_sql('jobs', conn, if_exists='replace', index=False)
    
    conn.commit()
    conn.close()
    
    print("===================================================")
    print(f"Database '{DB_FILE}' berhasil dibuat dan diisi.")
    print("===================================================")

if __name__ == '__main__':
    create_database()
