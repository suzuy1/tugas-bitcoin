# 📊 Proyek Analisis Hybrid & Migrasi Dataset Historis Bitcoin (2018 - 2025)

Proyek ini merupakan platform analitik terintegrasi untuk memproses, memvisualisasikan, dan mengelola data historis Bitcoin (BTC/USD) dari tahun 2018 hingga 2025. Proyek ini mengombinasikan kekuatan **analisis interaktif Python**, **dashboard web berbasis Streamlit dan Plotly/Matplotlib**, **aplikasi frontend web client-side (HTML/Tailwind/Chart.js)**, serta **manajemen database relasional (SQLite via DBeaver)**.

### 🔗 Sumber Dataset
Dataset historis Bitcoin yang digunakan diperoleh dari Kaggle: [Bitcoin Historical Datasets 2018-2024](https://www.kaggle.com/datasets/novandraanugrah/bitcoin-historical-datasets-2018-2024).

---

## 📂 Struktur Repositori

Berikut adalah pemetaan berkas yang terdapat di dalam direktori kerja proyek:

```text
├── .venv/                         # Virtual environment Python (lokal)
├── btc_1d_data_2018_to_2025.csv   # Dataset Bitcoin - Timeframe Harian (1 Day) - Ringan
├── btc_4h_data_2018_to_2025.csv   # Dataset Bitcoin - Timeframe 4 Jam (4 Hour) - Sedang
├── btc_1h_data_2018_to_2025.csv   # Dataset Bitcoin - Timeframe 1 Jam (1 Hour) - Agak Berat
├── btc_15m_data_2018_to_2025.csv  # Dataset Bitcoin - Timeframe 15 Menit (15 Min) - Berat
├── tugas_bitcoin.ipynb            # Dashboard Analisis Interaktif berbasis Jupyter Notebook
├── app.py                         # Streamlit Dashboard (Plotly Subplots & Analisis Teknikal)
├── btc_dashboard.py               # Streamlit Dashboard (Matplotlib Candlestick & Anotasi Halving)
├── index.html                     # Web Dashboard Mandiri (Tailwind CSS, PapaParse, Chart.js)
├── database_bitcoin.db            # Database SQLite hasil migrasi dari DBeaver
├── readme.md                      # Dokumentasi lengkap proyek (berkas ini)
└── .gitignore                     # Konfigurasi pengabaian berkas Git
```

---

## 🛠️ Analisis Detail Komponen Proyek

Proyek ini dirancang secara modular dengan empat cara berbeda untuk menganalisis data, memberikan fleksibilitas penuh sesuai lingkungan kerja yang digunakan.

### 1. Interactive Jupyter Notebook (`tugas_bitcoin.ipynb`)
Digunakan untuk analisis data eksploratif cepat langsung di dalam editor VS Code.
* **Fitur Utama:**
  * Kontrol input interaktif menggunakan `ipywidgets` (Dropdown untuk timeframe dan DatePicker untuk rentang tanggal).
  * **Caching Sistem (`_cache`):** Menyimpan data di memori RAM agar file CSV berukuran besar tidak perlu dibaca ulang saat mengganti parameter tanggal pada timeframe yang sama.
  * **Pembersihan Data Otomatis:** Deteksi otomatis kolom tanggal/harga, pembersihan spasi nama kolom, parsing timestamp (milidetik atau string ISO), serta pembersihan zona waktu (tz-naive UTC standard).
  * Visualisasi grafik garis pergerakan harga menggunakan `matplotlib`.

### 2. Streamlit Professional Dashboard (`app.py`)
Aplikasi web analitik profesional interaktif yang menghitung indikator teknikal secara *real-time*.
* **Fitur Utama:**
  * **Kalkulasi Indikator Teknikal:**
    * *Simple Moving Average (SMA):* MA20 (tren jangka pendek), MA50 (tren jangka menengah), dan MA200 (tren jangka panjang).
    * *Relative Strength Index (RSI 14):* Indikator momentum jenuh beli (>70) dan jenuh jual (<30).
    * *Drawdown Risk:* Menghitung persentase penurunan harga dari puncak tertinggi (*rolling maximum*) sepanjang periode terpilih.
  * **Metrik Statistik Lanjut:** Menampilkan Harga Penutupan Terakhir, Maksimum Drawdown (Drawdown terdalam), Volatilitas Harian, dan Rasio Hari Naik (*Win Rate*).
  * **Visualisasi Multi-Subplot Plotly:**
    1. *Subplot 1:* Grafik Candlestick interaktif dilapisi dengan Moving Average yang dapat dinyalakan/dimatikan di sidebar.
    2. *Subplot 2:* Volume transaksi berupa grafik batang yang diwarnai dinamis (hijau untuk naik, merah untuk turun).
    3. *Subplot 3:* Grafik RSI 14 dengan garis batas jenuh 30 & 70.
    4. *Subplot 4:* Area fill visualisasi risiko Drawdown (DD%).
  * **Export CSV:** Unduh langsung data terfilter beserta hasil kalkulasi indikator teknikal ke PC lokal.

### 3. Streamlit Custom Dark-Theme Dashboard (`btc_dashboard.py`)
Dashboard alternatif yang dirancang khusus dengan estetika terminal gelap bertema kripto menggunakan kombinasi CSS kustom dan rendering visualisasi statis presisi tinggi.
* **Fitur Utama:**
  * **Visualisasi Candlestick Manual:** Candlestick digambar secara manual di Matplotlib dengan menggambar garis sumbu (*wick*) dan kotak badan (*body*) secara presisi berbasis perbedaan harga Open/Close.
  * **Anotasi Siklus Bitcoin Halving:** Menampilkan garis putus-putus vertikal emas dan label teks untuk peristiwa penting Bitcoin Halving (Halving 2020: `2020-05-11` dan Halving 2024: `2024-04-20`) jika masuk dalam rentang tanggal filter.
  * **Visualisasi Drawdown:** Plot area penurunan harga lengkap dengan garis bantu putus-putus dan teks penunjuk nilai All-Time Max Drawdown.
  * **Desain UI Kustom:** Menggunakan injeksi CSS kustom di Streamlit untuk memodifikasi latar belakang halaman (`#0d1117`), kartu metrik, tombol unduh, dan dropdown agar menyerupai terminal perdagangan profesional.

### 4. Standalone Web Client (`index.html`)
Aplikasi web frontend murni (*client-side*) yang berjalan secara offline tanpa memerlukan server backend Python.
* **Fitur Utama:**
  * **PapaParse Engine:** Parser CSV berkecepatan tinggi berbasis streaming JavaScript untuk menangani file CSV hingga ratusan megabyte secara langsung di browser tanpa membekukan antarmuka pengguna (UI).
  * **Tailwind CSS v4:** Kerangka kerja CSS modern untuk tampilan responsif, modern, dan rapi pada perangkat desktop maupun seluler.
  * **Chart.js Visualization:** Menggambar grafik garis harga penutupan interaktif secara cepat dengan pengoptimalan performa (*pointRadius* disembunyikan otomatis jika jumlah baris data >200 agar grafis tidak lambat).
  * **Deteksi Kolom Cerdas:** Secara otomatis mengenali header kolom tanggal (`date`, `open time`, dll.) dan harga (`close`, `price`, dll.) dari file CSV mana pun yang diunggah oleh pengguna.

---

## ⚡ Instalasi dan Panduan Penggunaan

### 1. Prasyarat Lingkungan Kerja
Pastikan laptop Anda telah terinstal **Python 3.8+** dan IDE **Visual Studio Code**.

### 2. Instalasi Dependensi Python
Buka terminal di folder proyek Anda dan jalankan perintah berikut untuk menginstal pustaka yang dibutuhkan:

```bash
# Membuat virtual environment (opsional namun direkomendasikan)
python -m venv .venv
.venv\Scripts\activate  # Untuk Windows

# Instalasi library pendukung
pip install pandas numpy matplotlib plotly streamlit mplfinance ipywidgets notebook
```

### 3. Cara Menjalankan Aplikasi

* **Untuk Jupyter Notebook:**
  Buka file `tugas_bitcoin.ipynb` di VS Code, pastikan kernel mengarah ke `.venv` Anda, lalu klik **Run All**.

* **Untuk Streamlit Dashboard (`app.py`):**
  Jalankan perintah berikut di terminal:
  ```bash
  streamlit run app.py
  ```

* **Untuk Streamlit Custom Dashboard (`btc_dashboard.py`):**
  Jalankan perintah berikut di terminal:
  ```bash
  streamlit run btc_dashboard.py
  ```

* **Untuk Standalone Web Client (`index.html`):**
  Cukup klik ganda (double-click) file `index.html` untuk membukanya langsung di Google Chrome, Edge, atau Firefox. Unggah berkas CSV Bitcoin (misal: `btc_1d_data_2018_to_2025.csv`) lewat input file yang disediakan untuk mulai menganalisis.

---

## 💾 Implementasi & Migrasi Basis Data (SQLite & DBeaver)

Setelah proses pengolahan data di Python selesai, repositori data ini dimigrasikan ke sistem manajemen basis data relasional SQLite menggunakan aplikasi DBeaver untuk kueri data terstruktur skala besar.

### Langkah Migrasi Data di DBeaver:
1. Buka DBeaver, buat koneksi database baru dengan memilih driver **SQLite**.
2. Simpan file database dengan nama `database_bitcoin.db` di folder proyek Anda.
3. Klik kanan pada folder **Tables** di koneksi baru tersebut, pilih **Import Data**.
4. Pilih **CSV** sebagai sumber data, lalu masukkan file `btc_1d_data_2018_to_2025.csv`.
5. Pada panel target mapping, beri nama tabel baru: `bitcoin_harian`. Selesaikan proses impor hingga data berhasil dimigrasikan.

### Sintaks SQL (DML) Pengujian Basis Data:

> [!IMPORTANT]  
> Karena nama kolom bawaan dataset memiliki karakter spasi dan berhuruf besar (sesuai struktur raw data), nama kolom harus diapit dengan tanda petik ganda (`""`) pada kueri SQL.

#### Kueri 1: Menemukan 5 Rekor Harga Tertinggi Sepanjang Masa (All-Time High)
Digunakan untuk mengidentifikasi puncak-puncak harga Bitcoin dan kapan peristiwa tersebut terjadi.
```sql
SELECT "Open time", "High", "Volume" 
FROM bitcoin_harian 
ORDER BY "High" DESC 
LIMIT 5;
```

#### Kueri 2: Analisis Statistik Deskriptif Agregat
Digunakan untuk mengevaluasi total baris data historis, rata-rata harga penutupan, serta harga ekstrem tertinggi dan terendah sepanjang masa.
```sql
SELECT 
    COUNT(*) AS Total_Hari,
    AVG("Close") AS Rata_Rata_Harga,
    MAX("High") AS Harga_Tertinggi_Maksimal,
    MIN("Low") AS Harga_Terendah_Minimal
FROM bitcoin_harian;
```

#### Kueri 3: Menghitung Selisih Fluktuasi Harian Terbesar (High - Low)
Digunakan untuk mengukur volatilitas harian ekstrem yang pernah dialami pasar Bitcoin.
```sql
SELECT 
    "Open time", 
    "High", 
    "Low", 
    ("High" - "Low") AS Fluktuasi_Harian_USD
FROM bitcoin_harian 
ORDER BY Fluktuasi_Harian_USD DESC 
LIMIT 5;
```

---

## 📈 Kesimpulan Proyek
Proyek ini mendemonstrasikan integrasi yang sukses antara pengolahan data hibrida menggunakan **Python** untuk analisis visual yang interaktif dan dinamis, **Web Frontend murni** untuk aksesibilitas offline portabel tanpa backend, serta **Database Relasional (SQLite)** untuk penyimpanan jangka panjang dan kueri data transaksional yang terstruktur secara optimal.