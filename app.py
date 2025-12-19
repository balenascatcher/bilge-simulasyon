import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import json

# Configuration
EXCEL_FILE = "mail_merge_wide_3kalem.xlsx"
LOG_FILE = "student_logs.json"
ADMIN_PASSWORD = "trakya_gumruk"

# Page Config
st.set_page_config(page_title="Trakya Üniversitesi - BİLGE Simülasyonu", layout="wide")

# Custom CSS for Trakya University Colors (Blue-White) and BİLGE Style
st.markdown("""
    <style>
    .main {
        background-color: #ffffff;
    }
    [data-testid="stForm"] {
        background-color: #ffffff;
        border: 1px solid #004a99;
        padding: 20px;
        border-radius: 10px;
    }
    [data-testid="stExpander"] {
        background-color: #ffffff;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #ffffff;
    }
    .stButton>button {
        background-color: #004a99;
        color: white;
        border-radius: 4px;
        font-weight: bold;
        width: 100%;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        border-color: #004a99;
    }
    h1, h2, h3 {
        color: #004a99;
        border-bottom: 2px solid #004a99;
        padding-bottom: 10px;
    }
    .section-header {
        background-color: #004a99;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .bilge-box {
        border: 1px solid #dee2e6;
        padding: 15px;
        border-radius: 5px;
        background-color: white;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# Load Data
@st.cache_data
def get_all_assignments():
    if os.path.exists(EXCEL_FILE):
        xl = pd.ExcelFile(EXCEL_FILE)
        return xl.sheet_names
    return []

def load_assignment_data(sheet_name):
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
        # Fill all NaN values with "---" for strings and 0 for numbers
        # First, handle numeric columns
        numeric_cols = ['Toplam_Fatura_Değeri', 'Kap_Adedi_1', 'Net_Ağırlık_KG_1', 'Brüt_Ağırlık_KG_1', 'Kalem_Fiyatı_1',
                        'Kap_Adedi_2', 'Net_Ağırlık_KG_2', 'Brüt_Ağırlık_KG_2', 'Kalem_Fiyatı_2',
                        'Kap_Adedi_3', 'Net_Ağırlık_KG_3', 'Brüt_Ağırlık_KG_3', 'Kalem_Fiyatı_3',
                        'Toplam_Net_Ağırlık_KG', 'Toplam_Brüt_Ağırlık_KG']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Then fill remaining NaNs (strings) with "---"
        df = df.fillna("---")
        return df
    return None

# Logging Function
def log_attempt(student_no, student_name, success, errors, odev_name="Bilinmiyor"):
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "student_no": str(student_no),
        "student_name": student_name,
        "odev_no": str(odev_name),
        "success": success,
        "errors": errors
    }
    
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    
    logs.append(log_entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)

# Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'student_data' not in st.session_state:
    st.session_state.student_data = None
if 'admin_mode' not in st.session_state:
    st.session_state.admin_mode = False
if 'pending_matches' not in st.session_state:
    st.session_state.pending_matches = None

# Sidebar Navigation
st.sidebar.title("BİLGE SİSTEMİ")
st.sidebar.subheader("İthalat Beyanname Portali")
page = st.sidebar.radio("Menü", ["Öğrenci Girişi", "Dijital Beyanname", "Hoca Paneli"])

if page == "Öğrenci Girişi":
    st.title("🎓 Trakya Üniversitesi Gümrük İşletme Bölümü")
    st.subheader("Dijital Gümrük Beyanname Simülasyonu (BİLGE)")
    
    assignments = get_all_assignments()
    
    if st.session_state.logged_in:
        st.success(f"Giriş Yapıldı: {st.session_state.student_data['Öğrenci_Ad_Soyad']}")
        st.info(f"Çalışılan Ödev: {st.session_state.get('current_odev', 'Bilinmiyor')}")
        if st.button("Oturumu Kapat"):
            st.session_state.logged_in = False
            st.session_state.student_data = None
            st.rerun()
    else:
        with st.form("login_form"):
            student_no = st.text_input("Öğrenci Numarası")
            selected_odev = st.selectbox("Yapmak İstediğiniz Ödevi Seçiniz", assignments)
            submit_login = st.form_submit_button("Sisteme Giriş Yap")
            
            if submit_login:
                df_odev = load_assignment_data(selected_odev)
                if df_odev is not None:
                    try:
                        student_no_int = int(student_no)
                        match = df_odev[df_odev['Öğrenci_Numarası'] == student_no_int]
                    except ValueError:
                        match = df_odev[df_odev['Öğrenci_Numarası'].astype(str) == student_no]
                    
                    if not match.empty:
                        # Check Deadline if column exists
                        if 'Son_Teslim' in df_odev.columns:
                            deadline_val = match.iloc[0]['Son_Teslim']
                            if deadline_val != "---":
                                deadline_dt = None
                                if isinstance(deadline_val, datetime):
                                    deadline_dt = deadline_val
                                else:
                                    deadline_str = str(deadline_val)
                                    # Try multiple formats
                                    for fmt in ("%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M:%S"):
                                        try:
                                            deadline_dt = datetime.strptime(deadline_str, fmt)
                                            break
                                        except ValueError:
                                            continue
                                
                                if deadline_dt and datetime.now() > deadline_dt:
                                    st.error(f"⚠️ Bu ödevin süresi dolmuştur! (Son Teslim: {deadline_val})")
                                    st.stop()

                        st.session_state.student_data = match.iloc[0].to_dict()
                        st.session_state.current_odev = selected_odev
                        st.session_state.logged_in = True
                        
                        # Display Assignment Info
                        odev_no = st.session_state.student_data.get('Ödev_No', '---')
                        st.success(f"Hoş geldiniz, {st.session_state.student_data['Öğrenci_Ad_Soyad']}!")
                        if odev_no != "---":
                            st.info(f"📌 Ödev No: {odev_no}")
                        
                        st.rerun()
                    else:
                        st.error(f"Bu öğrenci numarası '{selected_odev}' sayfasında bulunamadı.")

        # Handle multiple matches outside the form
        if 'pending_matches' in st.session_state and st.session_state.pending_matches is not None:
            st.info(f"Numaranıza tanımlı {len(st.session_state.pending_matches)} farklı fatura bulundu.")
            selected_invoice = st.selectbox("Çalışmak istediğiniz Fatura Numarasını seçin:", 
                                          st.session_state.pending_matches['Fatura_Numarası'].tolist())
            if st.button("Seçilen Fatura ile Başla"):
                match = st.session_state.pending_matches
                st.session_state.student_data = match[match['Fatura_Numarası'] == selected_invoice].iloc[0].to_dict()
                st.session_state.logged_in = True
                st.session_state.pending_matches = None
                st.success(f"Giriş Başarılı! {selected_invoice} nolu fatura yüklendi.")
                st.rerun()

elif page == "Dijital Beyanname":
    if not st.session_state.logged_in:
        st.warning("Lütfen önce 'Öğrenci Girişi' sayfasından giriş yapınız.")
    else:
        data = st.session_state.student_data
        
        # Re-check deadline even if logged in
        son_teslim = data.get('Son_Teslim', '---')
        if son_teslim != "---":
            deadline_dt = None
            if isinstance(son_teslim, datetime):
                deadline_dt = son_teslim
            else:
                for fmt in ("%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M:%S"):
                    try:
                        deadline_dt = datetime.strptime(str(son_teslim), fmt)
                        break
                    except ValueError:
                        continue
            
            if deadline_dt and datetime.now() > deadline_dt:
                st.error(f"⚠️ Bu ödevin süresi dolmuştur! (Son Teslim: {son_teslim})")
                if st.button("Giriş Sayfasına Dön"):
                    st.session_state.logged_in = False
                    st.rerun()
                st.stop()

        st.title("📝 Gümrük İşlemleri Portalı")
        
        # Assignment Info Header
        odev_no = data.get('Ödev_No', '---')
        son_teslim = data.get('Son_Teslim', '---')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Öğrenci", data['Öğrenci_Ad_Soyad'])
        with col2:
            st.metric("Ödev No", odev_no)
        with col3:
            st.metric("Son Teslim", son_teslim)
        
        st.divider()
        
        # Main Tabs: Invoice and Declaration
        main_tabs = st.tabs(["📄 Ticari Fatura", "✍️ Beyanname Girişi"])
        
        with main_tabs[0]:
            st.subheader("Dijital Ticari Fatura")
            
            # Veri kontrolü
            if data is None:
                st.error("Veri bulunamadı. Lütfen tekrar giriş yapın.")
            else:
                # HTML içeriğini güvenli bir şekilde oluştur
                # Sayısal değerleri formatla
                f_no = data.get('Fatura_Numarası', '---')
                f_tarih = data.get('Beyan_Tarihi', '---')
                ref = data.get('Referans_Numarası', '---')
                satici = data.get('Gönderici_Adı_Adresi_VergiNo', '---')
                alici = data.get('Alıcı_Adı_Adresi', '---')
                mense = data.get('Sevk_Ülkesi_Adı_Kodu', '---')
                varis = data.get('Gideceği_Ülke_Kodu', '---')
                ilk_varis = data.get('İlk_Varış_Ülkesi_Kodu', '---')
                v_gumruk_adi = data.get('Varış Gümrük İdaresi', '---')
                tasima = data.get('Taşıma_Aracı_Kimliği', '---')
                yukleme = data.get('Boşaltma_Yeri', '---')
                rejimi = data.get('Rejim_Kodu', '---')
                b_turu = data.get('Beyanname_Türü', '---')
                t_sinir = data.get('Taşıma_Şekli_Sınır', '---')
                t_dahili = data.get('Taşıma_Şekli_Dahili', '---')
                konteyner = data.get('Konteyner_Kodu', '---')
                ticaret_ulke = data.get('Ticareti_Yapan_Ülke_Kodu', '---')
                doviz = data.get('Döviz', 'USD')
                toplam = float(data.get('Toplam_Fatura_Değeri', 0))
                
                # Banka ve Ağırlık Bilgileri
                banka = data.get('Banka_Adı_Şube', '---')
                swift = data.get('SWIFT_Kodu', '---')
                iban = data.get('IBAN', '---')
                net_toplam = data.get('Toplam_Net_Ağırlık_KG', 0)
                brut_toplam = data.get('Toplam_Brüt_Ağırlık_KG', 0)
                odeme_sekli = data.get('Ödeme_Şekli', '---')
                teslim_sekli = data.get('Teslim_Şekli_Yeri', '---')

                invoice_html = f"""<div style="border: 2px solid #004a99; padding: 30px; background-color: white; color: black; font-family: 'Times New Roman', Times, serif; line-height: 1.6;">
<div style="text-align: center; border-bottom: 3px double #004a99; padding-bottom: 10px; margin-bottom: 20px;">
<h1 style="color: #004a99; margin: 0; font-size: 28px;">TİCARİ FATURA</h1>
<div style="font-size: 14px; font-weight: bold;">(COMMERCIAL INVOICE)</div>
</div>

<div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
<div style="width: 48%; border: 1px solid #ccc; padding: 10px;">
<strong style="color: #004a99; border-bottom: 1px solid #eee; display: block; margin-bottom: 5px;">İHRACATÇI / SATICI (EXPORTER):</strong>
<div style="font-size: 14px; white-space: pre-wrap;">{satici}</div>
</div>
<div style="width: 48%; border: 1px solid #ccc; padding: 10px;">
<table style="width: 100%; font-size: 14px; border-collapse: collapse;">
<tr><td style="padding: 3px;"><b>Fatura No:</b></td><td style="padding: 3px;">{f_no}</td></tr>
<tr><td style="padding: 3px;"><b>Tarih:</b></td><td style="padding: 3px;">{f_tarih}</td></tr>
<tr><td style="padding: 3px;"><b>Referans:</b></td><td style="padding: 3px;">{ref}</td></tr>
<tr><td style="padding: 3px;"><b>Döviz:</b></td><td style="padding: 3px;">{doviz}</td></tr>
<tr><td style="padding: 3px;"><b>Beyanname Türü:</b></td><td style="padding: 3px;">{b_turu}</td></tr>
<tr><td style="padding: 3px;"><b>Çıkış Rejimi:</b></td><td style="padding: 3px;">{rejimi}</td></tr>
</table>
</div>
</div>

<div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
<div style="width: 48%; border: 1px solid #ccc; padding: 10px;">
<strong style="color: #004a99; border-bottom: 1px solid #eee; display: block; margin-bottom: 5px;">ALICI / İTHALATÇI (CONSIGNEE):</strong>
<div style="font-size: 14px; white-space: pre-wrap;">{alici}</div>
</div>
<div style="width: 48%; border: 1px solid #ccc; padding: 10px;">
<strong style="color: #004a99; border-bottom: 1px solid #eee; display: block; margin-bottom: 5px;">NAKLİYE VE LOJİSTİK BİLGİLERİ:</strong>
<div style="font-size: 13px;">
<b>Menşe Ülke:</b> {mense}<br>
<b>Gideceği Ülke:</b> {varis}<br>
<b>İlk Varış Ülkesi:</b> {ilk_varis}<br>
<b>Ticareti Yapan Ülke:</b> {ticaret_ulke}<br>
<b>Gümrük İdaresi:</b> {v_gumruk_adi}<br>
<b>Taşıma Aracı Kimliği:</b> {tasima}<br>
<b>Yükleme Yeri:</b> {yukleme}<br>
<b>Taşıma Şekli (Sınır):</b> {t_sinir}<br>
<b>Taşıma Şekli (Dahili):</b> {t_dahili}<br>
<b>Konteyner:</b> {"Evet (1)" if str(konteyner)=="1" else "Hayır (0)"}
</div>
</div>
</div>

<table style="width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 20px; border: 1px solid #004a99;">
<thead>
<tr style="background-color: #004a99; color: white; text-align: center;">
<th style="border: 1px solid #004a99; padding: 5px;">Eşyanın Tanımı</th>
<th style="border: 1px solid #004a99; padding: 5px;">GTİP</th>
<th style="border: 1px solid #004a99; padding: 5px;">Miktar/Birim</th>
<th style="border: 1px solid #004a99; padding: 5px;">Net/Brüt (KG)</th>
<th style="border: 1px solid #004a99; padding: 5px;">Kalem Fiyatı</th>
<th style="border: 1px solid #004a99; padding: 5px;">İstatistiki Kıymet</th>
<th style="border: 1px solid #004a99; padding: 5px;">Navlun/Sigorta</th>
<th style="border: 1px solid #004a99; padding: 5px;">CIF Toplam</th>
<th style="border: 1px solid #004a99; padding: 5px;">Vergiler</th>
<th style="border: 1px solid #004a99; padding: 5px;">Genel Toplam</th>
</tr>
</thead>
<tbody>
"""
                for i in range(1, 4):
                    invoice_html += f"""
<tr>
<td style="border: 1px solid #ddd; padding: 5px;">{data.get(f'Ürün_Tanımı_{i}', '---')}</td>
<td style="border: 1px solid #ddd; padding: 5px; text-align: center;">{data.get(f'GTIP_Kodu_{i}', '---')}</td>
<td style="border: 1px solid #ddd; padding: 5px; text-align: center;">{data.get(f'Kap_Adedi_{i}', 0)} {data.get(f'Tamamlayıcı_Ölçü_Birimi_{i}', '---')}</td>
<td style="border: 1px solid #ddd; padding: 5px; text-align: center;">N: {data.get(f'Net_Ağırlık_KG_{i}', 0)}<br>B: {data.get(f'Brüt_Ağırlık_KG_{i}', 0)}</td>
<td style="border: 1px solid #ddd; padding: 5px; text-align: right;">{float(data.get(f'Kalem_Fiyatı_{i}', 0)):.2f}</td>
<td style="border: 1px solid #ddd; padding: 5px; text-align: right;">{float(data.get(f'İstatistiki_Kıymet_FOB_{i}', 0)):.2f}</td>
<td style="border: 1px solid #ddd; padding: 5px; text-align: center;">N: {float(data.get(f'Navlun_Tutari_{i}', 0)):.2f}<br>S: {float(data.get(f'Sigorta_Tutari_{i}', 0)):.2f}</td>
<td style="border: 1px solid #ddd; padding: 5px; text-align: right;">{float(data.get(f'CIF_Toplam_{i}', 0)):.2f}</td>
<td style="border: 1px solid #ddd; padding: 5px; text-align: right;">{float(data.get(f'Vergiler_Toplami_{i}', 0)):.2f}</td>
<td style="border: 1px solid #ddd; padding: 5px; text-align: right;">{float(data.get(f'Toplam_Tutar_{i}', 0)):.2f}</td>
</tr>"""

                invoice_html += f"""
</tbody>
<tfoot>
<tr style="font-weight: bold; background-color: #f8f9fa;">
<td colspan="5" style="text-align: right; border: 1px solid #004a99; padding: 10px;">TOPLAMLAR:</td>
<td colspan="2" style="border: 1px solid #004a99; padding: 10px; text-align: center;">Net: {net_toplam} KG / Brüt: {brut_toplam} KG</td>
<td colspan="2" style="border: 1px solid #004a99; padding: 10px; text-align: right;">GENEL TOPLAM ({doviz}):</td>
<td style="border: 1px solid #004a99; padding: 10px; text-align: right;">{toplam:.2f}</td>
</tr>
</tfoot>
</table>

<div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
<div style="width: 60%; border: 1px solid #ccc; padding: 10px;">
<strong style="color: #004a99; border-bottom: 1px solid #eee; display: block; margin-bottom: 5px;">ÖDEME VE BANKA BİLGİLERİ:</strong>
<div style="font-size: 13px;">
<b>Ödeme Şekli:</b> {odeme_sekli}<br>
<b>Teslim Şekli:</b> {teslim_sekli}<br>
<b>Banka Adı:</b> {banka}<br>
<b>SWIFT Kodu:</b> {swift}<br>
<b>IBAN:</b> {iban}
</div>
</div>
<div style="width: 35%; border: 1px solid #ccc; padding: 10px;">
<strong style="color: #004a99; border-bottom: 1px solid #eee; display: block; margin-bottom: 5px;">EK BELGELER:</strong>
<div style="font-size: 12px;">
<b>1. Kalem:</b> {data.get('Ek_Belge_Kodu_1', '---')} ({data.get('Ek_Belge_Referans_1', '---')})<br>
<b>2. Kalem:</b> {data.get('Ek_Belge_Kodu_2', '---')} ({data.get('Ek_Belge_Referans_2', '---')})<br>
<b>3. Kalem:</b> {data.get('Ek_Belge_Kodu_3', '---')} ({data.get('Ek_Belge_Referans_3', '---')})
</div>
</div>
</div>

<div style="margin-top: 30px; display: flex; justify-content: flex-end;">
<div style="width: 250px; text-align: center; border-top: 1px solid #000; padding-top: 5px;">
<b style="font-size: 14px;">Yetkili İmza ve Kaşe</b>
</div>
</div>
</div>"""
                st.markdown(invoice_html, unsafe_allow_html=True)
                st.info("💡 Yukarıdaki faturadaki bilgileri kullanarak yan sekmedeki beyannameyi doldurunuz.")

        with main_tabs[1]:
            st.write(f"**Beyan Sahibi:** {data['Öğrenci_Ad_Soyad']} | **Fatura No:** {data['Fatura_Numarası']}")
            
            with st.form("bilge_form"):
                # SECTION 1: GENEL BILGILER & TARAFLAR
                st.markdown('<div class="section-header">1. GENEL BİLGİLER & TARAFLAR</div>', unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    v_gumruk = st.text_input("Varış Gümrük İdaresi (Box A)", help="Örn: Kapıkule Gümrük Müdürlüğü")
                    b_turu = st.text_input("Beyanname Türü (Box 1)", help="Örn: IM")
                    c_rejimi = st.text_input("Çıkış Rejimi (Box 1)", help="Örn: 1000")
                    ref_no = st.text_input("Referans Numarası (Box 7)")
                with col2:
                    gonderici = st.text_area("Gönderici/İhracatçı (Box 2)", help="Ad, Adres ve Vergi No")
                    alici = st.text_area("Alıcı (Box 8)", help="Ad, Adres ve Verig No")
                with col3:
                    temsilci = st.text_area("Beyan Sahibi/Temsilci (Box 14)", help="Ad, Adres ve Vergi No")
                    b_yeri = st.text_input("Beyan Yeri")
                    b_tarihi = st.text_input("Beyan Tarihi (GG.AA.YYYY)")

                # SECTION 2: TASIMA VE FINANS
                st.markdown('<div class="section-header">2. TAŞIMA VE FİNANSAL BİLGİLER</div>', unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                with c1:
                    sevk_ulke = st.text_input("Sevk Ülkesi Kodu (Box 15)")
                    ticaret_ulke = st.text_input("Ticareti Yapan Ülke Kodu(Box 11)")
                    gidecek_ulke = st.text_input("Gideceği Ülke Kodu (Box 17)")
                    ilk_varis_ulke = st.text_input("İlk Varış Ülkesi Kodu (Box 17)")
                with c2:
                    tasima_araci = st.text_input("Taşıma Aracı Kimliği (Box 18/21)")
                    konteyner = st.text_input("Konteyner (Box 19)", help="0 veya 1")
                    teslim_sekli = st.text_input("Teslim Şekli ve Yeri (Box 20)", help="Örn: FCA - Viyana")
                with c3:
                    tasima_sinir = st.text_input("Taşıma Şekli - Sınır (Box 25)")
                    tasima_dahili = st.text_input("Taşıma Şekli - Dahili (Box 26)")
                    yukleme_yeri = st.text_input("Yükleme Yeri (Box 27)")

                st.divider()
                f1, f2, f3 = st.columns(3)
                with f1:
                    doviz = st.text_input("Döviz (Box 22)", help="Örn: EUR, USD")
                    top_fatura = st.number_input("Toplam Fatura Değeri", format="%.2f")
                with f2:
                    odeme_sekli = st.text_input("Ödeme Şekli (Box 28)")
                    banka = st.text_input("Banka Adı / Şube")
                    top_net = st.number_input("Toplam Net Ağırlık (KG)", format="%.2f")
                with f3:
                    iban = st.text_input("IBAN")
                    swift = st.text_input("SWIFT Kodu")
                    top_brut = st.number_input("Toplam Brüt Ağırlık (KG)", format="%.2f")

                # SECTION 3: KALEMLER
                st.markdown('<div class="section-header">3. KALEM DETAYLARI (EŞYA BİLGİLERİ)</div>', unsafe_allow_html=True)
                
                tabs = st.tabs(["Kalem 1", "Kalem 2", "Kalem 3"])
                
                for i, tab in enumerate(tabs, 1):
                    with tab:
                        k1, k2 = st.columns(2)
                        with k1:
                            st.text_input(f"GTİP Kodu (Box 33) - Kalem {i}", key=f"gtip_{i}")
                            st.text_area(f"Eşya Tanımı (Box 31) - Kalem {i}", key=f"tanim_{i}")
                            st.text_input(f"Menşe Ülke Kodu (Box 34) - Kalem {i}", key=f"mense_{i}")
                            st.text_input(f"Tamamlayıcı Ölçü Birimi (Box 41) - Kalem {i}", key=f"birim_{i}")
                            st.text_input(f"Ek Belge Kodu (Box 44) - Kalem {i}", key=f"ek_kod_{i}")
                            st.text_input(f"Ek Belge Referansı - Kalem {i}", key=f"ek_ref_{i}")
                        with k2:
                            st.text_input(f"Kap Cinsi (Box 31) - Kalem {i}", key=f"kap_cinsi_{i}")
                            st.number_input(f"Kap Adedi - Kalem {i}", key=f"kap_adet_{i}", step=1)
                            st.number_input(f"Net Ağırlık (KG) (Box 38) - Kalem {i}", key=f"net_{i}", format="%.2f")
                            st.number_input(f"Brüt Ağırlık (KG) (Box 35) - Kalem {i}", key=f"gross_{i}", format="%.2f")
                            st.number_input(f"Kalem Fiyatı (Box 42) - Kalem {i}", key=f"fiyat_{i}", format="%.2f")

                        st.markdown("**Vergi Hesaplamaları (Box 47)**")
                        v1, v2, v3, v4  = st.columns(4)
                        with v1:
                            st.number_input(f"İstatistik Kıymet (FOB) - Kalem {i}", key=f"fob_{i}", format="%.4f")
                            st.number_input(f"Navlun Tutarı - Kalem {i}", key=f"navlun_{i}", format="%.4f")
                        with v2:
                            st.number_input(f"Sigorta Tutarı - Kalem {i}", key=f"sigorta_{i}", format="%.4f")
                            st.number_input(f"Matrah (CIF Toplam) - Kalem {i}", key=f"cif_{i}", format="%.4f")
                        with v3:
                            st.number_input(f"Gümrük Vergisi (GV) - Kalem {i}", key=f"gv_{i}", format="%.4f")
                            st.number_input(f"ÖTV Tutarı - Kalem {i}", key=f"otv_{i}", format="%.4f")
                        with v4:
                            st.number_input(f"KDV Tutarı - Kalem {i}", key=f"kdv_{i}", format="%.4f")
                            st.number_input(f"Vergiler Toplamı - Kalem {i}", key=f"v_toplam_{i}", format="%.4f")

                st.divider()
                submit_decl = st.form_submit_button("BEYANNAMEYİ TESCİL ET (GÖNDER)")
                
                if submit_decl:
                    errors = []
                    
                    # Helper to compare strings (case-insensitive, stripped)
                    def check_str(input_val, correct_val, field_name):
                        if str(input_val).strip().lower() != str(correct_val).strip().lower():
                            errors.append(f"{field_name} hatalı.")

                    # Helper to compare numbers (with tolerance)
                    def check_num(input_val, correct_val, field_name, tol=0.1):
                        try:
                            if abs(float(input_val) - float(correct_val)) > tol:
                                errors.append(f"{field_name} hatalı veya eksik hesaplanmış.")
                        except:
                            errors.append(f"{field_name} sayısal bir değer olmalıdır.")

                    # Validation - General
                    check_str(v_gumruk, data['Varış Gümrük İdaresi'], "Varış Gümrük İdaresi")
                    check_str(b_turu, data['Beyanname_Türü'], "Beyanname Türü")
                    check_str(c_rejimi, data['Rejim_Kodu'], "Çıkış Rejimi")
                    check_str(ref_no, data['Referans_Numarası'], "Referans Numarası")
                    check_str(gonderici, data['Gönderici_Adı_Adresi_VergiNo'], "Gönderici Bilgileri")
                    check_str(alici, data['Alıcı_Adı_Adresi'], "Alıcı Bilgileri")
                    check_str(temsilci, data['Beyan_Sahibi_Temsilci'], "Beyan Sahibi/Temsilci")
                    check_str(b_yeri, data['Beyan_Yeri'], "Beyan Yeri")
                    check_str(b_tarihi, data['Beyan_Tarihi'], "Beyan Tarihi")
                    
                    # Validation - Tasima/Finans
                    check_str(sevk_ulke, data['Sevk_Ülkesi_Adı_Kodu'], "Sevk Ülkesi")
                    check_str(ticaret_ulke, data['Ticareti_Yapan_Ülke_Kodu'], "Ticareti Yapan Ülke")
                    check_str(gidecek_ulke, data['Gideceği_Ülke_Kodu'], "Gideceği Ülke")
                    check_str(ilk_varis_ulke, data['İlk_Varış_Ülkesi_Kodu'], "İlk Varış Ülkesi")
                    check_str(tasima_araci, data['Taşıma_Aracı_Kimliği'], "Taşıma Aracı")
                    check_str(konteyner, data['Konteyner_Kodu'], "Konteyner Kodu")
                    check_str(teslim_sekli, data['Teslim_Şekli_Yeri'], "Teslim Şekli")
                    check_str(tasima_sinir, data['Taşıma_Şekli_Sınır'], "Taşıma Şekli (Sınır)")
                    check_str(tasima_dahili, data['Taşıma_Şekli_Dahili'], "Taşıma Şekli (Dahili)")
                    check_str(yukleme_yeri, data['Boşaltma_Yeri'], "Yükleme Yeri")
                    check_str(doviz, data['Döviz'], "Döviz")
                    check_num(top_fatura, data['Toplam_Fatura_Değeri'], "Toplam Fatura Değeri")
                    check_num(top_net, data['Toplam_Net_Ağırlık_KG'], "Toplam Net Ağırlık")
                    check_num(top_brut, data['Toplam_Brüt_Ağırlık_KG'], "Toplam Brüt Ağırlık")
                    check_str(odeme_sekli, data['Ödeme_Şekli'], "Ödeme Şekli")
                    check_str(banka, data['Banka_Adı_Şube'], "Banka Bilgisi")
                    check_str(iban, data['IBAN'], "IBAN")
                    check_str(swift, data['SWIFT_Kodu'], "SWIFT Kodu")

                    # Validation - Items
                    for i in range(1, 4):
                        check_str(st.session_state[f"gtip_{i}"], data[f'GTIP_Kodu_{i}'], f"Kalem {i}: GTİP")
                        check_str(st.session_state[f"tanim_{i}"], data[f'Ürün_Tanımı_{i}'], f"Kalem {i}: Ürün Tanımı")
                        check_str(st.session_state[f"mense_{i}"], data[f'Menşe_Ülke_Kodu_{i}'], f"Kalem {i}: Menşe Ülke")
                        check_str(st.session_state[f"birim_{i}"], data[f'Tamamlayıcı_Ölçü_Birimi_{i}'], f"Kalem {i}: Tamamlayıcı Ölçü Birimi")
                        check_str(st.session_state[f"ek_kod_{i}"], data[f'Ek_Belge_Kodu_{i}'], f"Kalem {i}: Ek Belge Kodu")
                        check_str(st.session_state[f"ek_ref_{i}"], data[f'Ek_Belge_Referans_{i}'], f"Kalem {i}: Ek Belge Referansı")
                        check_str(st.session_state[f"kap_cinsi_{i}"], data[f'Kap_Cinsi_{i}'], f"Kalem {i}: Kap Cinsi")
                        check_num(st.session_state[f"kap_adet_{i}"], data[f'Kap_Adedi_{i}'], f"Kalem {i}: Kap Adedi")
                        check_num(st.session_state[f"net_{i}"], data[f'Net_Ağırlık_KG_{i}'], f"Kalem {i}: Net Ağırlık")
                        check_num(st.session_state[f"gross_{i}"], data[f'Brüt_Ağırlık_KG_{i}'], f"Kalem {i}: Brüt Ağırlık")
                        check_num(st.session_state[f"fiyat_{i}"], data[f'Kalem_Fiyatı_{i}'], f"Kalem {i}: Kalem Fiyatı")
                        
                        # Taxes
                        check_num(st.session_state[f"fob_{i}"], data[f'İstatistiki_Kıymet_FOB_{i}'], f"Kalem {i}: İstatistik Kıymet", tol=0.5)
                        check_num(st.session_state[f"navlun_{i}"], data[f'Navlun_Tutari_{i}'], f"Kalem {i}: Navlun", tol=0.5)
                        check_num(st.session_state[f"sigorta_{i}"], data[f'Sigorta_Tutari_{i}'], f"Kalem {i}: Sigorta", tol=0.5)
                        check_num(st.session_state[f"cif_{i}"], data[f'CIF_Toplam_{i}'], f"Kalem {i}: Matrah (CIF)", tol=0.5)
                        check_num(st.session_state[f"gv_{i}"], data[f'GV_{i}'], f"Kalem {i}: Gümrük Vergisi", tol=0.5)
                        check_num(st.session_state[f"otv_{i}"], data[f'ÖTV_{i}'], f"Kalem {i}: ÖTV", tol=0.5)
                        check_num(st.session_state[f"kdv_{i}"], data[f'KDV_{i}'], f"Kalem {i}: KDV", tol=0.5)
                        check_num(st.session_state[f"v_toplam_{i}"], data[f'Vergiler_Toplami_{i}'], f"Kalem {i}: Vergiler Toplamı", tol=0.5)

                    if not errors:
                        st.balloons()
                        st.success("🎊 TESCİL BAŞARILI! Beyanname BİLGE sistemine başarıyla kaydedildi. (Başarı Oranı: %100)")
                        odev_log_name = data.get('Ödev_No', st.session_state.get('current_odev', '1'))
                        log_attempt(data['Öğrenci_Numarası'], data['Öğrenci_Ad_Soyad'], True, [], odev_log_name)
                    else:
                        st.error(f"Beyanname Tescil Edilemedi! Toplam {len(errors)} hata bulundu.")
                        with st.expander("Hata Detaylarını Gör"):
                            for err in errors:
                                st.write(f"❌ {err}")
                        odev_log_name = data.get('Ödev_No', st.session_state.get('current_odev', '1'))
                        log_attempt(data['Öğrenci_Numarası'], data['Öğrenci_Ad_Soyad'], False, errors, odev_log_name)

elif page == "Hoca Paneli":
    st.title("📽️ Öğretim Üyesi Yönetim Paneli")
    
    if not st.session_state.admin_mode:
        password = st.text_input("Yönetici Şifresi", type="password")
        if st.button("Giriş"):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_mode = True
                st.rerun()
            else:
                st.error("Hatalı şifre!")
    else:
        if st.sidebar.button("Çıkış Yap"):
            st.session_state.admin_mode = False
            st.rerun()
            
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
            
            log_df = pd.DataFrame(logs)
            
            # Filter by Assignment
            all_odevs = ["Hepsi"] + sorted(log_df['odev_no'].unique().tolist())
            selected_filter = st.selectbox("Ödev Filtresi", all_odevs)
            
            if selected_filter != "Hepsi":
                log_df = log_df[log_df['odev_no'] == selected_filter]

            st.subheader(f"Öğrenci Denemeleri ({selected_filter})")
            st.dataframe(log_df)
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Toplam Deneme", len(log_df))
            with col_b:
                success_count = log_df['success'].sum()
                st.metric("Başarılı Tescil", success_count)
            with col_c:
                success_rate = (success_count / len(log_df)) * 100 if len(log_df) > 0 else 0
                st.metric("Genel Başarı Oranı", f"%{success_rate:.1f}")

            st.subheader("Öğrenci Bazlı Rapor")
            st.dataframe(log_df, use_container_width=True)
            
            # Analytics
            st.subheader("En Çok Hata Yapılan Alanlar")
            all_errors = []
            for err_list in log_df['errors']:
                for e in err_list:
                    if "Kalem" in e:
                        parts = e.split(":")
                        if len(parts) > 1:
                            all_errors.append(parts[1].strip())
                        else:
                            all_errors.append(e)
                    else:
                        all_errors.append(e)
            
            if all_errors:
                err_counts = pd.Series(all_errors).value_counts().reset_index()
                err_counts.columns = ['Hata Türü', 'Sayı']
                
                fig = px.bar(err_counts, x='Hata Türü', y='Sayı', 
                            title="Sınıf Genelinde Hata Dağılımı",
                            color='Sayı', color_continuous_scale='Blues')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Henüz hata kaydı bulunamamaktadır.")
                
        else:
            st.info("Henüz hiç deneme yapılmadı.")
