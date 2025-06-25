import stanza
import os

# Script ini hanya untuk mengunduh model Bahasa Indonesia.
# Jalankan script ini sekali saja dari terminal.

print("Memulai proses unduh model Stanza untuk Bahasa Indonesia (id)...")
print("Proses ini bisa memakan waktu beberapa menit, tergantung koneksi internet.")
print("Pastikan folder 'stanza_resources' di C:\\Users\\<nama_user>\\ sudah dihapus jika proses sebelumnya gagal.")

try:
    # Perintah untuk mengunduh paket 'id'
    stanza.download('id')
    print("\n=======================================================")
    print("  UNDUHAN SELESAI!")
    print("  Model Stanza untuk Bahasa Indonesia berhasil diunduh.")
    print("=======================================================")

except Exception as e:
    print(f"\nTerjadi error saat mengunduh: {e}")
    print("Pastikan koneksi internet Anda stabil dan coba jalankan script ini lagi.")

