# ==============================================================================
# SOFTWARE VERSION: v5.1
# RELEASE NOTE: Fix KeyError 'Campionato' & defined SCOREBOARD_CODE + Bracket
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

# ================= 1. CONFIGURAZIONE E SCOREBOARD =================

NOME_VISUALIZZATO = "TODIS PASTENA VOLLEY"
APP_VERSION = "v5.1 | Golden Release 🏆"

FOOTER_MSG = "🐾 <span style='color: #d32f2f; font-weight: 900; font-size: 13px; letter-spacing: 1px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);'>LINCI GO!</span> 🏐"    

TARGET_TEAM_ALIASES = ["TODIS PASTENA VOLLEY", "TODIS CS PASTENA VOLLEY", "TODIS C.S. PASTENA VOLLEY", "CS PASTENA"]

FILE_LANDING, FILE_MALE, FILE_FEMALE = "index.html", "maschile.html", "femminile.html"
FILE_GEN_MALE, FILE_GEN_FEMALE, FILE_SCORE = "generale_m.html", "generale_f.html", "segnapunti.html"

REPO_URL = "https://raw.githubusercontent.com/robertobrigantino-blip/todis-volley/main/"
URL_LOGO = REPO_URL + "logo.jpg"
URL_SPLIT_IMG = REPO_URL + "scelta_campionato.jpg"
BTN_ALL_RESULTS = REPO_URL + "all_result.png"
BTN_TODIS_RESULTS = REPO_URL + "todis_result.png"
BTN_SCOREBOARD = REPO_URL + "tabellone_segnapunti.png"
BTN_CALENDAR_EVENTS = REPO_URL + "prossimi_appuntamenti.png"
URL_COUNTER = "https://hits.sh/robertobrigantino-blip.github.io/todis-volley.svg?style=flat&label=VISITE&extraCount=0&color=d32f2f"

# --- CAMPIONATI ---
CAMPIONATI_MASCHILI = {"Serie D  Gir.C S.Maschile": "85622", "Under 19 Gir.A S.Maschile": "86865", "Under 17 Gir.B S.Maschile": "86864", "Under 15 Gir.B S.Maschile": "86848"}
CAMPIONATI_FEMMINILI = {"Serie C  Gir.A S.Femminile": "85471", "Under 18 Gir.B S.Femminile": "86850", "Under 16 Gir.A S.Femminile": "86853", "Under 14 Gir.C S.Femminile": "86860", "Under 13 Gir.B S.Femminile": "88820"}

# --- OVERRIDE FINALI ---
CAMPIONATI_FINALI = {"Under 18 Gir.B S.Femminile": "89371", "Under 19 Gir.A S.Maschile": "89301"}

# --- CLASSIFICHE AVULSE ---
CAMPIONATI_AVULSI = {"Serie C  Gir.A S.Femminile": "85473", "Under 14 Gir.C S.Femminile": "86858", "Under 16 Gir.A S.Femminile": "86853", "Under 18 Gir.B S.Femminile": "86849", "Serie D  Gir.C S.Maschile": "85620", "Under 19 Gir.A S.Maschile": "86865"}

ALL_CAMPIONATI = {**CAMPIONATI_MASCHILI, **CAMPIONATI_FEMMINILI}

SCOREBOARD_CODE = """
<style>
    body { background-color: #121212; color: white; overflow: hidden; margin: 0; padding: 0; }
    .rotate-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #111; z-index: 9999; flex-direction: column; justify-content: center; align-items: center; text-align: center; color: white; }
    @media (orientation: portrait) { .rotate-overlay { display: flex; } .sb-container { display: none; } }
    .sb-container { display: grid; grid-template-columns: 1fr 180px 1fr; height: 100vh; width: 100vw; }
    .team-panel { display: flex; flex-direction: column; justify-content: center; align-items: center; position: relative; cursor: pointer; transition: background 0.2s; }
    .team-home { background-color: #1e3a8a; border-right: 2px solid #333; }
    .team-guest { background-color: #b91c1c; border-left: 2px solid #333; }
    .team-name-input { background: transparent; border: none; color: rgba(255,255,255,0.8); font-size: 24px; font-weight: bold; text-align: center; width: 80%; margin-bottom: 10px; text-transform: uppercase; }
    .score-display { font-size: 180px; font-weight: 800; line-height: 1; user-select: none; }
    .center-panel { background-color: #222; display: flex; flex-direction: column; justify-content: space-between; align-items: center; padding: 10px 5px; }
    .current-set-badge { background: #d32f2f; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-top: 5px; }
    .btn-ctrl { padding: 8px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; width: 100%; color: white; font-size: 12px; text-decoration: none; text-align: center; display: block; box-sizing: border-box; }
</style>
<div class="rotate-overlay"><h2>Ruota il dispositivo 🔄</h2></div>
<div class="sb-container">
    <div class="team-panel team-home" onclick="addPoint('Home')">
        <input type="text" class="team-name-input" value="CASA">
        <div class="score-display" id="scoreHome">0</div>
    </div>
    <div class="center-panel">
        <div id="setNum" class="current-set-badge">SET 1</div>
        <div style="font-size:30px;"><span id="setsHome">0</span> - <span id="setsGuest">0</span></div>
        <button class="btn-ctrl" style="background:#546e7a;" onclick="location.reload()">Reset</button>
        <a href="index.html" class="btn-ctrl" style="background:#333;">Esci</a>
    </div>
    <div class="team-panel team-guest" onclick="addPoint('Guest')">
        <input type="text" class="team-name-input" value="OSPITI">
        <div class="score-display" id="scoreGuest">0</div>
    </div>
</div>
<script>
    let sH=0, sG=0, setH=0, setG=0, cur=1;
    function addPoint(t){ if(t=='Home')sH++; else sG++; update(); check(); }
    function update(){ document.getElementById('scoreHome').innerText=sH; document.getElementById('scoreGuest').innerText=sG; document.getElementById('setsHome').innerText=setH; document.getElementById('setsGuest').innerText=setG; }
    function check(){ let lim=(cur==5)?15:25; if((sH>=lim||sG>=lim)&&Math.abs(sH-sG)>=2){ if(sH>sG)setH++; else setG++; sH=0; sG=0; cur++; update(); document.getElementById('setNum').innerText="SET "+cur; } }
</script>
"""

BRACKET_HTML = """
<div class="bracket-container">
    <table class="bracket-table">
        <thead><tr><th>CAMPO 1</th><th>CAMPO 2</th><th>CAMPO 3</th><th>CAMPO 4</th></tr></thead>
        <tbody>
            <tr>
                <td class="highlight-match">QF1: 1° Avulsa<br>vs 8° Avulsa</td>
                <td class="highlight-match">QF2: 2° Avulsa<br>vs 7° Avulsa</td>
                <td class="highlight-match">QF3: 3° Avulsa<br>vs 6° Avulsa</td>
                <td class="highlight-match">QF4: 4° Avulsa<br>vs 5° Avulsa</td>
            </tr>
            <tr><td colspan="4" style="height:20px; border:none;"></td></tr>
            <tr>
                <td class="highlight-match">SF1: Vinc. QF1<br>vs Vinc. QF4</td>
                <td class="highlight-match">SF2: Vinc. QF2<br>vs Vinc. QF3</td>
                <td></td><td></td>
            </tr>
            <tr><td colspan="4" style="height:20px; border:none;"></td></tr>
            <tr>
                <td class="highlight-match" style="background:#ffeb3b">FINALE 1°-2°<br>Vinc. SF1 vs Vinc. SF2</td>
                <td></td><td></td><td></td>
            </tr>
        </tbody>
    </table>
</div>
"""

# ================= 2. FUNZIONI HELPER =================

def is_target_team(team_name):
    if pd.isna(team_name) or not str(team_name).strip(): return False
    name_clean = str(team_name).upper().strip()
    for alias in TARGET_TEAM_ALIASES:
        if alias.upper() in name_clean: return True
    return False

def create_google_calendar_link(row):
    if not row.get('DataISO'): return ""
    title = quote(f"🏐 {row['Squadra Casa']} vs {row['Squadra Ospite']}")
    location = quote(row['Impianto']) if row['Impianto'] else ""
    date_clean = row['DataISO'].replace('-', '')
    dates = f"{date_clean}/{date_clean}"
    return f"https://www.google.com/calendar/render?action=TEMPLATE&text={title}&dates={dates}&location={location}"

def create_whatsapp_link(row):
    text = f"🏐 *{row['Campionato']}*\n{row['Squadra Casa']} vs {row['Squadra Ospite']}"
    if row.get('Punteggio'): text += f"\nRisultato: {row['Punteggio']}"
    return f"https://wa.me/?text={quote(text)}"

def crea_card_html(r, camp, is_focus_mode=False):
    is_home = is_target_team(r['Squadra Casa'])
    is_away = is_target_team(r['Squadra Ospite'])
    is_my_match = is_home or is_away
    cs = 'class="team-info my-team-text"' if is_home else 'class="team-info"'
    os = 'class="team-info my-team-text"' if is_away else 'class="team-info"'
    status_class = "upcoming"
    sc_val, so_val = r['Set Casa'] or "-", r['Set Ospite'] or "-"

    if r['Punteggio']:
        try:
            sc, so = int(r['Set Casa']), int(r['Set Ospite'])
            bg_c = "bg-green" if sc > so else "bg-red"
            bg_o = "bg-green" if so > sc else "bg-red"
            if is_my_match: status_class = "win" if ((is_home and sc > so) or (is_away and so > sc)) else "loss"
            else: status_class = "played"; bg_c, bg_o = "bg-gray", "bg-gray"
            if r['Parziali']:
                matches = re.findall(r'(\d+)\s*-\s*(\d+)', str(r['Parziali']))
                if matches:
                    partials_c = "".join([f'<div class="partial-badge">{p[0]}</div>' for p in matches])
                    partials_o = "".join([f'<div class="partial-badge">{p[1]}</div>' for p in matches])
                    sc_val = f'<div class="scores-wrapper"><div class="partials-inline">{partials_c}</div><div class="set-total {bg_c}">{sc}</div></div>'
                    so_val = f'<div class="scores-wrapper"><div class="partials-inline">{partials_o}</div><div class="set-total {bg_o}">{so}</div></div>'
        except: pass
    
    btns = f'<a href="{r["Maps"]}" target="_blank" class="btn btn-map">📍 Mappa</a>' if r['Maps'] else ""
    if is_my_match or not is_focus_mode:
        if not r['Punteggio']: btns += f'<a href="{create_google_calendar_link(r)}" target="_blank" class="btn btn-cal">📅</a>'
        btns += f'<a href="{create_whatsapp_link(r)}" target="_blank" class="btn btn-wa">💬</a>'

    return f'<div class="match-card {status_class}" data-date-iso="{r["DataISO"]}" data-camp="{camp}" data-my-team="{str(is_my_match).lower()}"><div class="match-header">📅 {r["Data"]} | {r["Giornata"]}</div><div class="teams"><div class="team-row"><span {cs}>{r["Squadra Casa"]}</span>{sc_val}</div><div class="team-row"><span {os}>{r["Squadra Ospite"]}</span>{so_val}</div></div><div class="match-footer"><span class="gym-name">🏟️ {r["Impianto"]}</span><div class="action-buttons">{btns}</div></div></div>'

# ================= 3. CSS BASE =================

CSS_BASE = """
<style>
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    html, body { height: 100%; margin: 0; padding: 0; font-family: 'Roboto', sans-serif; background-color: #f0f2f5; color: #333; overflow-x: hidden; }
    body { display: flex; flex-direction: column; }
    .app-header { background-color: #d32f2f; color: white; padding: 0 15px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 5px rgba(0,0,0,0.2); height: 60px; flex-shrink: 0; z-index: 1000; position: sticky; top: 0; }
    .header-left { display: flex; align-items: center; gap: 10px; }
    .app-header img.logo-main { height: 40px; width: 40px; border-radius: 50%; border: 2px solid white; object-fit: cover; }
    .app-header h1 { margin: 0; font-size: 13px; text-transform: uppercase; font-weight: 700; }   
    .nav-buttons { display: flex; gap: 8px; align-items: center; }
    .nav-icon-img { height: 42px; width: auto; filter: drop-shadow(0 2px 3px rgba(0,0,0,0.3)); }
    .calendar-container { position: relative; display: none; }
    .calendar-container.has-events { display: inline-block; animation: pulse 2s infinite; }
    .calendar-container.has-events::after { content: ''; position: absolute; top: 2px; right: 2px; width: 10px; height: 10px; background: #ffeb3b; border-radius: 50%; border: 2px solid #d32f2f; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.08); } 100% { transform: scale(1); } }
    .landing-container { flex: 1; display: flex; flex-direction: column; justify-content: space-around; align-items: center; padding: 5px 0; }
    .choice-card { position: relative; width: 92%; max-width: 450px; border-radius: 15px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
    .choice-img { width: 100%; height: auto; max-height: 58vh; object-fit: contain; display: block; }
    .click-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; }
    .click-area { width: 50%; height: 100%; cursor: pointer; }
    .tab-bar { background-color: white; display: flex; overflow-x: auto; white-space: nowrap; position: sticky; top: 60px; z-index: 99; border-bottom: 1px solid #eee; flex-shrink: 0; }
    .tab-btn { flex: 1; padding: 10px 8px; font-size: 11px; font-weight: 600; color: #666; border: none; background: none; border-bottom: 3px solid transparent; min-width: 85px; text-transform: uppercase; }
    .tab-btn.active { color: #d32f2f; border-bottom-color: #d32f2f; font-weight: bold; }
    .tab-content { display: none; padding: 15px; width: 100%; max-width: 800px; margin: 0 auto; }
    .tab-content.active { display: block; }
    h2 { color: #d32f2f; font-size: 16px; border-left: 4px solid #d32f2f; padding-left: 8px; margin: 15px 0; }
    .table-card { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; width: 100%; }
    .table-scroll { overflow-x: auto; width: 100%; }
    table { width: 100%; border-collapse: collapse; font-size: 11px; table-layout: fixed; }
    th, td { padding: 8px 4px; text-align: center; border-bottom: 1px solid #f0f0f0; }
    th { background-color: #ffebee; color: #c62828; font-weight: bold; }
    td:nth-child(2) { text-align: left; width: 120px; position: sticky; left: 0; background: white; white-space: normal; line-height: 1.2; z-index: 2; }
    .my-team-row td { background-color: #fff3e0 !important; font-weight: bold; }
    .match-card { background: white; border-radius: 8px; padding: 12px; margin-bottom: 15px; border-left: 4px solid #ddd; position: relative; }
    .match-card.win { border-left-color: #2e7d32; } .match-card.loss { border-left-color: #c62828; }
    .team-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .scores-wrapper { display: flex; align-items: center; gap: 6px; }
    .partials-inline { display: flex; gap: 2px; }
    .partial-badge { width: 22px; height: 22px; background: #7986cb; color: white; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 9px; }
    .set-total { width: 26px; height: 26px; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; }
    .bg-green { background: #2e7d32; } .bg-red { background: #c62828; } .bg-gray { background: #78909c; }
    .btn { text-decoration: none; padding: 4px 8px; border-radius: 12px; font-size: 9px; font-weight: bold; display: inline-flex; align-items: center; gap: 3px; border: 1px solid transparent; margin-left: 4px; }
    .btn-map { background: #e3f2fd; color: #1565c0; } .btn-cal { background: #f3e5f5; color: #7b1fa2; } .btn-wa { background: #e8f5e9; color: #2e7d32; }
    .bracket-container { width: 100%; overflow-x: auto; margin-bottom: 20px; background: white; padding: 10px; border-radius: 8px; }
    .bracket-table { width: 100%; border-collapse: collapse; min-width: 500px; font-size: 10px; }
    .bracket-table td { border: 1px solid #ddd; padding: 5px; text-align: center; background: #fafafa; }
    .highlight-match { background: #ffff00 !important; font-weight: bold; border: 2px solid #000 !important; }
    .install-popup { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: white; padding: 20px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); z-index: 5000; width: 85%; text-align: center; display: none; border: 2px solid #d32f2f; }
    .footer-counter { text-align: center; padding: 15px 0; background: white; border-top: 1px solid #eee; }
</style>
<script>
    function openTab(i){ document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active')); document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active')); document.getElementById('content-'+i).classList.add('active'); document.getElementById('btn-'+i).classList.add('active'); }
    function closePopup(id){ document.getElementById(id).style.display='none'; }
    function openModal(){ document.getElementById('modal-overlay').style.display='flex'; }
    function closeModal(){ document.getElementById('modal-overlay').style.display='none'; }
    function printCalendar(){ window.print(); }
    window.onload = function(){
        if(navigator.standalone || window.matchMedia('(display-mode: standalone)').matches) return;
        const isIos = /iphone|ipad|ipod/.test(navigator.userAgent.toLowerCase());
        const p = isIos ? document.getElementById('ios-popup') : document.getElementById('android-popup');
        if(p) setTimeout(()=>p.style.display='block', 3000);
    };
</script>
"""

# ================= 4. SCRAPING =================

def get_match_details_robust(driver, url):
    d, iso, l, m, p = "N/D", "", "N/D", "", ""
    try:
        driver.get(url); WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "divImpianto")))
        soup = BeautifulSoup(driver.page_source, 'html.parser'); text = soup.get_text(separator=" ")
        match = re.search(r'(\d{2}/\d{2}/\d{4}).*?(\d{2}[:\.]\d{2})', text)
        if match: d = f"{match.group(1)} ⏰ {match.group(2)}"; iso = datetime.strptime(match.group(1), "%d/%m/%Y").strftime("%Y-%m-%d")
        imp = soup.find('div', class_='divImpianto')
        if imp: l = imp.get_text(strip=True); m = f"https://www.google.com/maps/search/?api=1&query={quote(l)}"
        dc = soup.find('div', id='risultatoCasa'); do = soup.find('div', id='risultatoOspite')
        if dc and do:
            nc = [x.get_text(strip=True) for x in dc.find_all('div', class_='parziale') if x.get_text(strip=True).isdigit()]
            no = [x.get_text(strip=True) for x in do.find_all('div', class_='parziale') if x.get_text(strip=True).isdigit()]
            p = ",".join([f"{nc[i]}-{no[i]}" for i in range(min(len(nc), len(no)))])
    except: pass
    return d, iso, l, m, p

def scrape_data():
    chrome_options = Options(); chrome_options.add_argument("--headless"); driver = webdriver.Chrome(options=chrome_options)
    all_results, all_standings, all_avulse = [], [], []
    
    for n, id_c in ALL_CAMPIONATI.items():
        id_work = CAMPIONATI_FINALI.get(n, id_c); base = "https://www.fipavcampania.it/mobile/" if "Serie" in n else "https://www.fipavsalerno.it/mobile/"
        try:
            driver.get(f"{base}risultati.asp?CampionatoId={id_work}"); soup = BeautifulSoup(driver.page_source, 'html.parser')
            divs = soup.find('div', style=lambda x: x and 'margin-top:7.5em' in x)
            if divs:
                cur_g = "N/D"
                for el in divs.children:
                    if el.name == 'div' and 'divGiornata' in el.get('class', []): cur_g = el.get_text(strip=True)
                    elif el.name == 'a' and 'gara' in el.get('class', []):
                        pt_c = el.find('div', class_='setCasa').get_text(strip=True) if el.find('div', class_='setCasa') else ''
                        pt_o = el.find('div', class_='setOspite').get_text(strip=True) if el.find('div', class_='setOspite') else ''
                        c = el.find('div', class_='squadraCasa').get_text(strip=True).replace(pt_c, '').strip()
                        o = el.find('div', class_='squadraOspite').get_text(strip=True).replace(pt_o, '').strip()
                        dt, dtiso, luo, maps, parz = get_match_details_robust(driver, urljoin(base, el.get('href', '')))
                        all_results.append({'Campionato': n, 'Giornata': cur_g, 'Squadra Casa': c, 'Squadra Ospite': o, 'Punteggio': f"{pt_c}-{pt_o}" if pt_c else "", 'Data': dt, 'DataISO': dtiso, 'Impianto': luo, 'Maps': maps, 'Set Casa': pt_c, 'Set Ospite': pt_o, 'Parziali': parz})
            driver.get(f"{base}risultati.asp?CampionatoId={id_c}&vis=classifica"); tabs = pd.read_html(StringIO(driver.page_source))
            if tabs: df = tabs[0]; df['Campionato'] = n; all_standings.append(df)
        except: pass

    for n, id_c in CAMPIONATI_AVULSI.items():
        dom = "fipavcampania.it" if "Serie" in n else "fipavsalerno.it"
        try:
            driver.get(f"https://www.{dom}/classifica.aspx?tipo=avulsa&CId={id_c}"); time.sleep(2)
            tabs = pd.read_html(StringIO(driver.page_source), decimal=',', thousands='.')
            if tabs:
                df_a = max(tabs, key=len).astype(str); df_a.columns = [f"col_{i}" for i in range(len(df_a.columns))]
                df_a['Campionato_Ref'] = n; all_avulse.append(df_a)
        except: pass

    driver.quit()
    # FIX PER KEYERROR: Se all_results è vuoto, creiamo un DF con le colonne corrette
    cols = ['Campionato', 'Giornata', 'Squadra Casa', 'Squadra Ospite', 'Punteggio', 'Data', 'DataISO', 'Impianto', 'Maps', 'Set Casa', 'Set Ospite', 'Parziali']
    df_res = pd.DataFrame(all_results) if all_results else pd.DataFrame(columns=cols)
    df_std = pd.concat(all_standings, ignore_index=True) if all_standings else pd.DataFrame(columns=['Campionato', 'Squadra', 'P.'])
    df_avu = pd.concat(all_avulse, ignore_index=True) if all_avulse else pd.DataFrame(columns=['Campionato_Ref'])
    return df_res, df_std, df_avu

# ================= 5. GENERATORI =================

def genera_landing_page():
    print("📄 Generazione Landing Page...")
    html = f"""<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"><title>{NOME_VISUALIZZATO}</title><link rel="manifest" href="manifest.json">{CSS_BASE}</head><body><div class="app-header"><div class="header-left"><img src="{URL_LOGO}" class="logo-main"><h1>{NOME_VISUALIZZATO}</h1></div><div class="nav-buttons"><a href="{FILE_SCORE}"><img src="{BTN_SCOREBOARD}" class="nav-icon-img"></a></div></div><div class="landing-container"><div class="choice-card"><img src="{URL_SPLIT_IMG}" class="choice-img"><div class="click-overlay"><a href="{FILE_MALE}" class="click-area"></a><a href="{FILE_FEMALE}" class="click-area"></a></div></div><div class="social-section"><div class="social-icons"><a href="https://facebook.com/111542261731361" target="_blank"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" class="social-icon-img"></a><a href="https://instagram.com/asdcspastena_volley/" target="_blank"><img src="https://upload.wikimedia.org/wikipedia/commons/e/e7/Instagram_logo_2016.svg" class="social-icon-img"></a></div></div></div><div class="footer-counter"><img src="{URL_COUNTER}"><br><span class="version-text">{APP_VERSION}</span><div class="footer-msg">{FOOTER_MSG}</div></div><div id="android-popup" class="install-popup"><b>Installa l'App Ufficiale</b><br><button class="btn-install-app" onclick="alert('Usa il menu di Chrome > Installa App')">INSTALLA</button><br><button onclick="closePopup('android-popup')" style="border:none;background:none;color:#999">Più tardi</button></div></body></html>"""
    with open(FILE_LANDING, "w", encoding="utf-8") as f: f.write(html)

def genera_pagina_app(df_ris, df_class, df_avulse, filename, camp_target):
    title = "Settore Maschile" if "maschile" in filename else "Settore Femminile"
    nav = f'<a href="#" onclick="openModal()"><span id="btn-calendar" class="calendar-container"><img src="{BTN_CALENDAR_EVENTS}" class="nav-icon-img"></span></a><a href="{"generale_m.html" if "maschile" in filename else "generale_f.html"}"><img src="{BTN_ALL_RESULTS}" class="nav-icon-img"></a><a href="{FILE_SCORE}"><img src="{BTN_SCOREBOARD}" class="nav-icon-img"></a>'
    html = f'<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{title}</title>{CSS_BASE}</head><body><div id="modal-overlay" class="modal-overlay" onclick="closeModal()"><div class="modal-content" onclick="event.stopPropagation()"><div class="modal-header"><div class="modal-title">📅 Prossimi Appuntamenti</div><button class="close-btn" onclick="closeModal()">×</button></div><div id="modal-body"></div></div></div><div class="app-header"><div class="header-left" onclick="location.href=\'index.html\'"><img src="{URL_LOGO}" class="logo-main"><h1>{title}</h1></div><div class="nav-buttons">{nav}</div></div>'
    
    camps = [c for c in camp_target.keys() if c in df_class['Campionato'].unique()]
    html += '<div class="tab-bar">'
    for i, c in enumerate(camps): html += f'<button id="btn-{i}" class="tab-btn {"active" if i==0 else ""}" onclick="openTab({i})">{c.split(" Gir.")[0]}</button>'
    html += '</div>'

    for i, c in enumerate(camps):
        html += f'<div id="content-{i}" class="tab-content {"active" if i==0 else ""}">'
        if c in CAMPIONATI_FINALI: html += f'<div class="finals-banner">🏆 Fasi Finali Provinciali</div>' + BRACKET_HTML
        html += f"<h2>🏆 Classifica Girone</h2>"
        df_c = df_class[df_class['Campionato'] == c].sort_values(by='P.')
        html += '<div class="table-card"><div class="table-scroll"><table><thead><tr><th>Pos</th><th>Squadra</th><th>Pt</th><th>G</th><th>V</th><th>P</th><th>SF</th><th>SS</th></tr></thead><tbody>'
        for _, r in df_c.iterrows():
            cls = 'class="my-team-row"' if is_target_team(r.get('Squadra','')) else ''
            html += f"<tr {cls}><td>{r.get('P.','-')}</td><td>{r.get('Squadra','?')}</td><td><b>{r.get('Pu.',0)}</b></td><td>{r.get('G.G.',0)}</td><td>{r.get('G.V.',0)}</td><td>{r.get('G.P.',0)}</td><td>{r.get('S.F.',0)}</td><td>{r.get('S.S.',0)}</td></tr>"
        html += '</tbody></table></div></div>'

        if not df_avulse.empty and c in df_avulse['Campionato_Ref'].unique():
            html += f"<h2 style='color: #1565c0; border-left-color: #1565c0;'>🏅 Classifica Generale (Avulsa)</h2>"
            df_a = df_avulse[df_avulse['Campionato_Ref'] == c]
            html += '<div class="table-card" style="border: 1px solid #bbdefb;"><div class="table-scroll"><table><thead><tr style="background-color: #e3f2fd;"><th>Pos</th><th>Squadra</th><th>Pz.</th><th>P/G</th><th>Pt</th><th>G</th><th>V</th><th>P</th><th>SF</th><th>SS</th></tr></thead><tbody>'
            for _, r in df_a.iterrows():
                cls = 'class="my-team-row"' if is_target_team(r['col_1']) else ''
                def f_dec(v): v=str(v).replace('nan','-').replace('.',','); return v[:-2] if v.endswith(',0') else v
                html += f"<tr {cls}><td>{r['col_0']}</td><td>{r['col_1']}</td><td>{r['col_2']}</td><td>{f_dec(r['col_3'])}</td><td><b>{r['col_4']}</b></td><td>{r['col_5']}</td><td>{r['col_6']}</td><td>{r['col_7']}</td><td>{r['col_8']}</td><td>{r['col_9']}</td></tr>"
            html += '</tbody></table></div></div>'
        
        html += f"<h2>📅 Calendario</h2>"
        html += f'<div class="calendar-controls"><button class="btn-tool" onclick="toggleSort({i})">📅 Ordina</button><button class="btn-tool" onclick="printCalendar()">🖨️ Stampa</button></div><div id="calendar-container-{i}">'
        df_t = df_ris[df_ris['Campionato'] == c]
        df_t_my = df_t[df_t['Squadra Casa'].apply(is_target_team) | df_t['Squadra Ospite'].apply(is_target_team)]
        for _, r in df_t_my.iterrows(): html += crea_card_html(r, c, True)
        html += '</div></div>'
    html += f'<div class="footer-counter"><img src="{URL_COUNTER}"><br><span class="version-text">{APP_VERSION}</span></div></body></html>'
    with open(filename, "w", encoding="utf-8") as f: f.write(html)

def genera_pagina_generale(df_ris, df_class, filename, camp_target):
    nav = f'<a href="index.html"><img src="{BTN_TODIS_RESULTS}" class="nav-icon-img"></a>'
    html = f'<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Risultati</title>{CSS_BASE}</head><body><div class="app-header" style="background:#1976D2"><div class="header-left" onclick="location.href=\'index.html\'"><img src="{URL_LOGO}" class="logo-main"><h1>Tutti i Risultati</h1></div><div class="nav-buttons">{nav}</div></div>'
    camps = [c for c in camp_target.keys() if c in df_class['Campionato'].unique()]
    html += '<div class="tab-bar">'
    for i, c in enumerate(camps): html += f'<button id="btn-{i}" class="tab-btn {"active" if i==0 else ""}" onclick="openTab({i})">{c.split(" Gir.")[0]}</button>'
    html += '</div>'
    for i, c in enumerate(camps):
        html += f'<div id="content-{i}" class="tab-content {"active" if i==0 else ""}">'
        html += f'<div class="calendar-controls"><button class="btn-tool" onclick="toggleSort({i})">📅 Ordina</button></div><div id="calendar-container-{i}">'
        df_r = df_ris[df_ris['Campionato'] == c]
        for _, r in df_r.iterrows(): html += crea_card_html(r, c, False)
        html += '</div></div>'
    html += '</body></html>'
    with open(filename, "w", encoding="utf-8") as f: f.write(html)

def genera_segnapunti():
    print("📄 Generazione Segnapunti...")
    html = f'<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"><title>Segnapunti</title>{SCOREBOARD_CODE}</head></html>'
    with open(FILE_SCORE, "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    df_ris, df_class, df_avulse = scrape_data()
    genera_landing_page()
    genera_pagina_app(df_ris, df_class, df_avulse, FILE_MALE, CAMPIONATI_MASCHILI)
    genera_pagina_app(df_ris, df_class, df_avulse, FILE_FEMALE, CAMPIONATI_FEMMINILI)
    genera_pagina_generale(df_ris, df_class, FILE_GEN_MALE, CAMPIONATI_MASCHILI)
    genera_pagina_generale(df_ris, df_class, FILE_GEN_FEMALE, CAMPIONATI_FEMMINILI)
    genera_segnapunti()
    print(f"✅ Generazione {APP_VERSION} completata!")
