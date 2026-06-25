Berikut adalah panduan lengkap langkah-demi-langkah dari awal sampai akhir untuk penyusunan laporan tugas kuliah kamu. Formatnya sudah dibuat terstruktur dan rapi agar mudah kamu rapikan ke dalam Microsoft Word atau Google Docs.

---

## 📑 LAPORAN TUGAS: PENGOLAHAN DAN MIGRASI DATASET HISTORIS BITCOIN (2018 - 2025)

### 🔗 Sumber Dataset
* **Kaggle Dataset:** [Bitcoin Historical Datasets 2018-2024](https://www.kaggle.com/datasets/novandraanugrah/bitcoin-historical-datasets-2018-2024)

---

### BAB 1: PERSIAPAN DATASET DAN LINGKUNGAN KERJA (VS CODE)

Pada tahap awal, dilakukan penyiapan *environment* pemrograman menggunakan Python di Visual Studio Code (VS Code) untuk menganalisis data secara interaktif.

#### Langkah 1: Pemilihan dan Penyiapan File Dataset

1. Unduh dataset Bitcoin dari Kaggle.
2. Pilih file **`btc_1d_data_2018_to_2025.csv`** (Timeframe Harian / 1 Day).
   * *Alasan pemilihan:* Jumlah baris data (~2.500 baris) jauh lebih ringan untuk diproses oleh RAM komputer dibandingkan timeframe 15 menit (15m) yang mencapai ratusan ribu baris, namun tetap mempertahankan akurasi tren tahunan.
3. Buat sebuah folder khusus tugas di laptop, lalu masukkan file CSV tersebut ke dalamnya.

#### Langkah 2: Instalasi Library yang Dibutuhkan via Terminal

Buka terminal di VS Code, pastikan *virtual environment* (`.venv`) aktif, lalu instal semua pustaka (*library*) pendukung data science dengan perintah berikut:

```bash
pip install pandas matplotlib ipywidgets notebook
```

> **Catatan Dokumentasi:** Jika menggunakan Jupyter Notebook di dalam lingkungan tertentu yang sensitif terhadap spasi folder, instalasi dapat dipaksa melalui *cell* notebook dengan perintah `%pip install ipywidgets`.

#### Langkah 3: Pembuatan File Notebook Interaktif

1. Buat file baru di dalam folder kerja dengan nama **`tugas_bitcoin.ipynb`** (Ekstensi `.ipynb` digunakan untuk menjalankan Jupyter Notebook di VS Code).
2. Jika VS Code meminta aktivasi kernel, pilih kernel Python yang sesuai dengan `.venv` laptop kamu.

#### Langkah 4: Implementasi Kode Dashboard Analisis Data (Hybrid & Berkelanjutan)

Masukkan kode Python di bawah ini ke dalam satu *cell* Notebook. Kode ini telah dioptimalkan dengan fitur **Caching** (agar file besar tidak dibaca berulang kali), **Penanganan Zona Waktu (Timezone UTC)**, dan kalkulasi **Persentase Perubahan Harga (% Change)**.

```python
import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, clear_output

# Cache agar file tidak dibaca ulang kalau timeframe sama
_cache = {}

html_judul = widgets.HTML(
    "<h2>📊 Dashboard Hybrid Bitcoin Interaktif (2018 - 2025)</h2>"
    "<p>Pilih Timeframe dan Rentang Tanggal untuk Analisis:</p>"
)

tf_dropdown = widgets.Dropdown(
    options=[
        ('1 Hari (1d) - Ringan', '1d'),
        ('4 Jam (4h) - Sedang', '4h'),
        ('1 Jam (1h) - Agak Berat', '1h'),
        ('15 Menit (15m) - Berat', '15m')
    ],
    value='1d',
    description='Timeframe:'
)

min_limit = pd.to_datetime('2018-01-01').date()
max_limit = pd.to_datetime('2025-12-31').date()

start_picker = widgets.DatePicker(
    description='Tgl Mulai:',
    value=pd.to_datetime('2024-01-01').date(),
    min=min_limit, max=max_limit
)
end_picker = widgets.DatePicker(
    description='Tgl Selesai:',
    value=max_limit,
    min=min_limit, max=max_limit
)

btn_tampil = widgets.Button(
    description='Proses & Tampilkan',
    button_style='warning',
    icon='sync',
    layout=widgets.Layout(width='220px', margin='10px 0px 10px 100px')
)

output_area = widgets.Output()

FILE_MAPPING = {
    '1d': 'btc_1d_data_2018_to_2025.csv',
    '4h': 'btc_4h_data_2018_to_2025.csv',
    '1h': 'btc_1h_data_2018_to_2025.csv',
    '15m': 'btc_15m_data_2018_to_2025.csv'
}

KOLOM_TANGGAL_KANDIDAT = ['date', 'open time', 'timestamp', 'time']
KOLOM_HARGA_KANDIDAT = ['close', 'price', 'harga']


def load_dataframe(tf: str) -> pd.DataFrame:
    """Baca dan standarisasi CSV dengan Caching Memori."""
    if tf in _cache:
        return _cache[tf]

    file_name = FILE_MAPPING[tf]
    df = pd.read_csv(file_name)
    df.columns = df.columns.str.strip()

    kolom_tanggal = next((col for col in df.columns if col.lower() in KOLOM_TANGGAL_KANDIDAT), None)
    kolom_harga = next((col for col in df.columns if col.lower() in KOLOM_HARGA_KANDIDAT), None)

    if kolom_tanggal is None or kolom_harga is None:
        raise ValueError("Struktur kolom file tidak dikenali sistem.")

    if df[kolom_tanggal].dtype in ['int64', 'float64'] and df[kolom_tanggal].max() > 1e11:
        df['Tanggal_Fix'] = pd.to_datetime(df[kolom_tanggal], unit='ms')
    else:
        df['Tanggal_Fix'] = pd.to_datetime(df[kolom_tanggal])

    if df['Tanggal_Fix'].dt.tz is not None:
        df['Tanggal_Fix'] = df['Tanggal_Fix'].dt.tz_convert('UTC').dt.tz_localize(None)

    df['Harga_Fix'] = pd.to_numeric(df[kolom_harga], errors='coerce')
    df = df.dropna(subset=['Harga_Fix']).sort_values('Tanggal_Fix').reset_index(drop=True)

    _cache[tf] = df
    return df


def aksi_proses_data(b):
    with output_area:
        clear_output(wait=True)

        start_dt = pd.to_datetime(start_picker.value)
        end_dt = pd.to_datetime(end_picker.value)

        if start_dt > end_dt:
            print("❌ ERROR: Tanggal Mulai tidak boleh melewati Tanggal Selesai!")
            return

        tf = tf_dropdown.value
        print(f"⏳ Memuat data {tf.upper()}... (Mohon tunggu beberapa detik)")

        try:
            df = load_dataframe(tf)
        except Exception as e:
            clear_output()
            print(f"❌ Gagal memproses file: {e}")
            return

        data_terfilter = df[(df['Tanggal_Fix'] >= start_dt) & (df['Tanggal_Fix'] <= end_dt)]
        clear_output(wait=True)

        if data_terfilter.empty:
            print("❌ Tidak ada data pada rentang tanggal tersebut.")
            return

        harga_awal  = data_terfilter.iloc[0]['Harga_Fix']
        harga_akhir = data_terfilter.iloc[-1]['Harga_Fix']
        harga_max   = data_terfilter['Harga_Fix'].max()
        harga_min   = data_terfilter['Harga_Fix'].min()
        pct_change  = ((harga_akhir - harga_awal) / harga_awal) * 100
        tanda       = "📈" if pct_change >= 0 else "📉"

        print(f"📊 DASHBOARD BITCOIN — TIMEFRAME: {tf.upper()}")
        print(f"📅 Periode : {start_picker.value} s/d {end_picker.value} | 🗂️ {len(data_terfilter):,} Baris")
        print("-" * 65)
        print(f"🔹 Harga Awal    : ${harga_awal:,.2f}")
        print(f"🔹 Harga Akhir   : ${harga_akhir:,.2f}")
        print(f"{tanda} Perubahan  : {pct_change:+.2f}%")
        print(f"🔺 Tertinggi     : ${harga_max:,.2f}")
        print(f"🔻 Terendah      : ${harga_min:,.2f}")
        print("-" * 65)

        plt.figure(figsize=(12, 5))
        plt.plot(data_terfilter['Tanggal_Fix'], data_terfilter['Harga_Fix'], color='#f2a900', linewidth=1.2)
        plt.title(f'Pergerakan Bitcoin — {tf.upper()}', fontsize=13, fontweight='bold')
        plt.grid(True, linestyle='--', alpha=0.4)
        plt.tight_layout()
        plt.show()

btn_tampil.on_click(aksi_proses_data)
ui_hybrid = widgets.VBox([html_judul, widgets.HBox([tf_dropdown]), widgets.HBox([start_picker, end_picker]), btn_tampil, output_area])
display(ui_hybrid)
```

---

### BAB 2: IMPLEMENTASI DAN MIGRASI BASIS DATA (DBEAVER)

Setelah data berhasil dianalisis di Python, data mentah tersebut dipindahkan ke sistem manajemen basis data menggunakan **DBeaver** berbasis **SQLite**.

#### Langkah 1: Pembuatan Database Baru di DBeaver

1. Buka aplikasi DBeaver.
2. Klik menu **New Database Connection** (Ikon colokan listrik di pojok kiri atas).
3. Pilih driver database **SQLite**, lalu klik **Next**.
4. Di kolom *Path*, tentukan folder dan ketik nama file database yang ingin dibuat (Contoh: `database_bitcoin.db`), klik **Finish**.

#### Langkah 2: Proses Impor Data (Import Wizard)

1. Pada panel kiri (*Database Navigator*), ekspansi koneksi SQLite yang baru dibuat.
2. Klik kanan pada folder **Tables**, lalu pilih menu **Import Data**.
3. Pilih **CSV** sebagai *Source Type*, lalu klik **Next**.
4. Cari file **`btc_1d_data_2018_to_2025.csv`** dari folder penyimpanan laptop kamu.
5. Pada bagian **Tables Mapping**, ubah target nama tabel menjadi lebih ringkas, yaitu: **`bitcoin_harian`**. Klik **Next** sampai proses selesai, lalu klik **Proceed**.

#### Langkah 3: Pengujian dan Analisis Query SQL (DML)

Untuk memastikan data termigrasi dengan sempurna, dilakukan eksekusi beberapa sintaks SQL di DBeaver.

*Catatan Penting:* Karena nama kolom bawaan dataset memiliki spasi (seperti hasil perintah `PRAGMA table_info`), maka nama kolom wajib diapit tanda petik ganda (`""`).

* **Query 1: Rekor Harga Tertinggi Sepanjang Masa (All-Time High)**
```sql
SELECT "Open time", "High", "Volume" 
FROM bitcoin_harian 
ORDER BY "High" DESC 
LIMIT 5;
```

* **Query 2: Analisis Statistik Deskriptif Agregat**
```sql
SELECT 
    COUNT(*) AS Total_Hari,
    AVG("Close") AS Rata_Rata_Harga,
    MAX("High") AS Harga_Tertinggi_Maksimal,
    MIN("Low") AS Harga_Terendah_Minimal
FROM bitcoin_harian;
```

* **Query 3: Menghitung Selisih Fluktuasi Harian Terbesar**
```sql
SELECT "Open time", "High", "Low", ("High" - "Low") AS Fluktuasi_Harian_USD
FROM bitcoin_harian 
ORDER BY Fluktuasi_Harian_USD DESC 
LIMIT 5;
```

---

**Kesimpulan Laporan:** Dataset berhasil diolah secara *hybrid* menggunakan Python (VS Code) untuk kebutuhan visualisasi grafik yang interaktif, serta berhasil dimigrasikan ke dalam Database Relasional (SQLite via DBeaver) untuk kebutuhan manajemen kueri data terstruktur.