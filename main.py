# ==============================================================================
# SOFTWARE VERSION: v4.9
# RELEASE NOTE: Fix NameError & Added U19M Finals Override
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

# ================= 1. CONFIGURAZIONE =================
NOME_VISUALIZZATO = "TODIS PASTENA VOLLEY"
APP_VERSION = "v4.9 | Fasi Finali Provinciali 🏆"

FOOTER_MSG = "🐾 <span style='color: #d32f2f; font-weight: 900; font-size: 13px; letter-spacing: 1px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);'>LINCI GO!</span> 🏐"    
                                                                        
TARGET_TEAM_ALIASES = [
    "TODIS PASTENA VOLLEY",
    "TODIS CS PASTENA VOLLEY",
    "TODIS C.S. PASTENA VOLLEY",
    "CS PASTENA"
]

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

# CAMPIONATI ORDINARI (Gironi)
CAMPIONATI_MASCHILI = {
    "Serie D  Gir.C S.Maschile": "85622",
    "Under 19 Gir.A S.Maschile": "86865",
    "Under 17 Gir.B S.Maschile": "86864",
    "Under 15 Gir.B S.Maschile": "86848",
}

CAMPIONATI_FEMMINILI = {
    "Serie C  Gir.A S.Femminile": "85471",
    "Under 18 Gir.B S.Femminile": "86850",
    "Under 16 Gir.A S.Femminile": "86853",
    "Under 14 Gir.C S.Femminile": "86860",
    "Under 13 Gir.B S.Femminile": "88820",
}

# OVERRIDE FASI FINALI (Aggiornato con U19M)
CAMPIONATI_FINALI = {
    "Under 18 Gir.B S.Femminile": "89371",
    "Under 19 Gir.A S.Maschile": "89301",
}

# CLASSIFICHE AVULSE
CAMPIONATI_AVULSI = {
    "Serie C  Gir.A S.Femminile": "85473",
    "Under 14 Gir.C S.Femminile": "86858",
    "Under 16 Gir.A S.Femminile": "86853",
    "Under 18 Gir.B S.Femminile": "86849",
    "Serie D  Gir.C S.Maschile": "85620",
    "Under 19 Gir.A S.Maschile": "86865",
}

ALL_CAMPIONATI = {**CAMPIONATI_MASCHILI, **CAMPIONATI_FEMMINILI}

# ================= 2. FUNZIONI HELPER (Definite prima degli usi) =================

def is_target_team(team_name):
    if pd.isna(team_name) or not str(team_name).strip(): return False
    name_clean = str(team_name).upper().strip()
    for alias in TARGET_TEAM_ALIASES:
        if alias.upper() in name_clean: return True
    return False

def create_google_calendar_link(row):
    if not row['DataISO']: return ""
    title = quote(f"🏐 {row['Squadra Casa']} vs {row['Squadra Ospite']}")
    location = quote(row['Impianto']) if row['Impianto'] else ""
    time_match = re.search(r'⏰\s*(\d{1,2}[:\.]\d{2})', row['Data'])
    if time_match:
        ora_str = time_match.group(1).replace('.', ':')
        try:
            dt_start = datetime.strptime(f"{row['DataISO']} {ora_str}", "%Y-%m-%d %H:%M")
            dt_end = dt_start + timedelta(hours=2)
            dates = f"{dt_start.strftime('%Y%m%dT%H%M00')}/{dt_end.strftime('%Y%m%dT%H%M00')}"
        except: dates = f"{row['DataISO'].replace('-','')}T120000/{row['DataISO'].replace('-','')}T140000"
    else:
        date_clean = row['DataISO'].replace('-', '')
        dates = f"{date_clean}/{date_clean}"
    return f"https://www.google.com/calendar/render?action=TEMPLATE&text={title}&dates={dates}&location={location}&details=Campionato+{quote(row['Campionato'])}"

def create_whatsapp_link(row):
    if row['Punteggio']:
        text = f"🏐 *Risultato {row['Campionato']}*\n{row['Squadra Casa']} {row['Set Casa']} - {row['Set Ospite']} {row['Squadra Ospite']}"
    else:
        text = f"📅 *Gara {row['Campionato']}*\n{row['Data']}\n📍 {row['Impianto']}\n{row['Squadra Casa']} vs {row['Squadra Ospite']}"
    return f"https://wa.me/?text={quote(text)}"

def crea_card_html(r, camp, is_focus_mode=False):
    is_home = is_target_team(r['Squadra Casa'])
    is_away = is_target_team(r['Squadra Ospite'])
    is_my_match = is_home or is_away
    cs = 'class="team-info my-team-text"' if is_home else 'class="team-info"'
    os = 'class="team-info my-team-text"' if is_away else 'class="team-info"'
    status_class = "upcoming"
    sc_val = r['Set Casa'] if r['Set Casa'] else "-"
    so_val = r['Set Ospite'] if r['Set Ospite'] else "-"

    if r['Punteggio']:
        try:
            sc, so = int(r['Set Casa']), int(r['Set Ospite'])
            bg_c = "bg-green" if sc > so else "bg-red"
            bg_o = "bg-green" if so > sc else "bg-red"
            if is_my_match: status_class = "win" if ((is_home and sc > so) or (is_away and so > sc)) else "loss"
            else:
                status_class = "played"
                bg_c, bg_o = "bg-gray", "bg-gray"
            if r['Parziali'] and str(r['Parziali']).strip():
                matches = re.findall(r'(\d+)\s*-\s*(\d+)', str(r['Parziali']))
                if matches:
                    partials_c = "".join([f'<div class="partial-badge">{p[0]}</div>' for p in matches])
                    partials_o = "".join([f'<div class="partial-badge">{p[1]}</div>' for p in matches])
                    sc_val = f'<div class="scores-wrapper"><div class="partials-inline">{partials_c}</div><div class="set-total {bg_c}">{sc}</div></div>'
                    so_val = f'<div class="scores-wrapper"><div class="partials-inline">{partials_o}</div><div class="set-total {bg_o}">{so}</div></div>'
        except: status_class = "played"
    
    btns_html = f'<a href="{r["Maps"]}" target="_blank" class="btn btn-map">📍 Mappa</a>' if r['Maps'] else ""
    if is_my_match or not is_focus_mode:
        if not r['Punteggio']: btns_html += f'<a href="{create_google_calendar_link(r)}" target="_blank" class="btn btn-cal">📅</a>'
        btns_html += f'<a href="{create_whatsapp_link(r)}" target="_blank" class="btn btn-wa">💬</a>'

    return f"""
    <div class="match-card {status_class}" data-date-iso="{r['DataISO']}" data-camp="{camp}" data-my-team="{str(is_my_match).lower()}">
        <div class="match-header"><span>📅 {r['Data']}</span> <span>|</span> <span>{r['Giornata']}</span></div>
        <div class="teams">
            <div class="team-row"><span {cs}>{r['Squadra Casa']}</span>{sc_val}</div>
            <div class="team-row"><span {os}>{r['Squadra Ospite']}</span>{so_val}</div>
        </div>
        <div class="match-footer" onclick="event.stopPropagation()">
            <span class="gym-name">🏟️ {r['Impianto']}</span>
            <div class="action-buttons">{btns_html}</div>
        </div>
    </div>
    """

# ================= 3. CSS E SCRIPT =================
CSS_BASE = """
<style>
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    html, body { height: 100%; margin: 0; padding: 0; font-family: 'Roboto', sans-serif; background-color: #f0f2f5; color: #333; overflow-x: hidden; }
    body { display: flex; flex-direction: column; }
    .app-header { background-color: #d32f2f; color: white; padding: 0 15px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 5px rgba(0,0,0,0.2); height: 60px; flex-shrink: 0; z-index: 1000; position: sticky; top: 0; }
    .header-left { display: flex; align-items: center; gap: 10px; cursor: pointer; }
    .app-header img.logo-main { height: 40px; width: 40px; border-radius: 50%; border: 2px solid white; object-fit: cover; }
    .app-header h1 { margin: 0; font-size: 13px; text-transform: uppercase; line-height: 1.1; font-weight: 700; }   
    .nav-buttons { display: flex; gap: 8px; align-items: center; }
    .nav-icon-img { height: 42px; width: auto; transition: transform 0.1s; filter: drop-shadow(0 2px 3px rgba(0,0,0,0.3)); cursor: pointer; }
    .calendar-container { position: relative; display: none; }
    .calendar-container.has-events { display: inline-block; animation: pulse-icon 2s infinite; }
    .calendar-container.has-events::after { content: ''; position: absolute; top: 2px; right: 2px; width: 10px; height: 10px; background: #ffeb3b; border-radius: 50%; border: 2px solid #d32f2f; z-index: 11; }
    @keyframes pulse-icon { 0% { transform: scale(1); } 50% { transform: scale(1.08); } 100% { transform: scale(1); } }
    .landing-container { flex: 1; display: flex; flex-direction: column; justify-content: space-around; align-items: center; padding: 5px 0; overflow: hidden; }
    .instruction-text { font-weight: 700; color: #555; font-size: 11px; text-transform: uppercase; margin: 0; }
    .choice-card { position: relative; width: 92%; max-width: 450px; display: flex; justify-content: center; align-items: center; }
    .choice-img { width: 100%; height: auto; max-height: 58vh; object-fit: contain; display: block; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
    .click-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; border-radius: 15px; overflow: hidden; }
    .click-area { width: 50%; height: 100%; cursor: pointer; }
    .social-section { text-align: center; margin: 5px 0; } 
    .social-icons { display: flex; justify-content: center; gap: 30px; }
    .social-icon-img { width: 34px; height: 34px; }
    .tab-bar { background-color: white; display: flex; overflow-x: auto; white-space: nowrap; position: sticky; top: 60px; z-index: 99; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-bottom: 1px solid #eee; flex-shrink: 0; scrollbar-width: none; }
    .tab-bar::-webkit-scrollbar { display: none; } 
    .tab-btn { flex: 1; padding: 10px 8px; text-align: center; background: none; border: none; font-size: 11px; font-weight: 600; color: #666; border-bottom: 3px solid transparent; cursor: pointer; min-width: 85px; text-transform: uppercase; }
    .tab-btn.active { color: #d32f2f; border-bottom: 3px solid #d32f2f; font-weight: bold; }
    .tab-content { display: none; padding: 15px; width: 100%; max-width: 800px; margin: 0 auto; animation: fadeIn 0.3s; }
    .tab-content.active { display: block; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    h2 { color: #d32f2f; font-size: 16px; border-left: 4px solid #d32f2f; padding-left: 8px; margin-top: 15px; margin-bottom: 12px; }
    
    .finals-banner { background: linear-gradient(45deg, #ffd700, #ff8f00); color: #000; padding: 12px; border-radius: 8px; text-align: center; font-weight: 900; margin-bottom: 15px; border: 2px solid #000; box-shadow: 0 4px 10px rgba(0,0,0,0.2); text-transform: uppercase; font-size: 13px; letter-spacing: 1px; }

    .table-card { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; width: 100%; }
    .table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; width: 100%; }
    table { width: 100%; border-collapse: collapse; font-size: 11px; table-layout: fixed; }
    th, td { padding: 8px 4px; text-align: center; border-bottom: 1px solid #f0f0f0; }
    th { background-color: #ffebee; color: #c62828; font-weight: bold; text-transform: uppercase; font-size: 10px; }
    th:nth-child(1), td:nth-child(1) { width: 30px; }
    th:nth-child(2), td:nth-child(2) { width: 120px; text-align: left; position: sticky; left: 0; background-color: white; z-index: 10; border-right: 1px solid #eee; white-space: normal; word-wrap: break-word; line-height: 1.2; }
    th:nth-child(3), td:nth-child(3) { width: 35px; font-weight: 800; background-color: #fafafa; }
    th:not(:nth-child(-n+3)), td:not(:nth-child(-n+3)) { width: 28px; font-size: 9px; }
    .my-team-row td { background-color: #fff3e0 !important; font-weight: bold; }
    .my-team-row td:nth-child(2) { background-color: #fff3e0 !important; }
    
    .match-card { background: white; border-radius: 8px; padding: 12px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid #ddd; position: relative; width: 100%; }
    .match-card.win { border-left-color: #2e7d32; } .match-card.loss { border-left-color: #c62828; } .match-card.upcoming { border-left-color: #ff9800; } 
    .match-header { display: flex; align-items: center; gap: 8px; font-size: 11px; color: #666; margin-bottom: 10px; border-bottom: 1px solid #f5f5f5; padding-bottom: 5px; }
    .team-row { display: flex; justify-content: space-between; align-items: center; width: 100%; gap: 10px; margin-bottom: 8px; }
    .team-info { flex: 1; min-width: 0; font-size: 14px; line-height: 1.2; white-space: normal; word-wrap: break-word; }
    .my-team-text { color: #d32f2f; font-weight: 700; }
    .scores-wrapper { display: flex !important; flex-direction: row !important; align-items: center !important; gap: 6px; flex-shrink: 0; }
    .partials-inline { display: flex !important; flex-direction: row !important; gap: 3px; }
    .partial-badge { width: 22px; height: 22px; background-color: #7986cb; color: white; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: bold; flex-shrink: 0; }
    .set-total { width: 26px; height: 26px; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px; flex-shrink: 0; }
    .bg-green { background-color: #2e7d32; } .bg-red { background-color: #c62828; } .bg-gray { background-color: #78909c; }
    .match-footer { margin-top: 8px; padding-top: 8px; border-top: 1px solid #f5f5f5; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; }
    .gym-name { font-size: 9px; color: #666; width: 100%; margin-bottom: 5px; flex: 1; }
    .action-buttons { display: flex; gap: 5px; justify-content: flex-end; }
    .btn { text-decoration: none; padding: 4px 8px; border-radius: 12px; font-size: 9px; font-weight: bold; display: flex; align-items: center; gap: 3px; border: 1px solid transparent; }
    .btn-map { background-color: #e3f2fd; color: #1565c0; border-color: #bbdefb; }
    .btn-cal { background-color: #f3e5f5; color: #7b1fa2; border-color: #e1bee7; } .btn-wa { background-color: #e8f5e9; color: #2e7d32; border-color: #c8e6c9; } 
    .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 2000; display: none; align-items: center; justify-content: center; backdrop-filter: blur(2px); }
    .modal-content { background: white; width: 90%; max-width: 400px; max-height: 80vh; border-radius: 12px; padding: 15px; overflow-y: auto; position: relative; }
    .modal-header { display: flex !important; flex-direction: row !important; justify-content: space-between !important; align-items: center !important; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px; width: 100%; }
    .modal-title { font-size: 16px; font-weight: bold; color: #d32f2f; margin: 0; }
    .close-btn { background: #eee; border: none; font-size: 22px; padding: 2px 10px; border-radius: 6px; color: #333; cursor: pointer; line-height: 1; }
    .calendar-controls { display: flex; gap: 8px; margin-bottom: 12px; justify-content: flex-end; position: relative; z-index: 10; }
    .btn-tool { font-size: 10px; padding: 6px 12px; background: #fff; border: 1px solid #ccc; border-radius: 15px; cursor: pointer; color: #555; font-weight: bold; transition: 0.2s; z-index: 11; }
    .btn-tool.active { background: #d32f2f; color: white; border-color: #d32f2f; }
    .install-popup { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: white; padding: 20px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); z-index: 5000; width: 85%; max-width: 350px; text-align: center; display: none; border: 3px solid #d32f2f; animation: slideUp 0.5s ease-out; }
    @keyframes slideUp { from { transform: translate(-50%, 150%); } to { transform: translate(-50%, 0); } }
    .btn-install-app { background: #d32f2f; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; width: 100%; margin: 10px 0; font-size: 14px; cursor: pointer; }
    .footer-counter { text-align: center; padding: 8px 0; background: white; border-top: 1px solid #eee; flex-shrink: 0; width: 100%; }
    .footer-msg { font-size: 10px; color: #d32f2f; margin: 0; font-weight: bold; }
    @media print {
        html, body { height: auto !important; overflow: visible !important; display: block !important; background: white !important; }
        .app-header, .tab-bar, .calendar-controls, .footer-counter, .install-popup, .btn-map, .btn-cal, .btn-wa, .close-btn { display: none !important; }
        .tab-content { display: none !important; }
        .tab-content.active { display: block !important; width: 100% !important; height: auto !important; }
    }
</style>
<script>
    if ('serviceWorker' in navigator) { window.addEventListener('load', () => { navigator.serviceWorker.register('sw.js').catch(err => console.log('SW Error', err)); }); }
    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault(); deferredPrompt = e;
        if (!/iphone|ipad|ipod/.test(window.navigator.userAgent.toLowerCase())) {
            setTimeout(() => { const p = document.getElementById('android-popup'); if(p) p.style.display = 'block'; }, 2000);
        }
    });
    async function triggerAndroidInstall() {
        if (deferredPrompt) { deferredPrompt.prompt(); await deferredPrompt.userChoice; deferredPrompt = null; closePopup('android-popup'); }
        else { alert("Usa il menu di Chrome (3 puntini) e seleziona 'Installa App'."); }
    }
    function closePopup(id) { document.getElementById(id).style.display = 'none'; }
    function openModal() { document.getElementById('modal-overlay').style.display = 'flex'; }
    function closeModal() { document.getElementById('modal-overlay').style.display = 'none'; }
    function printCalendar() { window.print(); }
    function openTab(tabIndex) {
        var contents = document.getElementsByClassName("tab-content");
        for (var i = 0; i < contents.length; i++) contents[i].classList.remove("active");
        var buttons = document.getElementsByClassName("tab-btn");
        for (var i = 0; i < buttons.length; i++) buttons[i].classList.remove("active");
        document.getElementById("content-" + tabIndex).classList.add("active");
        document.getElementById("btn-" + tabIndex).classList.add("active");
    }
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
            btn.innerHTML = "🔢 Per Giornata";
            btn.setAttribute('data-sorted', 'true');
            btn.classList.add('active');
        } else {
            container.innerHTML = originalOrder[tabId];
            btn.innerHTML = "📅 Per Data";
            btn.setAttribute('data-sorted', 'false');
            btn.classList.remove('active');
        }
    }
    window.onload = function() {
        const isIos = /iphone|ipad|ipod/.test(window.navigator.userAgent.toLowerCase());
        const isStandalone = window.navigator.standalone === true;
        if (isIos && !isStandalone) { setTimeout(() => { const p = document.getElementById('ios-popup'); if(p) p.style.display = 'block'; }, 3000); }
        if (document.title.includes("Maschile") || document.title.includes("Femminile")) {
            const today = new Date(); today.setHours(0,0,0,0);
            let nextMatches = {};
            document.querySelectorAll('.match-card.upcoming').forEach(card => {
                if(card.getAttribute('data-my-team') === 'true') {	 
                    const dateStr = card.getAttribute('data-date-iso');
                    const campName = card.getAttribute('data-camp'); 
                    const parts = dateStr.split('-');
                    const matchDate = new Date(parts[0], parts[1]-1, parts[2]);
                    if (matchDate >= today) {
                        if (!nextMatches[campName] || matchDate < nextMatches[campName].date) {
                            nextMatches[campName] = { date: matchDate, html: card.outerHTML };
                        }
                    }
                }
            });
            let popupHTML = "";
            for (const [camp, data] of Object.entries(nextMatches)) {
                const campPulito = camp.replace(' S.Femminile', '').replace(' S.Maschile', '');
                popupHTML += `<h3 style="color:#d32f2f; font-size:14px; margin-top:10px; border-bottom:1px solid #eee">🏆 ${campPulito}</h3>` + data.html;			   
            }
            if (popupHTML !== "") {
                const modalBody = document.getElementById('modal-body');										 
                if(modalBody) {
                    modalBody.innerHTML = popupHTML;							 
                    const btnCal = document.getElementById('btn-calendar');
                    if(btnCal) { btnCal.style.display = 'inline-block'; btnCal.classList.add('has-events'); }
                }
            }
        }
    };
</script>
"""

# ================= 4. SCRAPING (Versione Robusta) =================

def get_match_details_robust(driver, match_url):
    data_ora_full, data_iso, luogo, link_maps, parziali_str = "Data da definire", "", "Impianto non definito", "", ""
    try:
        driver.get(match_url)
        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "divImpianto")))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        clean_text = re.sub(r'\s+', ' ', soup.get_text(separator=" ", strip=True).replace(u'\xa0', u' '))
        date_pattern = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4}).*?(\d{1,2}[:\.]\d{2})', clean_text)
        if date_pattern:
            d, o = date_pattern.group(1), date_pattern.group(2)
            data_ora_full = f"{d} ⏰ {o}"
            try: data_iso = datetime.strptime(d, "%d/%m/%Y").strftime("%Y-%m-%d")
            except: pass
        imp = soup.find('div', class_='divImpianto')
        if imp: luogo = imp.get_text(strip=True)
        a_map = soup.find('a', href=lambda x: x and ('google.com/maps' in x or 'maps.google' in x))
        if a_map: link_maps = a_map['href']
        elif luogo != "Impianto non definito": link_maps = f"https://www.google.com/maps/search/?api=1&query={quote(luogo)}"
        div_casa = soup.find('div', id='risultatoCasa'); div_ospite = soup.find('div', id='risultatoOspite')
        if div_casa and div_ospite:
            nums_casa = [d.get_text(strip=True) for d in div_casa.find_all('div', class_='parziale') if re.search(r'\d+', d.get_text())]
            nums_ospite = [d.get_text(strip=True) for d in div_ospite.find_all('div', class_='parziale') if re.search(r'\d+', d.get_text())]
            parziali_str = ",".join([f"{nums_casa[i]}-{nums_ospite[i]}" for i in range(min(len(nums_casa), len(nums_ospite)))])
    except: pass
    return data_ora_full, data_iso, luogo, link_maps, parziali_str

def scrape_data():
    chrome_options = Options(); chrome_options.add_argument("--headless"); driver = webdriver.Chrome(options=chrome_options)
    all_results, all_standings, all_avulse = [], [], []
    
    # 1. Risultati e Classifica Girone
    for nome_camp, id_camp in ALL_CAMPIONATI.items():
        # Override se in Fasi Finali
        id_da_usare = CAMPIONATI_FINALI.get(nome_camp, id_camp)
        base_url = "https://www.fipavsalerno.it/mobile/"
        if "Serie" in nome_camp: base_url = "https://www.fipavcampania.it/mobile/"
        try:
            driver.get(f"{base_url}risultati.asp?CampionatoId={id_da_usare}")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            div_giornata = soup.find('div', style=lambda x: x and 'margin-top:7.5em' in x)
            curr_giornata = "N/D"
            if div_giornata:
                for el in div_giornata.children:
                    if el.name == 'div' and 'divGiornata' in el.get('class', []): curr_giornata = el.get_text(strip=True)
                    elif el.name == 'a' and 'gara' in el.get('class', []):
                        pt_c = el.find('div', class_='setCasa').get_text(strip=True) if el.find('div', class_='setCasa') else ''
                        pt_o = el.find('div', class_='setOspite').get_text(strip=True) if el.find('div', class_='setOspite') else ''
                        c = el.find('div', class_='squadraCasa').get_text(strip=True).replace(pt_c, '').strip()
                        o = el.find('div', class_='squadraOspite').get_text(strip=True).replace(pt_o, '').strip()
                        d_ora, d_iso, luogo, maps, parziali = get_match_details_robust(driver, urljoin(base_url, el.get('href', '')))
                        all_results.append({'Campionato': nome_camp, 'Giornata': curr_giornata, 'Squadra Casa': c, 'Squadra Ospite': o, 'Punteggio': f"{pt_c}-{pt_o}" if pt_c else "", 'Data': d_ora, 'DataISO': d_iso, 'Impianto': luogo, 'Maps': maps, 'Set Casa': pt_c, 'Set Ospite': pt_o, 'Parziali': parziali})
            
            driver.get(f"{base_url}risultati.asp?CampionatoId={id_camp}&vis=classifica")
            tabs = pd.read_html(StringIO(driver.page_source))
            if tabs:
                df_s = tabs[0]; df_s['Campionato'] = nome_camp; all_standings.append(df_s)
        except: pass

    # 2. Classifiche Avulse
    for nome_camp, id_camp in CAMPIONATI_AVULSI.items():
        try:
            dominio = "fipavcampania.it" if "Serie" in nome_camp else "fipavsalerno.it"
            url_avulsa = f"https://www.{dominio}/classifica.aspx?tipo=avulsa&CId={id_camp}"
            driver.get(url_avulsa)
            time.sleep(2)
            tabs = pd.read_html(StringIO(driver.page_source), decimal=',', thousands='.')
            if tabs:
                df_a = max(tabs, key=len).astype(str)
                df_a.columns = [f"col_{i}" for i in range(len(df_a.columns))]
                df_a['Campionato_Ref'] = nome_camp 
                all_avulse.append(df_a)
        except: pass

    driver.quit()
    return pd.DataFrame(all_results), pd.concat(all_standings, ignore_index=True) if all_standings else pd.DataFrame(), pd.concat(all_avulse, ignore_index=True) if all_avulse else pd.DataFrame()

# ================= 5. GENERATORI PAGINE =================

def genera_landing_page():
    print(f"📄 Generazione Landing Page...")
    html = f"""<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"><meta name="theme-color" content="#d32f2f"><title>{NOME_VISUALIZZATO}</title><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"><link rel="icon" type="image/png" href="{URL_LOGO}"><link rel="apple-touch-icon" href="{URL_LOGO}"><link rel="manifest" href="manifest.json">{CSS_BASE}</head><body><div class="app-header"><div class="header-left"><img src="{URL_LOGO}" alt="Logo" class="logo-main"><h1>{NOME_VISUALIZZATO}</h1></div><div class="nav-buttons"><a href="{FILE_SCORE}" title="Segnapunti"><img src="{BTN_SCOREBOARD}" class="nav-icon-img"></a></div></div><div class="landing-container"><div class="instruction-text">Seleziona il settore:</div><div class="choice-card"><img src="{URL_SPLIT_IMG}" alt="Campionato" class="choice-img"><div class="click-overlay"><a href="{FILE_MALE}" class="click-area"></a><a href="{FILE_FEMALE}" class="click-area"></a></div></div><div class="social-section"><div class="social-icons"><a href="https://www.facebook.com/111542261731361?ref=_xav_ig_profile_page_web" target="_blank"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" class="social-icon-img"></a><a href="https://www.instagram.com/asdcspastena_volley/" target="_blank"><img src="https://upload.wikimedia.org/wikipedia/commons/e/e7/Instagram_logo_2016.svg" class="social-icon-img"></a></div></div></div><div class="footer-counter"><img src="{URL_COUNTER}" alt="Visite"><br><span class="version-text">{APP_VERSION}</span><div class="footer-msg">{FOOTER_MSG}</div></div><div id="android-popup" class="install-popup"><div style="font-weight:bold; font-size:16px; margin-bottom:5px;">Installa l'App Ufficiale</div><div style="font-size:13px;">Accedi ai risultati più velocemente e usa l'app a tutto schermo!</div><button class="btn-install-app" onclick="triggerAndroidInstall()">INSTALLA ORA</button><button class="btn-close-popup" onclick="closePopup('android-popup')">Magari più tardi</button></div><div id="ios-popup" class="install-popup"><div style="font-weight:bold; font-size:16px; margin-bottom:5px;">Installa su iPhone</div><div style="font-size:13px; margin-bottom:10px;">1. Premi <b>Condividi</b> <span style="font-size:18px">📤</span><br>2. Seleziona <b>"Aggiungi alla schermata Home"</b> ➕</div><button class="btn-install-app" onclick="closePopup('ios-popup')">HO CAPITO</button></div></body></html>"""
    with open(FILE_LANDING, "w", encoding="utf-8") as f: f.write(html)

def genera_pagina_app(df_ris, df_class, df_avulse, filename, campionati_target):
    page_title = "Settore Maschile" if "maschile" in filename else "Settore Femminile"
    origin = "maschile" if "maschile" in filename else "femminile"
    nav_links = f'<a href="#" onclick="openModal(); return false;"><span id="btn-calendar" class="calendar-container"><img src="{BTN_CALENDAR_EVENTS}" class="nav-icon-img"></span></a><a href="{"generale_m.html" if origin=="maschile" else "generale_f.html"}?from={origin}"><img src="{BTN_ALL_RESULTS}" class="nav-icon-img"></a><a href="{FILE_SCORE}"><img src="{BTN_SCOREBOARD}" class="nav-icon-img"></a>'

    html = f'<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{page_title}</title>{CSS_BASE}</head><body>'
    html += f'<div id="modal-overlay" class="modal-overlay" onclick="closeModal()"><div class="modal-content" onclick="event.stopPropagation()"><div class="modal-header"><div class="modal-title">📅 Prossimi Appuntamenti</div><button class="close-btn" onclick="closeModal()">×</button></div><div id="modal-body"></div></div></div>'
    html += f'<div class="app-header"><div class="header-left" onclick="window.location.href=\'index.html\'"><img src="{URL_LOGO}" class="logo-main"><div><h1>{page_title}</h1><div class="last-update">{time.strftime("%d/%m %H:%M")}</div></div></div><div class="nav-buttons">{nav_links}</div></div>'

    campionati_disp = [c for c in campionati_target.keys() if c in df_class['Campionato'].unique()]
    html += '<div class="tab-bar">'
    for i, camp in enumerate(campionati_disp): html += f'<button id="btn-{i}" class="tab-btn {"active" if i==0 else ""}" onclick="openTab({i})">{camp.split(" Gir.")[0]}</button>'
    html += '</div>'

    for i, camp in enumerate(campionati_disp):
        html += f'<div id="content-{i}" class="tab-content {"active" if i==0 else ""}">'
        if camp in CAMPIONATI_FINALI:
            html += f'<div class="finals-banner">🏆 Fasi Finali Provinciali</div>'
        titolo_class = "🏆 Classifica Girone (Concluso)" if camp in CAMPIONATI_FINALI else "🏆 Classifica Girone"
        html += f"<h2>{titolo_class}</h2>"
        df_c = df_class[df_class['Campionato'] == camp].sort_values(by='P.')
        html += '<div class="table-card"><div class="table-scroll"><table><thead><tr><th>Pos</th><th>Squadra</th><th>Pt</th><th>G</th><th>V</th><th>P</th><th>SF</th><th>SS</th></tr></thead><tbody>'
        for _, r in df_c.iterrows():
            cls = 'class="my-team-row"' if is_target_team(r.get('Squadra')) else ''
            html += f"<tr {cls}><td>{r.get('P.','-')}</td><td>{r.get('Squadra','?')}</td><td><b>{r.get('Pu.',0)}</b></td><td>{r.get('G.G.',0)}</td><td>{r.get('G.V.',0)}</td><td>{r.get('G.P.',0)}</td><td>{r.get('S.F.',0)}</td><td>{r.get('S.S.',0)}</td></tr>"
        html += '</tbody></table></div></div>'

        if not df_avulse.empty and camp in df_avulse['Campionato_Ref'].unique():
            html += f"<h2 style='color: #1565c0; border-left-color: #1565c0;'>🏅 Classifica Generale (Ranking Finali)</h2>"
            df_a = df_avulse[df_avulse['Campionato_Ref'] == camp]
            html += '<div class="table-card" style="border: 1px solid #bbdefb;"><div class="table-scroll"><table><thead><tr style="background-color: #e3f2fd; color: #1565c0;"><th>Pos</th><th>Squadra</th><th>Pz.</th><th>P/G</th><th>Pt</th><th>G</th><th>V</th><th>P</th><th>SF</th><th>SS</th></tr></thead><tbody>'
            for _, r in df_a.iterrows():
                squadra_nome = str(r['col_1'])
                cls = 'class="my-team-row"' if is_target_team(squadra_nome) else ''
                def format_pg(val):
                    v = str(val).replace('nan', '-').strip().replace('.', ',')
                    if len(v) == 2 and ',' not in v and v.isdigit(): return f"{v[0]},{v[1]}"
                    return v
                html += f"<tr {cls}><td>{r['col_0']}</td><td>{squadra_nome}</td><td>{r['col_2']}</td><td>{format_pg(r['col_3'])}</td><td><b>{r['col_4']}</b></td><td>{r['col_5']}</td><td>{r['col_6']}</td><td>{r['col_7']}</td><td>{r['col_8']}</td><td>{r['col_9']}</td></tr>"
            html += '</tbody></table></div></div>'
        
        titolo_cal = "📅 Calendario Fasi Finali" if camp in CAMPIONATI_FINALI else "📅 Calendario TODIS"
        html += f"<h2>{titolo_cal}</h2>"
        html += f'<div class="calendar-controls"><button class="btn-tool" id="btn-sort-{i}" data-sorted="false" onclick="toggleSort({i})">📅 Ordina per Data</button><button class="btn-tool" onclick="printCalendar()">🖨️ Stampa</button></div>'
        html += f'<div id="calendar-container-{i}">'
        df_todis = df_ris[(df_ris['Campionato'] == camp) & (df_ris['Squadra Casa'].apply(is_target_team) | df_ris['Squadra Ospite'].apply(is_target_team))]
        for _, r in df_todis.iterrows(): html += crea_card_html(r, camp, True)
        html += '</div></div>'
    html += f'<div class="footer-counter"><img src="{URL_COUNTER}"><br><span class="version-text">{APP_VERSION}</span></div></body></html>'
    with open(filename, "w", encoding="utf-8") as f: f.write(html)

def genera_pagina_generale(df_ris, df_class, filename, campionati_target):
    nav_links = f'<a href="#" onclick="tornaAlSettore(); return false;"><img src="{BTN_TODIS_RESULTS}" class="nav-icon-img"></a><a href="{FILE_SCORE}"><img src="{BTN_SCOREBOARD}" class="nav-icon-img"></a>'
    html = f'<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Risultati Completi</title>{CSS_BASE}</head><body>'
    html += f'<div class="app-header" style="background:#1976D2"><div class="header-left" onclick="window.location.href=\'index.html\'"><img src="{URL_LOGO}" class="logo-main"><h1>Risultati Completi</h1></div><div class="nav-buttons">{nav_links}</div></div>'
    campionati_disp = [c for c in campionati_target.keys() if c in df_class['Campionato'].unique()]
    html += '<div class="tab-bar">'
    for i, camp in enumerate(campionati_disp): html += f'<button id="btn-{i}" class="tab-btn {"active" if i==0 else ""}" onclick="openTab({i})">{camp.split(" Gir.")[0]}</button>'
    html += '</div>'
    for i, camp in enumerate(campionati_disp):
        html += f'<div id="content-{i}" class="tab-content {"active" if i==0 else ""}">'
        html += f'<h2>🏆 Classifica</h2>'
        df_c = df_class[df_class['Campionato'] == camp].sort_values(by='P.')
        html += '<div class="table-card"><div class="table-scroll"><table><thead><tr><th>Pos</th><th>Squadra</th><th>Pt</th><th>G</th><th>V</th><th>P</th><th>SF</th><th>SS</th></tr></thead><tbody>'
        for _, r in df_c.iterrows():
            cls = 'class="my-team-row"' if is_target_team(r.get('Squadra')) else ''
            html += f"<tr {cls}><td>{r.get('P.','-')}</td><td>{r.get('Squadra','?')}</td><td><b>{r.get('Pu.',0)}</b></td><td>{r.get('G.G.',0)}</td><td>{r.get('G.V.',0)}</td><td>{r.get('G.P.',0)}</td><td>{r.get('S.F.',0)}</td><td>{r.get('S.S.',0)}</td></tr>"
        html += '</tbody></table></div></div>'
        html += f'<h2>📅 Calendario</h2>'
        html += f'<div class="calendar-controls"><button class="btn-tool" id="btn-sort-{i}" data-sorted="false" onclick="toggleSort({i})">📅 Ordina per Data</button><button class="btn-tool" onclick="printCalendar()">🖨️ Stampa</button></div>'
        html += f'<div id="calendar-container-{i}">'
        df_r = df_ris[df_ris['Campionato'] == camp]
        for g in df_r['Giornata'].unique():
            html += f'<h3 style="background:#eee; padding:5px; border-radius:4px; margin:10px 0;">{g}</h3>'
            for _, r in df_r[df_r['Giornata'] == g].iterrows(): html += crea_card_html(r, camp, False)
        html += '</div></div>'
    html += f'<div class="footer-counter"><img src="{URL_COUNTER}"><br><span class="version-text">{APP_VERSION}</span></div></body></html>'
    with open(filename, "w", encoding="utf-8") as f: f.write(html)

def genera_segnapunti():
    html = f'<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Segnapunti</title>{SCOREBOARD_CODE}</head></html>'
    with open(FILE_SCORE, "w", encoding="utf-8") as f: f.write(html)

# ================= 6. AVVIO =================

if __name__ == "__main__":
    df_ris, df_class, df_avulse = scrape_data()
    genera_landing_page()
    genera_pagina_app(df_ris, df_class, df_avulse, FILE_MALE, CAMPIONATI_MASCHILI)
    genera_pagina_app(df_ris, df_class, df_avulse, FILE_FEMALE, CAMPIONATI_FEMMINILI)
    genera_pagina_generale(df_ris, df_class, FILE_GEN_MALE, CAMPIONATI_MASCHILI)
    genera_pagina_generale(df_ris, df_class, FILE_GEN_FEMALE, CAMPIONATI_FEMMINILI)
    genera_segnapunti()
    print(f"✅ Generazione {APP_VERSION} completata!")
