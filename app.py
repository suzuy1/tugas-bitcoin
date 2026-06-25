import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. KONFIGURASI HALAMAN DASHBOARD (WIDE MODE)
st.set_page_config(page_title="Bitcoin Pro Analytics", layout="wide")

st.title("📈 Bitcoin Professional Hybrid Analytics Dashboard")
st.write("Platform analisis teknikal dan manajemen risiko tingkat lanjut untuk data historis Bitcoin (2018 - 2025).")

FILE_MAPPING = {
    '1d': 'btc_1d_data_2018_to_2025.csv',
    '4h': 'btc_4h_data_2018_to_2025.csv',
    '1h': 'btc_1h_data_2018_to_2025.csv',
    '15m': 'btc_15m_data_2018_to_2025.csv'
}

# 2. ENGINE PEMROSESAN DATA & KALKULASI INDIKATOR (DENGAN CACHING)
@st.cache_data
def load_and_calculate_indicators(tf: str) -> pd.DataFrame:
    file_name = FILE_MAPPING[tf]
    df = pd.read_csv(file_name)
    df.columns = df.columns.str.strip()

    # Identifikasi Kolom OHLCV secara ketat
    col_tgl = next((c for c in df.columns if c.lower() in ['date', 'open time', 'timestamp', 'time']), None)
    col_op  = next((c for c in df.columns if c.lower() == 'open'), None)
    col_hi  = next((c for c in df.columns if c.lower() == 'high'), None)
    col_lo  = next((c for c in df.columns if c.lower() == 'low'), None)
    col_cl  = next((c for c in df.columns if c.lower() in ['close', 'price', 'harga']), None)
    col_vol = next((c for c in df.columns if c.lower() in ['volume', 'vol.', 'vol']), None)

    if not all([col_tgl, col_op, col_hi, col_lo, col_cl, col_vol]):
        raise ValueError("File CSV tidak memiliki struktur standar OHLCV.")

    # Standardisasi Tipe Data
    if df[col_tgl].dtype in ['int64', 'float64'] and df[col_tgl].max() > 1e11:
        df['Date_Fix'] = pd.to_datetime(df[col_tgl], unit='ms')
    else:
        df['Date_Fix'] = pd.to_datetime(df[col_tgl])

    if df['Date_Fix'].dt.tz is not None:
        df['Date_Fix'] = df['Date_Fix'].dt.tz_convert('UTC').dt.tz_localize(None)

    for col, target in [(col_op, 'Open'), (col_hi, 'High'), (col_lo, 'Low'), (col_cl, 'Close'), (col_vol, 'Volume')]:
        df[target] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume']).sort_values('Date_Fix').reset_index(drop=True)

    # KALKULASI INDIKATOR TEKNIKAL
    # Moving Averages
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()

    # RSI 14
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    # Daily Return untuk statistik volatilitas
    df['Return'] = df['Close'].pct_change()

    return df

# 3. ELEMEN UI - KONTROL PANEL (SIDEBAR)
with st.sidebar:
    st.header("🛠️ Pengaturan Analisis")
    tf = st.selectbox(
        "Timeframe:", ["1d", "4h", "1h", "15m"],
        format_func=lambda x: {'1d': 'Harian (1d)', '4h': '4 Jam (4h)', '1h': '1 Jam (1h)', '15m': '15 Menit (15m)'}[x]
    )
    
    min_limit, max_limit = pd.to_datetime('2018-01-01'), pd.to_datetime('2025-12-31')
    start_date = st.date_input("Tanggal Mulai:", value=pd.to_datetime('2024-01-01'), min_value=min_limit, max_value=max_limit)
    end_date = st.date_input("Tanggal Selesai:", value=max_limit, min_value=min_limit, max_value=max_limit)
    
    st.markdown("---")
    show_ma20 = st.checkbox("Tampilkan MA20 (Short)", value=True)
    show_ma50 = st.checkbox("Tampilkan MA50 (Medium)", value=True)
    show_ma200 = st.checkbox("Tampilkan MA200 (Long)", value=False)

# 4. EKSEKUSI DATA PIPELINE
if start_date > end_date:
    st.error("❌ ERROR: Tanggal Mulai tidak boleh melewati Tanggal Selesai!")
else:
    try:
        df_all = load_and_calculate_indicators(tf)
        
        # Saring data berdasarkan input user
        start_dt, end_dt = pd.to_datetime(start_date), pd.to_datetime(end_date)
        data_terfilter = df_all[(df_all['Date_Fix'] >= start_dt) & (df_all['Date_Fix'] <= end_dt)].copy()

        if data_terfilter.empty:
            st.warning("❌ Tidak ada data pada rentang tanggal tersebut.")
        else:
            # KALKULASI DRAWDOWN RISK
            rolling_max = data_terfilter['Close'].cummax()
            data_terfilter['Drawdown'] = (data_terfilter['Close'] - rolling_max) / rolling_max * 100
            max_dd = data_terfilter['Drawdown'].min()

            # Rangkuman Data Dasar
            harga_awal  = data_terfilter.iloc[0]['Close']
            harga_akhir = data_terfilter.iloc[-1]['Close']
            pct_change  = ((harga_akhir - harga_awal) / harga_awal) * 100

            # 5. LAYOUT METRIK UTAMA & ADVANCED STATS
            st.markdown("### 📊 Rangkuman Performa & Metrik Risiko")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Harga Penutupan", value=f"${harga_akhir:,.2f}", delta=f"{pct_change:+.2f}%")
            col2.metric("Maksimum Drawdown (Risk)", value=f"{max_dd:.2f}%", delta_color="inverse")
            
            # Kalkulasi Volatilitas & Win Rate
            volatilitas = data_terfilter['Return'].std() * 100
            hari_naik = (data_terfilter['Return'] > 0).sum()
            total_hari = len(data_terfilter)
            win_rate = (hari_naik / total_hari) * 100 if total_hari > 0 else 0

            col3.metric("Volatilitas Periode", value=f"{volatilitas:.2f}%")
            col4.metric("Rasio Hari Naik (Win Rate)", value=f"{win_rate:.1f}%")
            col5.metric("Total Baris Data", value=f"{total_hari:,}")

            # 6. PENYUSUNAN MULTI-SUBPLOT CHART (PLOTLY INTERAKTIF)
            fig = make_subplots(
                rows=4, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.04,
                row_heights=[0.5, 0.15, 0.15, 0.2]
            )

            # --- SUBPLOT 1: CANDLESTICK & MOVING AVERAGES (Bug Fixed Here) ---
            fig.add_trace(go.Candlestick(
                x=data_terfilter['Date_Fix'],
                open=data_terfilter['Open'], high=data_terfilter['High'],
                low=data_terfilter['Low'], close=data_terfilter['Close'],
                name="Harga BTC"
            ), row=1, col=1)

            if show_ma20:
                fig.add_trace(go.Scatter(x=data_terfilter['Date_Fix'], y=data_terfilter['MA20'], line=dict(color='#1f77b4', width=1.2), name='MA20'), row=1, col=1)
            if show_ma50:
                fig.add_trace(go.Scatter(x=data_terfilter['Date_Fix'], y=data_terfilter['MA50'], line=dict(color='#ff7f0e', width=1.2), name='MA50'), row=1, col=1)
            if show_ma200:
                fig.add_trace(go.Scatter(x=data_terfilter['Date_Fix'], y=data_terfilter['MA200'], line=dict(color='#2ca02c', width=1.5), name='MA200'), row=1, col=1)

            # --- SUBPLOT 2: VOLUME BARS ---
            colors = ['green' if cl >= op else 'red' for op, cl in zip(data_terfilter['Open'], data_terfilter['Close'])]
            fig.add_trace(go.Bar(
                x=data_terfilter['Date_Fix'], y=data_terfilter['Volume'],
                marker_color=colors, name="Volume", opacity=0.8
            ), row=2, col=1)

            # --- SUBPLOT 3: RSI 14 ---
            fig.add_trace(go.Scatter(x=data_terfilter['Date_Fix'], y=data_terfilter['RSI'], line=dict(color='#9467bd', width=1.5), name='RSI 14'), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=1, row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", line_width=1, row=3, col=1)

            # --- SUBPLOT 4: DRAWDOWN AREA ---
            fig.add_trace(go.Scatter(
                x=data_terfilter['Date_Fix'], y=data_terfilter['Drawdown'],
                fill='tozeroy', line=dict(color='rgba(214, 39, 40, 0.8)', width=1),
                name='Drawdown %', fillcolor='rgba(214, 39, 40, 0.2)'
            ), row=4, col=1)

            # PENYETELAN LAYOUT UTAMA GRAPH (DARK THEME)
            fig.update_layout(
                template="plotly_dark",
                height=800,
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_yaxes(title_text="Harga (USD)", row=1, col=1)
            fig.update_yaxes(title_text="Volume", row=2, col=1)
            fig.update_yaxes(title_text="RSI", range=[10, 90], row=3, col=1)
            fig.update_yaxes(title_text="DD %", range=[-100, 5], row=4, col=1)

            # Render Chart ke Web Streamlit
            st.plotly_chart(fig, use_container_width=True)

            # 7. FITUR EXPORT DATA KE CSV
            st.markdown("### 💾 Ekspor Data Hasil Filter")
            csv_data = data_terfilter.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download CSV Terfilter",
                data=csv_data,
                file_name=f"btc_filtered_{tf}_{start_date}_to_{end_date}.csv",
                mime="text/csv"
            )

    except FileNotFoundError:
        st.error(f"❌ File tidak ditemukan. Pastikan file CSV ditaruh sefolder dengan app.py.")
    except Exception as e:
        st.error(f"❌ Terjadi kesalahan sistem: {e}")