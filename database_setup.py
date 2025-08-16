# database_setup.py
import pymysql
import os
from dotenv import load_dotenv

# Muat variabel lingkungan
load_dotenv()

# Konfigurasi koneksi
connection = pymysql.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=int(os.getenv("DB_PORT")),
)

print("Berhasil terhubung ke MySQL.")

try:
    with connection.cursor() as cursor:
        db_name = os.getenv("DB_NAME")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.execute(f"USE {db_name}")
        print(f"Menggunakan database '{db_name}'.")

        # Hapus tabel lama jika ada agar tidak terjadi konflik
        print("Menghapus tabel lama (jika ada)...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DROP TABLE IF EXISTS karyawan, detail_penjualan, detail_pembelian, penjualan, pembelian, stok, produk")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        # --- Membuat Tabel-Tabel Baru ---
        print("Membuat skema tabel baru...")
        
        # Tabel Produk
        cursor.execute("""
        CREATE TABLE produk (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama_produk VARCHAR(255) NOT NULL UNIQUE,
            harga_jual INT NOT NULL
        )
        """)
        
        # Tabel Penjualan (Header)
        cursor.execute("""
        CREATE TABLE penjualan (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama_pelanggan VARCHAR(255) NOT NULL,
            tanggal_transaksi DATE NOT NULL
        )
        """)
        
        # Tabel Detail Penjualan
        cursor.execute("""
        CREATE TABLE detail_penjualan (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_penjualan INT NOT NULL,
            id_produk INT NOT NULL,
            jumlah INT NOT NULL,
            FOREIGN KEY (id_penjualan) REFERENCES penjualan(id),
            FOREIGN KEY (id_produk) REFERENCES produk(id)
        )
        """)
        
        # Tabel Pembelian (Header)
        cursor.execute("""
        CREATE TABLE pembelian (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama_supplier VARCHAR(255) NOT NULL,
            tanggal_transaksi DATE NOT NULL
        )
        """)

        # Tabel Detail Pembelian
        cursor.execute("""
        CREATE TABLE detail_pembelian (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_pembelian INT NOT NULL,
            id_produk INT NOT NULL,
            jumlah INT NOT NULL,
            harga_beli INT NOT NULL,
            FOREIGN KEY (id_pembelian) REFERENCES pembelian(id),
            FOREIGN KEY (id_produk) REFERENCES produk(id)
        )
        """)
        
        # Tabel Stok
        cursor.execute("""
        CREATE TABLE stok (
            id_produk INT PRIMARY KEY,
            jumlah_stok INT NOT NULL,
            FOREIGN KEY (id_produk) REFERENCES produk(id)
        )
        """)
        
        print("Semua tabel berhasil dibuat.")

        # --- Memasukkan Data Contoh ---
        print("Memasukkan data contoh...")
        
        # Produk
        produk_data = [('Buku Tulis', 5000), ('Pulpen', 2500), ('Pensil', 1500), ('Penghapus', 1000)]
        cursor.executemany("INSERT INTO produk (nama_produk, harga_jual) VALUES (%s, %s)", produk_data)
        
        # Pembelian
        pembelian_data = [('Supplier A', '2025-08-01'), ('Supplier B', '2025-08-02')]
        cursor.executemany("INSERT INTO pembelian (nama_supplier, tanggal_transaksi) VALUES (%s, %s)", pembelian_data)
        
        # Detail Pembelian
        detail_pembelian_data = [
            (1, 1, 100, 3500), # Beli 100 Buku Tulis dari Supplier A
            (1, 2, 200, 1500), # Beli 200 Pulpen dari Supplier A
            (2, 3, 150, 1000), # Beli 150 Pensil dari Supplier B
            (2, 4, 100, 700),  # Beli 100 Penghapus dari Supplier B
            (2, 1, 50, 3600),   # Beli lagi 50 Buku Tulis dari Supplier B
        ]
        cursor.executemany("INSERT INTO detail_pembelian (id_pembelian, id_produk, jumlah, harga_beli) VALUES (%s, %s, %s, %s)", detail_pembelian_data)

        # Penjualan
        penjualan_data = [('Andi', '2025-08-10'), ('Budi', '2025-08-11'), ('Citra', '2025-08-12')]
        cursor.executemany("INSERT INTO penjualan (nama_pelanggan, tanggal_transaksi) VALUES (%s, %s)", penjualan_data)
        
        # Detail Penjualan
        detail_penjualan_data = [
            (1, 1, 10), # Andi beli 10 Buku Tulis
            (1, 2, 20), # Andi beli 20 Pulpen
            (2, 3, 5),  # Budi beli 5 Pensil
            (2, 4, 5),  # Budi beli 5 Penghapus
            (3, 1, 5),  # Citra beli 5 Buku Tulis
            (3, 2, 10), # Citra beli 10 Pulpen
        ]
        cursor.executemany("INSERT INTO detail_penjualan (id_penjualan, id_produk, jumlah) VALUES (%s, %s, %s)", detail_penjualan_data)

        # --- Menghitung dan Mengisi Stok ---
        print("Menghitung dan memperbarui tabel stok...")
        cursor.execute("""
        INSERT INTO stok (id_produk, jumlah_stok)
        SELECT 
            p.id,
            (SELECT SUM(jumlah) FROM detail_pembelian WHERE id_produk = p.id) - 
            (SELECT COALESCE(SUM(jumlah), 0) FROM detail_penjualan WHERE id_produk = p.id) AS sisa_stok
        FROM produk p
        """)
        
    connection.commit()
    print("✅ Database kompleks berhasil disiapkan dengan data contoh.")

finally:
    connection.close()
    print("Koneksi ditutup.")