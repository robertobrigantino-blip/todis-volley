# ==============================================================================
# SOFTWARE VERSION: v67.0
# RELEASE NOTE: Tab abbreviati (Mobile Ready) + Footer Landing + Global Sort
# ==============================================================================

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from io import StringIO
from urllib.parse import urljoin, quote
import re 
from datetime import datetime, timedelta
import os

# ================= CONFIGURAZIONE =================
NOME_VISUALIZZATO = "TODIS PASTENA VOLLEY"
APP_VERSION = "v67.0 (Short Tabs & Print)"

# MESSAGGIO PERSONALIZZATO FOOTER
FOOTER_MSG = "👨‍💻 Non sparate sul programmatore (né sul libero 🏐)"                                                                              
TARGET_TEAM_ALIASES = [
    "TODIS PASTENA VOLLEY",
    "TODIS CS PASTENA VOLLEY",
    "TODIS C.S. PASTENA VOLLEY"
]

FILE_LANDING = "index.html"      
FILE_MALE = "maschile.html"      
FILE_FEMALE = "femminile.html"   
FILE_GEN_MALE = "generale_m.html"
FILE_GEN_FEMALE = "generale_f.html"
FILE_SCORE = "segnapunti.html"   

# URL IMMAGINI
REPO_URL = "https://raw.githubusercontent.com/robertobrigantino-blip/todis-volley/main/"
URL_LOGO = REPO_URL + "logo.jpg"
URL_SPLIT_IMG = REPO_URL + "scelta_campionato.jpg"

# BOTTONI
BTN_ALL_RESULTS = REPO_URL + "all_result.png"
BTN_TODIS_RESULTS = REPO_URL + "todis_result.png"
BTN_SCOREBOARD = REPO_URL + "tabellone_segnapunti.png"
BTN_CALENDAR_EVENTS = REPO_URL + "prossimi_appuntamenti.png"

URL_COUNTER = "https://hits.sh/robertobrigantino-blip.github.io/todis-volley.svg?style=flat&label=VISITE&extraCount=0&color=d32f2f"

# CAMPIONATI
CAMPIONATI_MASCHILI = {
    "Serie D  Maschile Gir.C": "85622",
    "Under 19 Maschile Gir.A": "86865",
    "Under 17 Maschile Gir.B": "86864",
    "Under 15 Maschile Gir.B": "86848",
}

CAMPIONATI_FEMMINILI = {
    "Serie C  Femminile Gir.A": "85471",
    "Under 18 Femminile Gir.B": "86850",
    "Under 16 Femminile Gir.A": "86853",
    "Under 14 Femminile Gir.C": "86860",
}

ALL_CAMPIONATI = {**CAMPIONATI_MASCHILI, **CAMPIONATI_FEMMINILI}

def is_target_team(team_name):
    if pd.isna(team_name) or not str(team_name).strip(): return False
    name_clean = str(team_name).upper().strip()
    for alias in TARGET_TEAM_ALIASES:
        if alias.upper() in name_clean: return True
    return False

# ================= CSS COMUNE =================
CSS_BASE = """
<style>
    body { font-family: 'Roboto', sans-serif; background-color: #f0f2f5; margin: 0; padding: 0; color: #333; padding-bottom: 80px; }
    
    /* Header */
    .app-header { background-color: #d32f2f; color: white; padding: 5px 15px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 5px rgba(0,0,0,0.2); position: sticky; top:0; z-index:1000; height: 60px; }
    .header-left { display: flex; align-items: center; gap: 10px; cursor: pointer; }
    .app-header img.logo-main { height: 40px; width: 40px; border-radius: 50%; border: 2px solid white; object-fit: cover; }
    .app-header h1 { margin: 0; font-size: 14px; text-transform: uppercase; line-height: 1.1; font-weight: 700; }
    .last-update { font-size: 9px; opacity: 0.9; font-weight: normal; }
    
    .nav-buttons { display: flex; gap: 10px; align-items: center; }
    .nav-icon-img { height: 45px; width: auto; transition: transform 0.1s, opacity 0.2s; filter: drop-shadow(0 2px 3px rgba(0,0,0,0.3)); cursor: pointer; }
    .nav-icon-img:active { transform: scale(0.90); opacity: 0.8; }
    
    /* CALENDARIO NOTIFICA */
    .calendar-container { position: relative; display: inline-block; display: none; }
    .calendar-container.has-events { display: inline-block; animation: pulse-icon 2s infinite; }
    .calendar-container.has-events::after { content: ''; position: absolute; top: 2px; right: 2px; width: 10px; height: 10px; background: #ffeb3b; border-radius: 50%; border: 2px solid #d32f2f; }
    @keyframes pulse-icon { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }

    /* Tabs */
    .tab-bar { background-color: white; display: flex; overflow-x: auto; white-space: nowrap; position: sticky; top: 60px; z-index: 99; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-bottom: 1px solid #eee; }
    .tab-btn { flex: 1; padding: 12px 15px; text-align: center; background: none; border: none; font-size: 13px; font-weight: 500; color: #666; border-bottom: 3px solid transparent; cursor: pointer; min-width: 100px; }
    .tab-btn.active { color: #d32f2f; border-bottom: 3px solid #d32f2f; font-weight: bold; }
    .tab-content { display: none; padding: 15px; max-width: 800px; margin: 0 auto; animation: fadeIn 0.3s; }
    .tab-content.active { display: block; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    
    h2 { color: #d32f2f; font-size: 16px; border-left: 4px solid #d32f2f; padding-left: 8px; margin-top: 15px; margin-bottom: 12px; }

    /* Controls Bar (Sort/Print) */
    .calendar-controls { display: flex; gap: 10px; margin-bottom: 15px; justify-content: flex-end; align-items: center; }
    .btn-tool { 
        font-size: 11px; padding: 6px 12px; background: #f0f2f5; 
        border: 1px solid #ccc; border-radius: 20px; cursor: pointer; 
        color: #555; font-weight: bold; display: flex; align-items: center; gap: 5px; 
        transition: background 0.2s;
    }
    .btn-tool:hover { background: #e0e0e0; }
    .btn-tool.active { background: #d32f2f; color: white; border-color: #d32f2f; }

    /* Classifica */
    .table-card { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; width: 100%; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; white-space: nowrap; }
    th { background-color: #ffebee; color: #c62828; padding: 10px 6px; text-align: center; font-weight: bold; font-size: 11px; text-transform: uppercase; }
    td { padding: 10px 6px; text-align: center; border-bottom: 1px solid #f0f0f0; }
    td:nth-child(2) { text-align: left; min-width: 140px; font-weight: 500; position: sticky; left: 0; background-color: white; border-right: 1px solid #eee; }
    .my-team-row td { background-color: #fff3e0 !important; font-weight: bold; }

    /* Card Partita */
    .match-card { background: white; border-radius: 8px; padding: 12px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid #ddd; position: relative; overflow: hidden; transition: max-height 0.3s ease; }
    .match-card.win { border-left-color: #2e7d32; } 
    .match-card.loss { border-left-color: #c62828; } 
    .match-card.upcoming { border-left-color: #ff9800; } 

    .match-header { display: flex; align-items: center; gap: 8px; font-size: 11px; color: #666; margin-bottom: 8px; border-bottom: 1px solid #f5f5f5; padding-bottom: 5px; padding-right: 50px; }
    .date-badge { font-weight: bold; color: #d32f2f; display: flex; align-items: center; gap: 4px; }
    .teams { display: flex; flex-direction: column; gap: 6px; font-size: 14px; margin-bottom: 8px; }
    .team-row { display: flex; justify-content: space-between; align-items: center; }
    .my-team-text { color: #d32f2f; font-weight: 700; }
    .match-footer { margin-top: 8px; padding-top: 8px; border-top: 1px solid #f5f5f5; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; }
    .gym-name { font-size: 11px; color: #666; width: 100%; display: block; margin-bottom: 5px; }
    .action-buttons { display: flex; gap: 5px; width: 100%; justify-content: flex-end; }
    .btn { text-decoration: none; padding: 5px 10px; border-radius: 15px; font-size: 10px; font-weight: bold; display: flex; align-items: center; gap: 3px; border: 1px solid transparent; }
    .btn-map { background-color: #e3f2fd; color: #1565c0; border-color: #bbdefb; }
    .btn-cal { background-color: #f3e5f5; color: #7b1fa2; border-color: #e1bee7; } 
    .btn-wa { background-color: #e8f5e9; color: #2e7d32; border-color: #c8e6c9; } 

    /* LAYOUT SET E PUNTEGGIO */
    .scores-wrapper { display: flex; align-items: center; gap: 8px; justify-content: flex-end; width: 100%; }
    .set-total { width: 28px; height: 28px; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 16px; flex-shrink: 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .bg-green { background-color: #2e7d32; } 
    .bg-red { background-color: #c62828; }
    .bg-gray { background-color: #78909c; }
    .partials-inline { display: flex; gap: 3px; overflow-x: auto; max-width: 150px; }
    .partial-badge { width: 24px; height: 24px; background-color: #7986cb; color: white; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 11px; flex-shrink: 0; }
    .team-info { flex-grow: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

    /* Modals & Footer */
    .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 2000; display: none; align-items: center; justify-content: center; backdrop-filter: blur(2px); }
    .modal-content { background: white; width: 85%; max-width: 400px; max-height: 80vh; border-radius: 12px; padding: 20px; overflow-y: auto; position: relative; box-shadow: 0 10px 25px rgba(0,0,0,0.2); animation: slideUp 0.3s; }
    .modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px; }
    .modal-title { font-size: 18px; font-weight: bold; color: #d32f2f; }
    .close-btn { background: #eee; border: none; font-size: 24px; padding: 0 10px; border-radius: 5px; color: #555; cursor: pointer; }
    .footer-counter { text-align: center; margin-top: 30px; padding: 20px 0; border-top: 1px solid #eee; }
    .version-text { font-size: 10px; color: #999; margin-top: 5px; display: block; font-family: monospace; }
    .footer-msg { font-size: 11px; color: #777; margin-top: 4px; font-style: italic; opacity: 0.8; }
    
    /* IOS INSTALL TIP */
    .ios-install-popup { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: white; padding: 15px; border-radius: 10px; box-shadow: 0 5px 20px rgba(0,0,0,0.3); z-index: 3000; width: 85%; max-width: 350px; text-align: center; display: none; animation: popUp 0.5s; }
    .ios-install-popup:after { content: ''; position: absolute; bottom: -10px; left: 50%; transform: translateX(-50%); border-width: 10px 10px 0; border-style: solid; border-color: white transparent transparent; }
    @keyframes popUp { from{transform:translate(-50%, 20px); opacity:0;} to{transform:translate(-50%, 0); opacity:1;} }
    .landing-container { padding: 15px; max-width: 600px; margin: 0 auto; text-align: center; }
    .choice-card { position: relative; width: 100%; border-radius: 15px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.2); background: white; }
    .choice-img { width: 100%; display: block; height: auto; }
    .click-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; }
    .click-area { width: 50%; height: 100%; cursor: pointer; }
    .instruction-text { margin-bottom: 15px; font-weight: 500; color: #555; font-size: 14px; }
    
    @media print {
        .app-header, .tab-bar, .nav-buttons, .calendar-controls, .footer-counter, .modal-overlay, .btn, .action-buttons, .ios-install-popup { display: none !important; }
        body { background: white; color: black; padding: 0; margin: 0; }
        .match-card { border: 1px solid #ccc; break-inside: avoid; box-shadow: none; margin-bottom: 10px; }
        .tab-content { display: block !important; }
        h2 { color: black; border-left: none; border-bottom: 2px solid #000; padding: 0; margin-top: 20px; }
    }
</style>
<script>
    function openTab(tabIndex) {
        var contents = document.getElementsByClassName("tab-content");
        for (var i = 0; i < contents.length; i++) contents[i].classList.remove("active");
        var buttons = document.getElementsByClassName("tab-btn");
        for (var i = 0; i < buttons.length; i++) buttons[i].classList.remove("active");
        document.getElementById("content-" + tabIndex).classList.add("active");
        document.getElementById("btn-" + tabIndex).classList.add("active");
    }
    
    function closeModal() { document.getElementById('modal-overlay').style.display = 'none'; }
    function closeIosPopup() { document.getElementById('ios-popup').style.display = 'none'; }
    function openModal() { document.getElementById('modal-overlay').style.display = 'flex'; }
    
    function tornaAlSettore() {
        const urlParams = new URLSearchParams(window.location.search);
        const origin = urlParams.get('from');
        if (origin === 'maschile') window.location.href = "maschile.html";
        else if (origin === 'femminile') window.location.href = "femminile.html";
        else window.location.href = "index.html";
    }

    var originalOrder = {};
    function toggleSort(tabId) {
        const container = document.getElementById('calendar-container-' + tabId);
        const btn = document.getElementById('btn-sort-' + tabId);
        const isSorted = btn.getAttribute('data-sorted') === 'true';
        if (!originalOrder[tabId]) originalOrder[tabId] = container.innerHTML;
        
        if (!isSorted) {
            const cards = Array.from(container.querySelectorAll('.match-card'));
            container.querySelectorAll('h3').forEach(h => h.style.display = 'none');
            cards.sort((a, b) => (a.getAttribute('data-date-iso') || '9999').localeCompare(b.getAttribute('data-date-iso') || '9999'));
            container.innerHTML = "";
            cards.forEach(card => container.appendChild(card));
            btn.innerHTML = "🔢 Ordina per Giornata";
            btn.setAttribute('data-sorted', 'true');
            btn.classList.add('active');
        } else {
            container.innerHTML = originalOrder[tabId];
            btn.innerHTML = "📅 Ordina per Data";
            btn.setAttribute('data-sorted', 'false');
            btn.classList.remove('active');
        }
    }
    function printCalendar() { window.print(); }

    window.onload = function() {
        const isIos = /iphone|ipad|ipod/.test( window.navigator.userAgent.toLowerCase() );
        const isInStandaloneMode = ('standalone' in window.navigator) && (window.navigator.standalone);
        if (isIos && !isInStandaloneMode && document.getElementById('ios-popup')) {
            setTimeout(() => { document.getElementById('ios-popup').style.display = 'block'; }, 2000);
        }
    };
</script>
"""

SCOREBOARD_CODE = """
<style>
    body { background-color: #121212; color: white; overflow: hidden; margin: 0; padding: 0; }
    .rotate-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #111; z-index: 9999; flex-direction: column; justify-content: center; align-items: center; text-align: center; color: white; }
    @media (orientation: portrait) { .rotate-overlay { display: flex; } .sb-container { display: none; } }
    .sb-container { display: grid; grid-template-columns: 1fr 180px 1fr; height: 100vh; width: 100vw; }
    .team-panel { display: flex; flex-direction: column; justify-content: center; align-items: center; position: relative; cursor: pointer; }
    .team-home { background-color: #1e3a8a; border-right: 2px solid #333; }
    .team-guest { background-color: #b91c1c; border-left: 2px solid #333; }
    .team-name-input { background: transparent; border: none; color: white; font-size: 24px; font-weight: bold; text-align: center; width: 80%; }
    .score-display { font-size: 180px; font-weight: 800; line-height: 1; user-select: none; }
    .center-panel { background-color: #222; display: flex; flex-direction: column; justify-content: space-between; align-items: center; padding: 10px 5px; }
    .sets-score { font-size: 35px; font-weight: bold; }
    .btn-ctrl { padding: 8px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; width: 90%; color: white; font-size: 12px; text-decoration: none; text-align: center; }
</style>
<div class="rotate-overlay"><h2>Ruota il dispositivo</h2></div>
<div class="sb-container">
    <div class="team-panel team-home" onclick="addPoint('Home')">
        <input type="text" class="team-name-input" value="CASA">
        <div class="score-display" id="scoreHome">0</div>
    </div>
    <div class="center-panel">
        <div class="sets-box"><div style="font-size:10px; color:#888;">SETS</div><div class="sets-score"><span id="setsHome">0</span> - <span id="setsGuest">0</span></div></div>
        <div class="controls-bottom">
            <button class="btn-ctrl" style="background:#546e7a;" onclick="resetMatch()">Reset</button>
            <a href="index.html" class="btn-ctrl" style="background:#333; margin-top:5px; display:block;">Esci</a>
        </div>
    </div>
    <div class="team-panel team-guest" onclick="addPoint('Guest')">
        <input type="text" class="team-name-input" value="OSPITI">
        <div class="score-display" id="scoreGuest">0</div>
    </div>
</div>
<script>
    let scoreH = 0, scoreG = 0, setsH = 0, setsG = 0;
    function addPoint(t) { if(t==='Home') scoreH++; else scoreG++; updateUI(); }
    function resetMatch() { if(confirm("Azzera?")) { scoreH=0; scoreG=0; setsH=0; setsG=0; updateUI(); } }
    function updateUI() { 
        document.getElementById('scoreHome').innerText = scoreH; document.getElementById('scoreGuest').innerText = scoreG;
        document.getElementById('setsHome').innerText = setsH; document.getElementById('setsGuest').innerText = setsG;
    }
</script>
"""

# ================= FUNZIONI DI SUPPORTO =================
def create_google_calendar_link(row):
    if not row['DataISO']: return ""
    title = quote(f"🏐 {row['Squadra Casa']} vs {row['Squadra Ospite']}")
    location = quote(row['Impianto']) if row['Impianto'] else ""
    date_clean = row['DataISO'].replace('-', '')
    dates = f"{date_clean}T120000/{date_clean}T140000"
    return f"https://www.google.com/calendar/render?action=TEMPLATE&text={title}&dates={dates}&location={location}"

def create_whatsapp_link(row):
    if row['Punteggio']: text = f"🏐 *Risultato*\n{row['Squadra Casa']} {row['Set Casa']} - {row['Set Ospite']} {row['Squadra Ospite']}"
    else: text = f"📅 *Gara*\n{row['Data']}\n{row['Squadra Casa']} vs {row['Squadra Ospite']}"
    return f"https://wa.me/?text={quote(text)}"

def crea_card_html(r, camp, is_focus_mode=False):
    is_home, is_away = is_target_team(r['Squadra Casa']), is_target_team(r['Squadra Ospite'])
    is_my_match = is_home or is_away
    cs = 'class="team-info my-team-text"' if is_home else 'class="team-info"'
    os = 'class="team-info my-team-text"' if is_away else 'class="team-info"'
    status_class = "upcoming"
    sc_val, so_val = r['Set Casa'] or "-", r['Set Ospite'] or "-"
    if r['Punteggio']:
        try:
            sc, so = int(r['Set Casa']), int(r['Set Ospite'])
            status_class = "win" if ((is_home and sc>so) or (is_away and so>sc)) else "loss"
            if not is_my_match: status_class = "played"
            bg_c = "bg-green" if sc > so else "bg-red"
            bg_o = "bg-green" if so > sc else "bg-red"
            if not is_my_match: bg_c = bg_o = "bg-gray"
            sc_val = f'<div class="set-total {bg_c}">{sc}</div>'
            so_val = f'<div class="set-total {bg_o}">{so}</div>'
        except: status_class = "played"
    
    btns = f'<a href="{r["Maps"]}" target="_blank" class="btn btn-map">📍</a>'
    if is_my_match or not is_focus_mode:
        if not r['Punteggio']: btns += f'<a href="{create_google_calendar_link(r)}" target="_blank" class="btn btn-cal">📅</a>'
        btns += f'<a href="{create_whatsapp_link(r)}" target="_blank" class="btn btn-wa">💬</a>'

    return f"""<div class="match-card {status_class}" data-date-iso="{r['DataISO']}">
        <div class="match-header"><span class="date-badge">📅 {r['Data']}</span> | {r['Giornata']}</div>
        <div class="teams">
            <div class="team-row"><span {cs}>{r['Squadra Casa']}</span>{sc_val}</div>
            <div class="team-row"><span {os}>{r['Squadra Ospite']}</span>{so_val}</div>
        </div>
        <div class="match-footer"><span class="gym-name">🏟️ {r['Impianto']}</span><div class="action-buttons">{btns}</div></div>
    </div>"""

def get_match_details_robust(driver, url):
    d_ora, d_iso, lug, mps, prz = "Data N.D.", "", "N.D.", "", ""
    try:
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        txt = soup.get_text()
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', txt)
        if date_match:
            d_ora = date_match.group(1)
            d_iso = datetime.strptime(d_ora, "%d/%m/%Y").strftime("%Y-%m-%d")
        imp = soup.find('div', class_='divImpianto')
        if imp: lug = imp.get_text(strip=True)
        mps = f"https://www.google.com/maps/search/?api=1&query={quote(lug)}"
    except: pass
    return d_ora, d_iso, lug, mps, prz

def scrape_data():
    opt = Options()
    opt.add_argument("--headless")
    driver = webdriver.Chrome(options=opt)
    res, std = [], []
    for nome, id_c in ALL_CAMPIONATI.items():
        base = "https://www.fipavsalerno.it/mobile/"
        if "Serie" in nome: base = "https://www.fipavcampania.it/mobile/"
        driver.get(f"{base}risultati.asp?CampionatoId={id_c}")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        container = soup.find('div', style=lambda x: x and 'margin-top:7.5em' in x)
        g_att = "N.D."
        if container:
            for el in container.children:
                if el.name == 'div' and 'divGiornata' in el.get('class', []): g_att = el.get_text(strip=True)
                elif el.name == 'a' and 'gara' in el.get('class', []):
                    pt_c = el.find('div', class_='setCasa').get_text(strip=True) if el.find('div', class_='setCasa') else ""
                    pt_o = el.find('div', class_='setOspite').get_text(strip=True) if el.find('div', class_='setOspite') else ""
                    c = el.find('div', class_='squadraCasa').get_text(strip=True).replace(pt_c, "").strip()
                    o = el.find('div', class_='squadraOspite').get_text(strip=True).replace(pt_o, "").strip()
                    d_ora, d_iso, lug, mps, prz = get_match_details_robust(driver, urljoin(base, el.get('href', '')))
                    res.append({'Campionato': nome, 'Giornata': g_att, 'Squadra Casa': c, 'Squadra Ospite': o, 'Punteggio': pt_c!="", 'Data': d_ora, 'DataISO': d_iso, 'Impianto': lug, 'Maps': mps, 'Set Casa': pt_c, 'Set Ospite': pt_o, 'Parziali': prz})
        try:
            driver.get(f"{base}risultati.asp?CampionatoId={id_c}&vis=classifica")
            df = pd.read_html(StringIO(driver.page_source))[0]
            df['Campionato'] = nome
            std.append(df)
        except: pass
    driver.quit()
    return pd.DataFrame(res), pd.concat(std) if std else pd.DataFrame()

# ================= GENERATORI HTML =================
def genera_landing_page():
    html = f'<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{NOME_VISUALIZZATO}</title>{CSS_BASE}</head><body><div class="app-header"><div class="header-left"><img src="{URL_LOGO}" class="logo-main"><h1>{NOME_VISUALIZZATO}</h1></div><div class="nav-buttons"><a href="{FILE_SCORE}"><img src="{BTN_SCOREBOARD}" class="nav-icon-img"></a></div></div><div class="landing-container"><div class="instruction-text">Seleziona il settore:</div><div class="choice-card"><img src="{URL_SPLIT_IMG}" class="choice-img"><div class="click-overlay" style="display:flex; position:absolute; top:0; width:100%; height:100%;"><a href="{FILE_MALE}" style="width:50%;"></a><a href="{FILE_FEMALE}" style="width:50%;"></a></div></div></div><div class="footer-counter"><img src="{URL_COUNTER}"><br><span class="version-text">{APP_VERSION}</span><div class="footer-msg">{FOOTER_MSG}</div></div><div id="ios-popup" class="ios-install-popup"><div style="font-weight:bold; margin-bottom:10px;">Installa l\'App</div><button onclick="closeIosPopup()">Chiudi</button></div></body></html>'
    with open(FILE_LANDING, "w", encoding="utf-8") as f: f.write(html)

def genera_pagina_app(df_ris, df_class, filename, campionati_target):
    page_title = "Settore Maschile" if "maschile" in filename else "Settore Femminile"
    origin = "maschile" if "maschile" in filename else "femminile"
    nav = f'<a href="{"generale_m.html" if origin=="maschile" else "generale_f.html"}?from={origin}"><img src="{BTN_ALL_RESULTS}" class="nav-icon-img"></a><a href="{FILE_SCORE}"><img src="{BTN_SCOREBOARD}" class="nav-icon-img"></a>'
    
    html = f'<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{page_title}</title>{CSS_BASE}</head><body>'
    html += f'<div class="app-header"><div class="header-left" onclick="window.location.href=\'index.html\'"><img src="{URL_LOGO}" class="logo-main"><h1>{page_title}</h1></div><div class="nav-buttons">{nav}</div></div>'
    
    camps = [c for c in campionati_target.keys() if c in df_class['Campionato'].unique()]
    html += '<div class="tab-bar">'
    for i, c in enumerate(camps):
        short = c.replace("Maschile", "").replace("Femminile", "").replace("  ", " ").strip()
        html += f'<button id="btn-{i}" class="tab-btn {"active" if i==0 else ""}" onclick="openTab({i})">{short}</button>'
    html += '</div>'

    for i, c in enumerate(camps):
        html += f'<div id="content-{i}" class="tab-content {"active" if i==0 else ""}">'
        html += f'<h2>🏆 Classifica</h2><div class="table-card"><table>'
        df_c = df_class[df_class['Campionato'] == c].sort_values(by=df_class.columns[0])
        for _, r in df_c.iterrows():
            cls = 'style="background:#fff3e0; font-weight:bold;"' if is_target_team(r.iloc[1]) else ''
            html += f'<tr {cls}><td>{r.iloc[0]}</td><td>{r.iloc[1]}</td><td>{r.iloc[2]}</td></tr>'
        html += '</table></div>'
        
        html += f'<h2>📅 Calendario TODIS</h2><div class="calendar-controls"><button class="btn-tool" id="btn-sort-{i}" data-sorted="false" onclick="toggleSort({i})">📅 Ordina Data</button><button class="btn-tool" onclick="printCalendar()">🖨️ Stampa</button></div>'
        html += f'<div id="calendar-container-{i}">'
        df_t = df_ris[(df_ris['Campionato'] == c) & (df_ris['Squadra Casa'].apply(is_target_team) | df_ris['Squadra Ospite'].apply(is_target_team))]
        for _, r in df_t.iterrows(): html += crea_card_html(r, c, True)
        html += '</div></div>'
    
    html += f'<div class="footer-counter"><img src="{URL_COUNTER}"><br><span class="version-text">{APP_VERSION}</span></div></body></html>'
    with open(filename, "w", encoding="utf-8") as f: f.write(html)

def genera_pagina_generale(df_ris, df_class, filename, campionati_target):
    html = f'<!DOCTYPE html><html><head>{CSS_BASE}</head><body>'
    html += f'<div class="app-header" style="background:#1976D2"><div class="header-left" onclick="tornaAlSettore()"><img src="{URL_LOGO}" class="logo-main"><h1>Tutti i Risultati</h1></div></div>'
    
    camps = [c for c in campionati_target.keys() if c in df_class['Campionato'].unique()]
    html += '<div class="tab-bar">'
    for i, c in enumerate(camps):
        short = c.replace("Maschile", "").replace("Femminile", "").replace("  ", " ").strip()
        html += f'<button id="btn-{i}" class="tab-btn {"active" if i==0 else ""}" onclick="openTab({i})">{short}</button>'
    html += '</div>'

    for i, c in enumerate(camps):
        html += f'<div id="content-{i}" class="tab-content {"active" if i==0 else ""}">'
        html += f'<div class="calendar-controls"><button class="btn-tool" id="btn-sort-{i}" data-sorted="false" onclick="toggleSort({i})">📅 Ordina Data</button><button class="btn-tool" onclick="printCalendar()">🖨️ Stampa</button></div>'
        html += f'<div id="calendar-container-{i}">'
        df_c = df_ris[df_ris['Campionato'] == c]
        for g in df_c['Giornata'].unique():
            html += f'<h3 style="background:#eee; padding:5px; border-radius:4px;">{g}</h3>'
            for _, r in df_c[df_c['Giornata'] == g].iterrows(): html += crea_card_html(r, c, False)
        html += '</div></div>'
    
    html += '</body></html>'
    with open(filename, "w", encoding="utf-8") as f: f.write(html)

def genera_segnapunti():
    with open(FILE_SCORE, "w", encoding="utf-8") as f: f.write(f'<!DOCTYPE html><html><head>{SCOREBOARD_CODE}</head></html>')

if __name__ == "__main__":
    df_ris, df_class = scrape_data()
    genera_landing_page()
    genera_pagina_app(df_ris, df_class, FILE_MALE, CAMPIONATI_MASCHILI)
    genera_pagina_app(df_ris, df_class, FILE_FEMALE, CAMPIONATI_FEMMINILI)
    genera_pagina_generale(df_ris, df_class, FILE_GEN_MALE, CAMPIONATI_MASCHILI)
    genera_pagina_generale(df_ris, df_class, FILE_GEN_FEMALE, CAMPIONATI_FEMMINILI)
    genera_segnapunti()
