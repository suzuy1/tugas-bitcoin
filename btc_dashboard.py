import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import mplfinance as mpf
import streamlit as st
from matplotlib.patches import Patch

# ─────────────────────────────────────────────
#  KONFIGURASI HALAMAN
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="BTC Dashboard",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS kustom — dark terminal aesthetic sesuai dunia crypto
st.markdown("""
<style>
    /* Background utama */
    .stApp { background-color: #0d1117; color: #e6edf3; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    [data-testid="stSidebar"] * { color: #e6edf3 !important; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="metric-container"] label { color: #8b949e !important; font-size: 0.78rem !important; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] { color: #e6edf3 !important; font-size: 1.3rem !important; font-weight: 700; }
    [data-testid="stMetricDelta"] svg { display: none; }

    /* Judul */
    h1 { color: #f0b429 !important; font-family: 'Courier New', monospace; letter-spacing: -0.5px; }
    h2, h3 { color: #c9d1d9 !important; }

    /* Divider */
    hr { border-color: #30363d; }

    /* Button */
    .stButton > button {
        background: #f0b429; color: #0d1117;
        font-weight: 700; border: none; border-radius: 6px;
        width: 100%; padding: 10px;
    }
    .stButton > button:hover { background: #ffd166; color: #0d1117; }

    /* Download button */
    .stDownloadButton > button {
        background: #21262d; color: #58a6ff;
        border: 1px solid #30363d; border-radius: 6px;
        width: 100%;
    }
    .stDownloadButton > button:hover { background: #30363d; }

    /* Selectbox & date_input */
    .stSelectbox > div > div, .stDateInput > div > div {
        background: #21262d; border: 1px solid #30363d; color: #e6edf3;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  KONSTANTA
# ─────────────────────────────────────────────
FILE_MAPPING = {
    '1d':  'btc_1d_data_2018_to_2025.csv',
    '4h':  'btc_4h_data_2018_to_2025.csv',
    '1h':  'btc_1h_data_2018_to_2025.csv',
    '15m': 'btc_15m_data_2018_to_2025.csv'
}
KOLOM_TANGGAL  = ['date', 'open time', 'timestamp', 'time']
KOLOM_OPEN     = ['open']
KOLOM_HIGH     = ['high']
KOLOM_LOW      = ['low']
KOLOM_CLOSE    = ['close', 'price', 'harga']
KOLOM_VOLUME   = ['volume']

BTC_HALVING = {
    '2020-05-11': 'Halving 2020',
    '2024-04-20': 'Halving 2024',
}

WARNA = {
    'bg':       '#0d1117',
    'panel':    '#161b22',
    'border':   '#30363d',
    'emas':     '#f0b429',
    'hijau':    '#3fb950',
    'merah':    '#f85149',
    'biru':     '#58a6ff',
    'ungu':     '#bc8cff',
    'abu':      '#8b949e',
    'teks':     '#e6edf3',
    'ma20':     '#58a6ff',
    'ma50':     '#ffa657',
    'ma200':    '#bc8cff',
}


# ─────────────────────────────────────────────
#  FUNGSI UTILITAS
# ─────────────────────────────────────────────
def deteksi_kolom(df_cols, kandidat):
    cols_lower = {c.lower(): c for c in df_cols}
    for k in kandidat:
        if k in cols_lower:
            return cols_lower[k]
    return None


@st.cache_data(show_spinner=False)
def load_dataframe(tf: str) -> pd.DataFrame:
    """Baca CSV, standarisasi kolom, cache per timeframe."""
    df = pd.read_csv(FILE_MAPPING[tf])
    df.columns = df.columns.str.strip()

    # Deteksi kolom
    kol = {
        'tanggal': deteksi_kolom(df.columns, KOLOM_TANGGAL),
        'open':    deteksi_kolom(df.columns, KOLOM_OPEN),
        'high':    deteksi_kolom(df.columns, KOLOM_HIGH),
        'low':     deteksi_kolom(df.columns, KOLOM_LOW),
        'close':   deteksi_kolom(df.columns, KOLOM_CLOSE),
        'volume':  deteksi_kolom(df.columns, KOLOM_VOLUME),
    }

    missing = [k for k, v in kol.items() if v is None and k != 'volume']
    if missing:
        raise ValueError(f"Kolom tidak ditemukan: {missing}. Kolom tersedia: {list(df.columns)}")

    # Parse tanggal
    raw = df[kol['tanggal']]
    if raw.dtype in ['int64', 'float64'] and raw.max() > 1e11:
        df['Tanggal_Fix'] = pd.to_datetime(raw, unit='ms')
    else:
        df['Tanggal_Fix'] = pd.to_datetime(raw)

    if df['Tanggal_Fix'].dt.tz is not None:
        df['Tanggal_Fix'] = df['Tanggal_Fix'].dt.tz_convert('UTC').dt.tz_localize(None)

    # Standarisasi kolom OHLCV
    for dest, src_key in [('Open','open'),('High','high'),('Low','low'),('Close','close')]:
        df[dest] = pd.to_numeric(df[kol[src_key]], errors='coerce')

    if kol['volume']:
        df['Volume'] = pd.to_numeric(df[kol['volume']], errors='coerce').fillna(0)
    else:
        df['Volume'] = 0

    df = (df.dropna(subset=['Open','High','Low','Close'])
            .sort_values('Tanggal_Fix')
            .reset_index(drop=True))
    return df


def hitung_ma(series, window):
    return series.rolling(window=window, min_periods=1).mean()


def hitung_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs  = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def hitung_drawdown(series):
    rolling_max = series.cummax()
    dd = (series - rolling_max) / rolling_max * 100
    return dd


def format_usd(val):
    if val >= 1_000:
        return f"${val:,.0f}"
    return f"${val:,.2f}"


# ─────────────────────────────────────────────
#  SIDEBAR — KONTROL
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ₿ BTC Dashboard")
    st.markdown("---")

    tf = st.selectbox(
        "Timeframe",
        ["1d", "4h", "1h", "15m"],
        format_func=lambda x: {
            "1d":  "📅  1 Hari  (1D) — Ringan",
            "4h":  "🕓  4 Jam  (4H) — Sedang",
            "1h":  "🕐  1 Jam  (1H) — Berat",
            "15m": "⚡  15 Menit (15M) — Sangat Berat"
        }[x]
    )

    st.markdown("#### Rentang Tanggal")
    min_limit = pd.to_datetime('2018-01-01').date()
    max_limit = pd.to_datetime('2025-12-31').date()

    start_date = st.date_input("Dari", value=pd.to_datetime('2023-01-01').date(),
                               min_value=min_limit, max_value=max_limit)
    end_date   = st.date_input("Hingga", value=max_limit,
                               min_value=min_limit, max_value=max_limit)

    st.markdown("#### Indikator Moving Average")
    tampil_ma20  = st.checkbox("MA 20",  value=True)
    tampil_ma50  = st.checkbox("MA 50",  value=True)
    tampil_ma200 = st.checkbox("MA 200", value=False)

    st.markdown("#### Overlay & Anotasi")
    tampil_volume   = st.checkbox("Volume Bars",       value=True)
    tampil_drawdown = st.checkbox("Drawdown Chart",    value=True)
    tampil_halving  = st.checkbox("Anotasi Halving",   value=True)

    st.markdown("---")
    btn_proses = st.button("▶  Tampilkan Grafik", type="primary")


# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown("# ₿  Bitcoin Historical Dashboard")
st.caption("Analisis harga historis Bitcoin 2018–2025 dengan indikator teknikal.")
st.markdown("---")


# ─────────────────────────────────────────────
#  PROSES & RENDER
# ─────────────────────────────────────────────
if btn_proses:

    # Validasi tanggal
    if start_date >= end_date:
        st.error("❌ Tanggal mulai harus sebelum tanggal selesai.")
        st.stop()

    with st.spinner(f"Memuat data {tf.upper()}..."):
        try:
            df_full = load_dataframe(tf)
        except FileNotFoundError:
            st.error(f"❌ File `{FILE_MAPPING[tf]}` tidak ditemukan di folder ini.")
            st.stop()
        except ValueError as e:
            st.error(f"❌ Struktur file bermasalah: {e}")
            st.stop()
        except Exception as e:
            st.error(f"❌ Gagal membaca data: {e}")
            st.stop()

    # Filter tanggal
    start_dt = pd.to_datetime(start_date)
    end_dt   = pd.to_datetime(end_date)
    df = df_full[(df_full['Tanggal_Fix'] >= start_dt) & (df_full['Tanggal_Fix'] <= end_dt)].copy()

    if df.empty:
        st.warning("⚠️ Tidak ada data pada rentang tanggal tersebut.")
        st.stop()

    # ── Hitung indikator ──────────────────────
    df['MA20']     = hitung_ma(df['Close'], 20)
    df['MA50']     = hitung_ma(df['Close'], 50)
    df['MA200']    = hitung_ma(df['Close'], 200)
    df['RSI']      = hitung_rsi(df['Close'])
    df['Drawdown'] = hitung_drawdown(df['Close'])

    # ── Statistik ringkas ─────────────────────
    harga_awal   = df.iloc[0]['Close']
    harga_akhir  = df.iloc[-1]['Close']
    harga_max    = df['High'].max()
    harga_min    = df['Low'].min()
    pct_change   = (harga_akhir - harga_awal) / harga_awal * 100
    max_drawdown = df['Drawdown'].min()
    volatilitas  = df['Close'].pct_change().std() * 100
    hari_naik    = (df['Close'].diff() > 0).sum()
    hari_turun   = (df['Close'].diff() < 0).sum()
    win_rate     = hari_naik / (hari_naik + hari_turun) * 100 if (hari_naik + hari_turun) > 0 else 0

    # ── Metrik cards ──────────────────────────
    st.markdown("### 📊 Ringkasan Performa")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Harga Awal",   format_usd(harga_awal))
    col2.metric("Harga Akhir",  format_usd(harga_akhir),
                delta=f"{pct_change:+.2f}%",
                delta_color="normal")
    col3.metric("Tertinggi (High)", format_usd(harga_max))
    col4.metric("Terendah (Low)",   format_usd(harga_min))

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Max Drawdown",    f"{max_drawdown:.2f}%")
    col6.metric("Volatilitas Harian", f"{volatilitas:.2f}%")
    col7.metric("Win Rate Candle",  f"{win_rate:.1f}%")
    col8.metric("Total Candle",     f"{len(df):,}")

    st.markdown("---")

    # ── GRAFIK UTAMA ──────────────────────────
    # Tentukan jumlah subplot secara dinamis
    n_panel = 1
    if tampil_volume:   n_panel += 1
    if tampil_drawdown: n_panel += 1

    # Rasio tinggi panel
    height_ratios = [4]
    if tampil_volume:   height_ratios.append(1)
    if tampil_drawdown: height_ratios.append(1.2)

    fig = plt.figure(figsize=(14, 4 + 1.8 * (n_panel - 1)))
    fig.patch.set_facecolor(WARNA['bg'])

    gs = gridspec.GridSpec(n_panel, 1, height_ratios=height_ratios, hspace=0.06)

    tanggal = df['Tanggal_Fix'].values
    panel_idx = 0

    # ── Panel 1: Candlestick + MA ─────────────
    ax_price = fig.add_subplot(gs[panel_idx])
    ax_price.set_facecolor(WARNA['panel'])
    panel_idx += 1

    # Gambar candlestick manual (matplotlib)
    td = (tanggal[-1] - tanggal[0]) / len(tanggal) * 0.6
    width_candle = np.timedelta64(int(td / np.timedelta64(1, 'ns')), 'ns')

    for i, row in df.iterrows():
        t   = row['Tanggal_Fix']
        op  = row['Open']
        hi  = row['High']
        lo  = row['Low']
        cl  = row['Close']
        col = WARNA['hijau'] if cl >= op else WARNA['merah']
        alpha = 0.9

        # Wick
        ax_price.plot([t, t], [lo, hi], color=col, linewidth=0.6, alpha=alpha)
        # Body
        body_lo = min(op, cl)
        body_hi = max(op, cl)
        ax_price.bar(t, body_hi - body_lo, bottom=body_lo,
                     width=width_candle, color=col, alpha=alpha, linewidth=0)

    # MA overlay
    if tampil_ma20:
        ax_price.plot(df['Tanggal_Fix'], df['MA20'],
                      color=WARNA['ma20'], linewidth=1.0, label='MA 20', alpha=0.85)
    if tampil_ma50:
        ax_price.plot(df['Tanggal_Fix'], df['MA50'],
                      color=WARNA['ma50'], linewidth=1.0, label='MA 50', alpha=0.85)
    if tampil_ma200:
        ax_price.plot(df['Tanggal_Fix'], df['MA200'],
                      color=WARNA['ma200'], linewidth=1.2, label='MA 200', alpha=0.85)

    # Anotasi halving
    if tampil_halving:
        for tgl_str, label in BTC_HALVING.items():
            tgl = pd.to_datetime(tgl_str)
            if start_dt <= tgl <= end_dt:
                ax_price.axvline(tgl, color=WARNA['emas'], linewidth=0.8,
                                 linestyle='--', alpha=0.7)
                ax_price.text(tgl, ax_price.get_ylim()[1] * 0.95, f' {label}',
                              color=WARNA['emas'], fontsize=7, va='top',
                              rotation=90, alpha=0.8)

    # Style panel harga
    ax_price.set_ylabel('Harga (USD)', color=WARNA['abu'], fontsize=9)
    ax_price.yaxis.set_label_position('right')
    ax_price.yaxis.tick_right()
    ax_price.tick_params(colors=WARNA['abu'], labelsize=8)
    ax_price.set_xticklabels([])
    for spine in ax_price.spines.values():
        spine.set_edgecolor(WARNA['border'])
    ax_price.grid(True, linestyle='--', alpha=0.15, color=WARNA['abu'])

    # Legend
    legend_items = []
    legend_items.append(Patch(color=WARNA['hijau'], label='Bullish'))
    legend_items.append(Patch(color=WARNA['merah'], label='Bearish'))
    if tampil_ma20:
        legend_items.append(plt.Line2D([0],[0], color=WARNA['ma20'], lw=1.5, label='MA 20'))
    if tampil_ma50:
        legend_items.append(plt.Line2D([0],[0], color=WARNA['ma50'], lw=1.5, label='MA 50'))
    if tampil_ma200:
        legend_items.append(plt.Line2D([0],[0], color=WARNA['ma200'], lw=1.5, label='MA 200'))

    ax_price.legend(handles=legend_items, loc='upper left',
                    facecolor=WARNA['panel'], edgecolor=WARNA['border'],
                    labelcolor=WARNA['teks'], fontsize=7.5)

    # Title
    ax_price.set_title(
        f'Bitcoin / USD  ·  {tf.upper()}  ·  {start_date} → {end_date}',
        color=WARNA['teks'], fontsize=10, fontweight='bold', pad=8, loc='left'
    )

    # ── Panel 2: Volume (opsional) ────────────
    if tampil_volume:
        ax_vol = fig.add_subplot(gs[panel_idx], sharex=ax_price)
        ax_vol.set_facecolor(WARNA['panel'])
        panel_idx += 1

        vol_colors = [WARNA['hijau'] if r['Close'] >= r['Open'] else WARNA['merah']
                      for _, r in df.iterrows()]
        ax_vol.bar(df['Tanggal_Fix'], df['Volume'],
                   width=width_candle, color=vol_colors, alpha=0.6, linewidth=0)

        ax_vol.set_ylabel('Volume', color=WARNA['abu'], fontsize=8)
        ax_vol.yaxis.set_label_position('right')
        ax_vol.yaxis.tick_right()
        ax_vol.tick_params(colors=WARNA['abu'], labelsize=7)
        ax_vol.set_xticklabels([])
        for spine in ax_vol.spines.values():
            spine.set_edgecolor(WARNA['border'])
        ax_vol.grid(True, linestyle='--', alpha=0.1, color=WARNA['abu'])

        # Format angka volume (K / M)
        ax_vol.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f'{x/1e9:.1f}B' if x >= 1e9
                              else (f'{x/1e6:.1f}M' if x >= 1e6
                                    else f'{x/1e3:.0f}K'))
        )

    # ── Panel 3: Drawdown (opsional) ──────────
    if tampil_drawdown:
        ax_dd = fig.add_subplot(gs[panel_idx], sharex=ax_price)
        ax_dd.set_facecolor(WARNA['panel'])

        ax_dd.fill_between(df['Tanggal_Fix'], df['Drawdown'], 0,
                           color=WARNA['merah'], alpha=0.35, label='Drawdown')
        ax_dd.plot(df['Tanggal_Fix'], df['Drawdown'],
                   color=WARNA['merah'], linewidth=0.7, alpha=0.8)
        ax_dd.axhline(0, color=WARNA['border'], linewidth=0.5)

        # Garis max drawdown
        ax_dd.axhline(max_drawdown, color=WARNA['emas'], linewidth=0.7,
                      linestyle=':', alpha=0.8)
        ax_dd.text(df['Tanggal_Fix'].iloc[-1], max_drawdown,
                   f'  Max {max_drawdown:.1f}%', color=WARNA['emas'],
                   fontsize=7, va='center')

        ax_dd.set_ylabel('Drawdown %', color=WARNA['abu'], fontsize=8)
        ax_dd.yaxis.set_label_position('right')
        ax_dd.yaxis.tick_right()
        ax_dd.tick_params(colors=WARNA['abu'], labelsize=7)
        for spine in ax_dd.spines.values():
            spine.set_edgecolor(WARNA['border'])
        ax_dd.grid(True, linestyle='--', alpha=0.1, color=WARNA['abu'])

        # Format sumbu X hanya di panel paling bawah
        ax_dd.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax_dd.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax_dd.get_xticklabels(), rotation=30, ha='right',
                 fontsize=7, color=WARNA['abu'])
    else:
        # Kalau tidak ada drawdown, format x di panel volume atau harga
        last_ax = ax_vol if tampil_volume else ax_price
        last_ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        last_ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(last_ax.get_xticklabels(), rotation=30, ha='right',
                 fontsize=7, color=WARNA['abu'])

    plt.tight_layout(pad=1.0)
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("---")

    # ── DOWNLOAD CSV ──────────────────────────
    st.markdown("### ⬇️ Export Data")

    kolom_export = ['Tanggal_Fix', 'Open', 'High', 'Low', 'Close', 'Volume',
                    'MA20', 'MA50', 'MA200', 'RSI', 'Drawdown']
    kolom_export = [c for c in kolom_export if c in df.columns]
    df_export = df[kolom_export].copy()
    df_export.rename(columns={'Tanggal_Fix': 'Date'}, inplace=True)
    df_export = df_export.round(4)

    csv_bytes = df_export.to_csv(index=False).encode('utf-8')
    nama_file = f"BTC_{tf}_{start_date}_{end_date}.csv"

    col_dl1, col_dl2 = st.columns([1, 2])
    with col_dl1:
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_bytes,
            file_name=nama_file,
            mime='text/csv'
        )
    with col_dl2:
        st.caption(f"File: `{nama_file}`  ·  {len(df_export):,} baris  ·  {len(kolom_export)} kolom (OHLCV + MA + RSI + Drawdown)")

else:
    # State awal — panduan singkat
    st.info("👈 Pilih **timeframe** dan **rentang tanggal** di sidebar, lalu klik **Tampilkan Grafik**.")

    col_g1, col_g2, col_g3 = st.columns(3)
    col_g1.markdown("""
**📈 Candlestick Chart**
Visualisasi OHLC lengkap dengan warna hijau/merah untuk membaca arah candle secara instan.
""")
    col_g2.markdown("""
**📉 Drawdown Chart**
Seberapa dalam BTC turun dari puncaknya di periode yang dipilih.
""")
    col_g3.markdown("""
**⬇️ Export CSV**
Download data yang sudah difilter beserta indikator MA, RSI, dan Drawdown siap pakai.
""")