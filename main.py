import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from io import StringIO
from urllib.parse import urljoin, quote
import re 
from datetime import datetime, timedelta
import os

# ================= CONFIGURAZIONE =================
NOME_VISUALIZZATO = "TODIS PASTENA VOLLEY"

TARGET_TEAM_ALIASES = [
    "TODIS PASTENA VOLLEY",
    "TODIS CS PASTENA VOLLEY",
    "TODIS C.S. PASTENA VOLLEY"
]

FILE_APP = "index.html"
FILE_GEN = "generale.html"
FILE_SCORE = "segnapunti.html"

# URL LOGO
URL_LOGO = "https://raw.githubusercontent.com/robertobrigantino-blip/todis-volley/main/logo.jpg"
URL_COUNTER = "https://hits.sh/robertobrigantino-blip.github.io/todis-volley.svg?style=flat&label=VISITE&extraCount=0&color=d32f2f"

CAMPIONATI = {
    "Serie D  Maschile Gir.C": "85622",
    "Serie C  Femminile Gir.A": "85471",
    "Under 18 Femminile Gir.B": "86850",
    "Under 16 Femminile Gir.A": "86853",
    "Under 14 Femminile Gir.C": "86860",
}

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
    .app-header { background-color: #d32f2f; color: white; padding: 10px 15px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 5px rgba(0,0,0,0.2); position: sticky; top:0; z-index:1000; }
    .header-left { display: flex; align-items: center; gap: 10px; }
    .app-header img { height: 35px; width: 35px; border-radius: 50%; border: 2px solid white; object-fit: cover; }
    .app-header h1 { margin: 0; font-size: 14px; text-transform: uppercase; line-height: 1.1; font-weight: 700; }
    .last-update { font-size: 9px; opacity: 0.9; font-weight: normal; }
    .nav-buttons { display: flex; gap: 8px; }
    .btn-nav { background: rgba(255,255,255,0.2); color: white; text-decoration: none; font-size: 18px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: 50%; border: 1px solid rgba(255,255,255,0.4); }
    .btn-nav.active { background: white; color: #d32f2f; }
    .tab-bar { background-color: white; display: flex; overflow-x: auto; white-space: nowrap; position: sticky; top: 54px; z-index: 99; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-bottom: 1px solid #eee; }
    .tab-btn { flex: 1; padding: 12px 15px; text-align: center; background: none; border: none; font-size: 13px; font-weight: 500; color: #666; border-bottom: 3px solid transparent; cursor: pointer; min-width: 100px; }
    .tab-btn.active { color: #d32f2f; border-bottom: 3px solid #d32f2f; font-weight: bold; }
    .tab-content { display: none; padding: 15px; max-width: 800px; margin: 0 auto; animation: fadeIn 0.3s; }
    .tab-content.active { display: block; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    h2 { color: #d32f2f; font-size: 16px; border-left: 4px solid #d32f2f; padding-left: 8px; margin-top: 15px; margin-bottom: 12px; }
    .table-card { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; width: 100%; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; white-space: nowrap; }
    th { background-color: #ffebee; color: #c62828; padding: 10px 6px; text-align: center; font-weight: bold; font-size: 11px; text-transform: uppercase; }
    td { padding: 10px 6px; text-align: center; border-bottom: 1px solid #f0f0f0; }
    td:nth-child(2) { text-align: left; min-width: 140px; font-weight: 500; position: sticky; left: 0; background-color: white; border-right: 1px solid #eee; }
    .my-team-row td { background-color: #fff3e0 !important; font-weight: bold; }
    .match-card { background: white; border-radius: 8px; padding: 12px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid #ddd; position: relative; overflow: hidden; }
    .match-card.win { border-left-color: #2e7d32; } 
    .match-card.loss { border-left-color: #c62828; } 
    .match-card.upcoming { border-left-color: #ff9800; } 
    .result-badge { position: absolute; top: 0; right: 0; font-size: 9px; padding: 3px 6px; border-bottom-left-radius: 6px; font-weight: bold; color: white; z-index: 10; text-transform: uppercase; }
    .badge-win { background-color: #2e7d32; }
    .badge-loss { background-color: #c62828; }
    .badge-played { background-color: #78909c; } 
    .match-header { display: flex; align-items: center; gap: 8px; font-size: 11px; color: #666; margin-bottom: 8px; border-bottom: 1px solid #f5f5f5; padding-bottom: 5px; padding-right: 50px; }
    .date-badge { font-weight: bold; color: #d32f2f; display: flex; align-items: center; gap: 4px; }
    .teams { display: flex; flex-direction: column; gap: 6px; font-size: 14px; margin-bottom: 8px; }
    .team-row { display: flex; justify-content: space-between; align-items: center; }
    .my-team-text { color: #d32f2f; font-weight: 700; }
    .team-score { font-weight: bold; background: #eee; padding: 2px 8px; border-radius: 4px; min-width: 25px; text-align: center; }
    .match-footer { margin-top: 8px; padding-top: 8px; border-top: 1px solid #f5f5f5; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; }
    .gym-name { font-size: 11px; color: #666; width: 100%; display: block; margin-bottom: 5px; }
    .action-buttons { display: flex; gap: 5px; width: 100%; justify-content: flex-end; }
    .btn { text-decoration: none; padding: 5px 10px; border-radius: 15px; font-size: 10px; font-weight: bold; display: flex; align-items: center; gap: 3px; border: 1px solid transparent; }
    .btn-map { background-color: #e3f2fd; color: #1565c0; border-color: #bbdefb; }
    .btn-cal { background-color: #f3e5f5; color: #7b1fa2; border-color: #e1bee7; } 
    .btn-wa { background-color: #e8f5e9; color: #2e7d32; border-color: #c8e6c9; } 
    .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 2000; display: none; align-items: center; justify-content: center; backdrop-filter: blur(2px); }
    .modal-content { background: white; width: 85%; max-width: 400px; max-height: 80vh; border-radius: 12px; padding: 20px; overflow-y: auto; position: relative; box-shadow: 0 10px 25px rgba(0,0,0,0.2); animation: slideUp 0.3s; }
    @keyframes slideUp { from { transform: translateY(50px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    .modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px; }
    .modal-title { font-size: 18px; font-weight: bold; color: #d32f2f; }
    .close-btn { background: #eee; border: none; font-size: 24px; padding: 0 10px; border-radius: 5px; color: #555; cursor: pointer; }
    .modal-content .match-card { border: 1px solid #eee; box-shadow: none; padding: 10px; margin-bottom: 8px; }
    .footer-counter { text-align: center; margin-top: 30px; padding: 20px 0; border-top: 1px solid #eee; }
    .footer-counter img { height: 20px; vertical-align: middle; }
    
    /* IOS INSTALL TIP */
    .ios-install-popup { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: white; padding: 15px; border-radius: 10px; box-shadow: 0 5px 20px rgba(0,0,0,0.3); z-index: 3000; width: 85%; max-width: 350px; text-align: center; display: none; animation: popUp 0.5s; }
    .ios-install-popup:after { content: ''; position: absolute; bottom: -10px; left: 50%; transform: translateX(-50%); border-width: 10px 10px 0; border-style: solid; border-color: white transparent transparent; }
    @keyframes popUp { from{transform:translate(-50%, 20px); opacity:0;} to{transform:translate(-50%, 0); opacity:1;} }
</style>
<script>
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('sw.js');
        });
    }

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

    window.onload = function() {
        // iOS Detection e Popup Installazione
        const isIos = /iphone|ipad|ipod/.test( window.navigator.userAgent.toLowerCase() );
        const isInStandaloneMode = ('standalone' in window.navigator) && (window.navigator.standalone);
        
        // Se è iOS e non è installata, mostra il suggerimento
        if (isIos && !isInStandaloneMode && document.getElementById('ios-popup')) {
            setTimeout(() => { document.getElementById('ios-popup').style.display = 'block'; }, 2000);
        }

        if (!document.title.toUpperCase().includes("TODIS") || document.title.includes("Segnapunti")) return;

        const today = new Date();
        today.setHours(0,0,0,0);
        let nextMatches = {};
        const allMatches = document.querySelectorAll('.match-card.upcoming');
        
        allMatches.forEach(card => {
            const isMyTeam = card.getAttribute('data-my-team');
            if(isMyTeam === 'true') {
                const dateStr = card.getAttribute('data-date-iso');
                const campName = card.getAttribute('data-camp');
                if (dateStr && campName) {
                    const parts = dateStr.split('-');
                    const matchDate = new Date(parts[0], parts[1]-1, parts[2]);
                    if (matchDate >= today) {
                        if (!nextMatches[campName] || matchDate < nextMatches[campName].date) {
                            nextMatches[campName] = { date: matchDate, html: card.outerHTML };
                        }
                    }
                }
            }
        });
        
        let popupHTML = "";
        let count = 0;
        for (const [camp, data] of Object.entries(nextMatches)) {
            popupHTML += `<h3>🏆 ${camp}</h3>`;
            popupHTML += data.html;
            count++;
        }
        
        if (count > 0) {
            const modalBody = document.getElementById('modal-body');
            if(modalBody) {
                modalBody.innerHTML = popupHTML;
                setTimeout(function(){
                    document.getElementById('modal-overlay').style.display = 'flex';
                }, 500);
            }
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
    
    .team-panel { display: flex; flex-direction: column; justify-content: center; align-items: center; position: relative; cursor: pointer; transition: background 0.2s; }
    .team-home { background-color: #1e3a8a; border-right: 2px solid #333; }
    .team-guest { background-color: #b91c1c; border-left: 2px solid #333; }
    .team-home:active, .team-guest:active { opacity: 0.9; }
    
    .team-name-input { background: transparent; border: none; color: rgba(255,255,255,0.8); font-size: 24px; font-weight: bold; text-align: center; width: 80%; margin-bottom: 10px; text-transform: uppercase; }
    .score-display { font-size: 180px; font-weight: 800; line-height: 1; user-select: none; }
    
    .service-ball { font-size: 30px; position: absolute; top: 20px; opacity: 0.1; transition: opacity 0.3s; }
    .serving .service-ball { opacity: 1; }
    
    .center-panel { background-color: #222; display: flex; flex-direction: column; justify-content: space-between; align-items: center; padding: 10px 5px; }
    .sets-box { text-align: center; margin-top: 5px; }
    .sets-label { font-size: 10px; color: #888; letter-spacing: 2px; }
    .sets-score { font-size: 35px; font-weight: bold; color: #fff; }
    .current-set-badge { background: #d32f2f; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-top: 5px; }
    
    .timer-box { text-align: center; }
    .timer-val { font-size: 28px; font-family: monospace; font-weight: bold; color: #fbbf24; }
    .btn-timer { background: #444; border: none; color: white; padding: 5px 15px; border-radius: 5px; margin-top: 5px; cursor: pointer; }
    
    /* FIX CONTROLS BOTTOM */
    .controls-bottom { display: flex; flex-direction: column; gap: 8px; width: 90%; margin-bottom: 10px; }
    
    .btn-ctrl { 
        padding: 10px; 
        border: none; 
        border-radius: 5px; 
        font-weight: bold; 
        cursor: pointer; 
        width: 100%; 
        color: white; 
        font-size: 12px; 
        text-decoration: none; 
        text-align: center; 
        display: block; 
        box-sizing: border-box; 
        font-family: inherit;
    }
    
    .btn-reset { background: #546e7a; }
    .btn-exit { background: #333; border: 1px solid #555; }
    .btn-fs { background: #000; border: 1px solid #444; }
    
    .fine-tune { display: flex; gap: 20px; margin-top: 10px; }
    .btn-tune { width: 40px; height: 40px; border-radius: 50%; border: 2px solid rgba(255,255,255,0.3); background: transparent; color: white; font-size: 20px; cursor: pointer; }
</style>
<div class="rotate-overlay"><div style="font-size: 50px;">🔄</div><h2>Ruota il dispositivo</h2><p>Il segnapunti funziona in orizzontale</p></div>
<div class="sb-container">
    <div class="team-panel team-home" id="colHome" onclick="addPoint('Home')">
        <div class="service-ball">🏐</div>
        <input type="text" class="team-name-input" value="CASA">
        <div class="score-display" id="scoreHome">0</div>
        <div class="fine-tune">
            <button class="btn-tune" onclick="adjScore('Home', -1); event.stopPropagation()">-</button>
            <button class="btn-tune" onclick="adjScore('Home', 1); event.stopPropagation()">+</button>
        </div>
    </div>
    <div class="center-panel">
        <div class="sets-box"><div class="sets-label">SETS</div><div class="sets-score"><span id="setsHome">0</span> - <span id="setsGuest">0</span></div><div class="current-set-badge" id="setNum">SET 1</div></div>
        <div class="timer-box"><div class="timer-val" id="timer">00:00</div><button class="btn-timer" onclick="toggleTimer()" id="btnTimer">START</button></div>
        <div class="controls-bottom">
            <button class="btn-ctrl" style="background:#2e7d32;" onclick="setServiceManual()">Battuta</button>
            <button class="btn-ctrl btn-fs" onclick="toggleFullScreen()">⛶ Full</button>
            <button class="btn-ctrl btn-reset" onclick="resetMatch()">Reset</button>
            <a href="index.html" class="btn-ctrl btn-exit">Esci</a>
        </div>
    </div>
    <div class="team-panel team-guest" id="colGuest" onclick="addPoint('Guest')">
        <div class="service-ball">🏐</div>
        <input type="text" class="team-name-input" value="OSPITI">
        <div class="score-display" id="scoreGuest">0</div>
        <div class="fine-tune">
            <button class="btn-tune" onclick="adjScore('Guest', -1); event.stopPropagation()">-</button>
            <button class="btn-tune" onclick="adjScore('Guest', 1); event.stopPropagation()">+</button>
        </div>
    </div>
</div>
<script>
    let scoreH = 0, scoreG = 0; let setsH = 0, setsG = 0; let currentSet = 1; let timerInt = null; let seconds = 0; let serving = null; 
    async function lockScreen() { try { await navigator.wakeLock.request('screen'); } catch(e){} }
    document.addEventListener('click', lockScreen, {once:true});
    function toggleFullScreen() { if (!document.fullscreenElement) { document.documentElement.requestFullscreen().catch(e => { console.log(e); }); } else { if (document.exitFullscreen) document.exitFullscreen(); } }
    function addPoint(team) { if(team === 'Home') scoreH++; else scoreG++; serving = team; updateUI(); checkSetWin(); }
    function adjScore(team, delta) { if(team === 'Home') scoreH = Math.max(0, scoreH + delta); else scoreG = Math.max(0, scoreG + delta); updateUI(); }
    function setServiceManual() { if (serving === 'Home') serving = 'Guest'; else serving = 'Home'; updateUI(); }
    function checkSetWin() {
        let limit = (currentSet === 5) ? 15 : 25;
        if ((scoreH >= limit && scoreH >= scoreG + 2) || (scoreG >= limit && scoreG >= scoreH + 2)) {
            let winner = (scoreH > scoreG) ? "CASA" : "OSPITI";
            setTimeout(() => {
                if (confirm(`SET TERMINATO!\\nVince: ${winner}\\n\\nIniziare il prossimo set?`)) {
                    if (scoreH > scoreG) setsH++; else setsG++;
                    if (setsH === 3 || setsG === 3) { alert(`PARTITA FINITA!\\nVince: ${winner}`); } 
                    else { currentSet++; scoreH = 0; scoreG = 0; stopTimer(); seconds = 0; updateTimer(); updateUI(); }
                }
            }, 100);
        }
    }
    function resetMatch() { if(!confirm("Sicuro di voler azzerare tutto?")) return; scoreH = 0; scoreG = 0; setsH = 0; setsG = 0; currentSet = 1; seconds = 0; stopTimer(); updateTimer(); updateUI(); }
    function updateUI() {
        document.getElementById('scoreHome').innerText = scoreH; document.getElementById('scoreGuest').innerText = scoreG;
        document.getElementById('setsHome').innerText = setsH; document.getElementById('setsGuest').innerText = setsG;
        document.getElementById('setNum').innerText = "SET " + currentSet;
        document.getElementById('colHome').classList.remove('serving'); document.getElementById('colGuest').classList.remove('serving');
        if(serving) document.getElementById('col' + serving).classList.add('serving');
    }
    function toggleTimer() { if(timerInt) stopTimer(); else startTimer(); }
    function startTimer() { document.getElementById('btnTimer').innerText = "STOP"; document.getElementById('btnTimer').style.background = "#d32f2f"; timerInt = setInterval(() => { seconds++; updateTimer(); }, 1000); }
    function stopTimer() { clearInterval(timerInt); timerInt = null; document.getElementById('btnTimer').innerText = "START"; document.getElementById('btnTimer').style.background = "#444"; }
    function updateTimer() { const m = Math.floor(seconds / 60).toString().padStart(2, '0'); const s = (seconds % 60).toString().padStart(2, '0'); document.getElementById('timer').innerText = `${m}:${s}`; }
</script>
"""

# ================= HELPER FUNCTIONS =================
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

# ================= GENERATORE HTML CARD =================
def crea_card_html(r, camp, is_focus_mode=False):
    is_home = is_target_team(r['Squadra Casa'])
    is_away = is_target_team(r['Squadra Ospite'])
    is_my_match = is_home or is_away
    
    cs = 'class="team-name my-team-text"' if is_home else 'class="team-name"'
    os = 'class="team-name my-team-text"' if is_away else 'class="team-name"'
    
    status_class = "upcoming"
    badge_html = ""
    
    if r['Punteggio']:
        try:
            sc, so = int(r['Set Casa']), int(r['Set Ospite'])
            if is_my_match:
                if (is_home and sc > so) or (is_away and so > sc):
                    status_class = "win"
                    badge_html = '<span class="result-badge badge-win">VINTA</span>'
                else:
                    status_class = "loss"
                    badge_html = '<span class="result-badge badge-loss">PERSA</span>'
            else:
                status_class = "played"
                badge_html = '<span class="result-badge badge-played">FINALE</span>'
        except: status_class = "played"
    
    lnk_wa = create_whatsapp_link(r)
    lnk_cal = create_google_calendar_link(r) if not r['Punteggio'] else ""
    lnk_map = r['Maps']
    
    btns_html = ""
    if lnk_map: btns_html += f'<a href="{lnk_map}" target="_blank" class="btn btn-map">📍 Mappa</a>'
    
    if is_my_match or not is_focus_mode:
        if lnk_cal: btns_html += f'<a href="{lnk_cal}" target="_blank" class="btn btn-cal">📅</a>'
        if lnk_wa: btns_html += f'<a href="{lnk_wa}" target="_blank" class="btn btn-wa">💬</a>'

    return f"""
    <div class="match-card {status_class}" data-date-iso="{r['DataISO']}" data-camp="{camp}" data-my-team="{str(is_my_match).lower()}">
        {badge_html}
        <div class="match-header">
            <span class="date-badge">📅 {r['Data']}</span> <span>|</span> <span>{r['Giornata']}</span>
        </div>
        <div class="teams">
            <div class="team-row"><span {cs}>{r['Squadra Casa']}</span><span class="team-score">{r['Set Casa']}</span></div>
            <div class="team-row"><span {os}>{r['Squadra Ospite']}</span><span class="team-score">{r['Set Ospite']}</span></div>
        </div>
        <div class="match-footer">
            <span class="gym-name">🏟️ {r['Impianto']}</span>
            <div class="action-buttons">{btns_html}</div>
        </div>
    </div>
    """

# ================= SCRAPING =================
def get_match_details_robust(driver, match_url):
    data_ora_full, data_iso, luogo, link_maps = "Data da definire", "", "Impianto non definito", ""
    try:
        driver.get(match_url)
        time.sleep(0.3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        clean_text = re.sub(r'\s+', ' ', soup.get_text(separator=" ", strip=True).replace(u'\xa0', u' '))
        
        date_pattern = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4}).*?(\d{1,2}[:\.]\d{2})', clean_text)
        if date_pattern:
            d, o = date_pattern.group(1), date_pattern.group(2)
            data_ora_full = f"{d} ⏰ {o}"
            try: data_iso = datetime.strptime(d, "%d/%m/%Y").strftime("%Y-%m-%d")
            except: pass
        else:
            sd = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})', clean_text)
            if sd: 
                data_ora_full = sd.group(1)
                try: data_iso = datetime.strptime(data_ora_full, "%d/%m/%Y").strftime("%Y-%m-%d")
                except: pass

        imp = soup.find('div', class_='divImpianto')
        if imp: luogo = imp.get_text(strip=True)
        
        a_map = soup.find('a', href=lambda x: x and ('google.com/maps' in x or 'maps.google' in x))
        if a_map: 
            link_maps = a_map['href']
        elif luogo != "Impianto non definito": 
            clean_gym = re.sub(r'\s+', ' ', luogo).strip()
            link_maps = f"https://www.google.com/maps/search/?api=1&query={quote(clean_gym)}"
    except: pass
    return data_ora_full, data_iso, luogo, link_maps

def scrape_data():
    print("🚀 Avvio scraping TOTALE...")
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    driver = webdriver.Chrome(options=chrome_options)
    all_results, all_standings = [], []

    for nome_camp, id_camp in CAMPIONATI.items():
        print(f"   Analisi: {nome_camp}...")
        base_url = "https://www.fipavsalerno.it/mobile/"
        if "Serie C" in nome_camp or "Serie D" in nome_camp: base_url = "https://www.fipavcampania.it/mobile/"
        
        driver.get(f"{base_url}risultati.asp?CampionatoId={id_camp}")
        time.sleep(1.5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        div_giornata = soup.find('div', style="margin-top:7.5em;; text-align:center;")
        curr_giornata = "N/D"
        if div_giornata:
            for el in div_giornata.children:
                if el.name == 'div' and 'divGiornata' in el.get('class', []): curr_giornata = el.get_text(strip=True)
                elif el.name == 'a' and 'gara' in el.get('class', []):
                    c = el.find('div', class_='squadraCasa').get_text(strip=True)
                    o = el.find('div', class_='squadraOspite').get_text(strip=True)
                    pt_c = el.find('div', class_='setCasa').get_text(strip=True) if el.find('div', class_='setCasa') else ''
                    pt_o = el.find('div', class_='setOspite').get_text(strip=True) if el.find('div', class_='setOspite') else ''
                    c = c.replace(pt_c, '').strip()
                    o = o.replace(pt_o, '').strip()

                    full_url = urljoin(base_url, el.get('href', ''))
                    d_ora, d_iso, luogo, maps = get_match_details_robust(driver, full_url)
                    all_results.append({
                        'Campionato': nome_camp, 'Giornata': curr_giornata,
                        'Squadra Casa': c, 'Squadra Ospite': o,
                        'Punteggio': f"{pt_c}-{pt_o}" if pt_c else "", 
                        'Data': d_ora, 'DataISO': d_iso, 'Impianto': luogo, 'Maps': maps,
                        'Set Casa': pt_c, 'Set Ospite': pt_o
                    })
        try:
            driver.get(f"{base_url}risultati.asp?CampionatoId={id_camp}&vis=classifica")
            time.sleep(1)
            tabs = pd.read_html(StringIO(driver.page_source))
            if tabs:
                df_s = tabs[0]
                df_s['Campionato'] = nome_camp
                all_standings.append(df_s)
        except: pass

    driver.quit()
    return pd.DataFrame(all_results), pd.concat(all_standings, ignore_index=True) if all_standings else pd.DataFrame()

# ================= GENERATORE PAGINE =================
def genera_pagina(df_ris, df_class, filename, mode="APP"):
    print(f"📄 Generazione {filename} (Mode: {mode})...")
    is_app = (mode == "APP")
    is_score = (mode == "SCORE")
    
    title = NOME_VISUALIZZATO
    if is_score: title = "Segnapunti"
    elif not is_app: title = "Risultati Completi"
    
    nav_links = ""
    if is_score:
        nav_links = f'<a href="{FILE_APP}" class="btn-nav">🏠</a>'
    else:
        if is_app:
            nav_links = f'<a href="{FILE_GEN}" class="btn-nav" title="Tutti i risultati">🌍</a> <a href="{FILE_SCORE}" class="btn-nav" title="Segnapunti">🔢</a>'
        else:
            nav_links = f'<a href="{FILE_APP}" class="btn-nav" title="Home">🏠</a> <a href="{FILE_SCORE}" class="btn-nav" title="Segnapunti">🔢</a>'

    modal_html = ""
    ios_tip_html = ""
    if is_app:
        modal_html = """
        <div id="modal-overlay" class="modal-overlay" onclick="closeModal()">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header"><div class="modal-title">📅 Prossimi Appuntamenti</div><button class="close-btn" onclick="closeModal()">×</button></div>
                <div id="modal-body"></div>
                <div style="text-align:center; margin-top:15px;"><button onclick="closeModal()" style="background:#d32f2f; color:white; border:none; padding:8px 20px; border-radius:20px;">Chiudi</button></div>
            </div>
        </div>"""
        
        # POPUP ISTRUZIONI IOS
        ios_tip_html = """
        <div id="ios-popup" class="ios-install-popup">
            <div style="font-weight:bold; margin-bottom:10px;">Installa l'App</div>
            <div style="font-size:14px; margin-bottom:15px;">Per un'esperienza migliore e schermo intero:</div>
            <div style="font-size:14px; margin-bottom:10px;">1. Premi il tasto Condividi <span style="font-size:18px">📤</span></div>
            <div style="font-size:14px;">2. Scorri e premi "Aggiungi alla schermata Home" <span style="font-size:18px">➕</span></div>
            <button onclick="closeIosPopup()" style="margin-top:15px; padding:5px 15px; border:none; background:#eee; border-radius:10px;">Chiudi</button>
        </div>
        """
    
    footer_html = f'<div class="footer-counter"><img src="{URL_COUNTER}" alt="Visite"></div>' if is_app else ""

    html = f"""<!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="theme-color" content="#d32f2f">
        
        <!-- APPLE IOS META TAGS SPECIFICI -->
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="Todis Volley">
        
        <title>{title}</title>
        <link rel="icon" type="image/png" href="{URL_LOGO}">
        <link rel="apple-touch-icon" href="{URL_LOGO}">
        
        <!-- PWA Manifest -->
        <link rel="manifest" href="manifest.json">
        {CSS_BASE}
        {'<style>.app-header { background-color: #1976D2; }</style>' if mode == "GENERAL" else ''} 
        {'<style>.app-header { display:none; } </style>' if is_score else ''} 
    </head>
    <body>
        {modal_html}
        {ios_tip_html}
    """
    
    if not is_score:
        html += f"""
        <div class="app-header">
            <div class="header-left">
                <img src="{URL_LOGO}" alt="Logo">
                <div><h1>{title}</h1><div class="last-update">{time.strftime("%d/%m %H:%M")}</div></div>
            </div>
            <div class="nav-buttons">{nav_links}</div>
        </div>"""

    if is_score:
        html += SCOREBOARD_CODE
    else:
        campionati_disp = df_class['Campionato'].unique()
        html += '<div class="tab-bar">'
        for i, camp in enumerate(campionati_disp):
            p = camp.split()
            n = f"{p[0]} {p[1]}" if len(p) > 1 else camp
            if "Gir." in camp: n += " " + camp.split("Gir.")[1].strip()
            html += f'<button id="btn-{i}" class="tab-btn {"active" if i==0 else ""}" onclick="openTab({i})">{n}</button>'
        html += '</div>'

        for i, camp in enumerate(campionati_disp):
            html += f'<div id="content-{i}" class="tab-content {"active" if i==0 else ""}">'
            html += f"<h2>🏆 Classifica</h2>"
            df_c = df_class[df_class['Campionato'] == camp].sort_values(by='P.')
            html += """<div class="table-card"><div class="table-scroll"><table><thead><tr><th>Pos</th><th>Squadra</th><th>Pt</th><th>G</th><th>V</th><th>P</th><th>SF</th><th>SS</th></tr></thead><tbody>"""
            for _, r in df_c.iterrows():
                cls = 'class="my-team-row"' if is_target_team(r['Squadra']) else ''
                html += f"<tr {cls}><td>{r.get('P.','-')}</td><td>{r.get('Squadra','?')}</td><td><b>{r.get('Pu.',0)}</b></td><td>{r.get('G.G.',0)}</td><td>{r.get('G.V.',0)}</td><td>{r.get('G.P.',0)}</td><td>{r.get('S.F.',0)}</td><td>{r.get('S.S.',0)}</td></tr>"
            html += '</tbody></table></div></div>'

            html += f"<h2>📅 Calendario</h2>"
            df_r = df_ris[df_ris['Campionato'] == camp]
            if is_app:
                mask = df_r['Squadra Casa'].apply(is_target_team) | df_r['Squadra Ospite'].apply(is_target_team)
                df_r = df_r[mask]
            
            if df_r.empty:
                html += "<p>Nessuna partita trovata.</p>"
            else:
                if not is_app:
                    giornate = df_r['Giornata'].unique()
                    for g in giornate:
                        html += f'<h3 style="background:#eee; padding:5px; border-radius:4px; margin:10px 0;">{g}</h3>'
                        for _, r in df_r[df_r['Giornata'] == g].iterrows(): html += crea_card_html(r, camp, is_app)
                else:
                    for _, r in df_r.iterrows(): html += crea_card_html(r, camp, is_app)
            html += '</div>'

    html += footer_html
    html += "</body></html>"
    with open(filename, "w", encoding="utf-8") as f: f.write(html)
    print(f"✅ Creato: {filename}")

if __name__ == "__main__":
    df_ris, df_class = scrape_data()
    genera_pagina(df_ris, df_class, FILE_APP, mode="APP")
    genera_pagina(df_ris, df_class, FILE_GEN, mode="GENERAL")
    genera_pagina(pd.DataFrame(), pd.DataFrame(), FILE_SCORE, mode="SCORE")
