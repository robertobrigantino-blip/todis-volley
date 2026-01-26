# ==============================================================================
# SOFTWARE VERSION: v2.9
# RELEASE NOTE: Classifiche Ottimizzate
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
APP_VERSION = "v2.9 | Stagione 25/26 - Ver. Finale 🏁"

# MESSAGGIO PERSONALIZZATO FOOTER
FOOTER_MSG = "🐾 <span style='color: #d32f2f; font-weight: 900; font-size: 15px; letter-spacing: 1px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);'>LINCI GO!</span> 🏐"    
                                                                        
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
    /* Reset e Layout Base */
    * { box-sizing: border-box; }
    html, body { 
        height: 100%; 
        margin: 0; 
        padding: 0; 
        font-family: 'Roboto', sans-serif; 
        background-color: #f0f2f5; 
        color: #333;
    }

    body { display: flex; flex-direction: column; overflow-x: hidden; }

    /* Header */
    .app-header { 
        background-color: #d32f2f; 
        color: white; 
        padding: 0 15px; 
        display: flex; 
        align-items: center; 
        justify-content: space-between; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.2); 
        height: 60px; 
        flex-shrink: 0; 
        z-index: 1000;
        position: sticky;
        top: 0;
    }
    .header-left { display: flex; align-items: center; gap: 10px; cursor: pointer; }
    .app-header img.logo-main { height: 40px; width: 40px; border-radius: 50%; border: 2px solid white; object-fit: cover; }
    .app-header h1 { margin: 0; font-size: 13px; text-transform: uppercase; line-height: 1.1; font-weight: 700; }   
    .nav-buttons { display: flex; gap: 8px; align-items: center; }
    .nav-icon-img { height: 42px; width: auto; transition: transform 0.1s; filter: drop-shadow(0 2px 3px rgba(0,0,0,0.3)); cursor: pointer; }

    /* --- LANDING PAGE --- */
    .landing-container { flex: 1; display: flex; flex-direction: column; justify-content: space-around; align-items: center; padding: 5px 0; overflow: hidden; }
    .instruction-text { font-weight: 700; color: #555; font-size: 11px; text-transform: uppercase; margin: 0; }
    .choice-card { position: relative; width: 92%; max-width: 450px; display: flex; justify-content: center; align-items: center; }
    .choice-img { width: 100%; height: auto; max-height: 58vh; object-fit: contain; display: block; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
	 
    .click-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; border-radius: 15px; overflow: hidden; }
    .click-area { width: 50%; height: 100%; cursor: pointer; }
    .social-section { text-align: center; margin: 5px 0; } 
    .social-icons { display: flex; justify-content: center; gap: 30px; }
    .social-icon-img { width: 34px; height: 34px; }
													  

    /* --- MENU TABS (CORRETTO) --- */

    .tab-bar { 
        background-color: white; 
        display: flex; 
        overflow-x: auto; 
        white-space: nowrap; 
        position: sticky; 
        top: 60px; 
        z-index: 99; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); 
        border-bottom: 1px solid #eee; 
        flex-shrink: 0;
        scrollbar-width: none; /* Nasconde scrollbar Firefox */
    }
    .tab-bar::-webkit-scrollbar { display: none; } /* Nasconde scrollbar Chrome/Safari */

    .tab-btn { 
        flex: 1; 
        padding: 10px 8px; /* Padding ridotto */
        text-align: center; 
        background: none; 
        border: none; 
        font-size: 11px; /* Font rimpicciolito come richiesto */
        font-weight: 600; 
        color: #666; 
        border-bottom: 3px solid transparent; 
        cursor: pointer; 
        min-width: 85px; /* Larghezza minima ridotta per farne stare di più */
        text-transform: uppercase;
    }

    .tab-btn.active { color: #d32f2f; border-bottom: 3px solid #d32f2f; font-weight: bold; }
    
    /* --- CONTENUTI --- */
    .tab-content { display: none; padding: 15px; max-width: 800px; margin: 0 auto; animation: fadeIn 0.3s; }
    .tab-content.active { display: block; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    h2 { color: #d32f2f; font-size: 16px; border-left: 4px solid #d32f2f; padding-left: 8px; margin-top: 15px; margin-bottom: 12px; }

/* --- CLASSIFICHE OTTIMIZZATE (Fix Disallineamento) --- */
    .table-card { 
        background: white; 
        border-radius: 8px; 
        overflow: hidden; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); 
        margin-bottom: 20px;
        width: 100%; /* Forza la tabella a stare nel contenitore */
    }
    .table-scroll { 
        overflow-x: auto; 
        -webkit-overflow-scrolling: touch; 
        width: 100%; 
    }
    table { 
        width: 100%; 
        border-collapse: collapse; 
        font-size: 11px; /* Leggermente più piccolo per mobile */
        table-layout: auto;
    }
    th { 
        background-color: #ffebee; 
        color: #c62828; 
        padding: 10px 4px; 
        text-align: center; 
        font-weight: bold; 
        text-transform: uppercase;
        font-size: 10px;
    }
    td { 
        padding: 10px 4px; 
        text-align: center; 
        border-bottom: 1px solid #f0f0f0; 
    }

    /* Colonna Squadra: il "cuore" del fix */
    th:nth-child(2), td:nth-child(2) { 
        text-align: left; 
        position: sticky; 
        left: 0; 
        background-color: white; 
        z-index: 10;
        border-right: 1px solid #eee;
        
        /* Gestione Nomi Lunghi */
        white-space: normal;    /* Permette il ritorno a capo */
        min-width: 110px;       /* Larghezza minima per il nome */
        max-width: 150px;       /* Impedisce alla colonna di espandersi troppo */
        line-height: 1.2;       /* Spaziatura riga per nomi su due linee */
        word-wrap: break-word;  /* Rompe parole eccessivamente lunghe se necessario */
    }
    
    /* Colonna Punti (PT): evidenziata */
    th:nth-child(3), td:nth-child(3) { 
        font-weight: 800; 
        color: #000;
        background-color: #fafafa;
        min-width: 30px;
    }

    /* Altre colonne statistiche: compatte */
    th:not(:nth-child(2)), td:not(:nth-child(2)) {
        min-width: 25px;
    }

    .my-team-row td { background-color: #fff3e0 !important; font-weight: bold; }
    .my-team-row td:nth-child(2) { background-color: #fff3e0 !important; } /* Fix per cella sticky */

    /* Match Cards */
    .match-card { background: white; border-radius: 8px; padding: 12px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid #ddd; position: relative; }
    .match-card.win { border-left-color: #2e7d32; } 
    .match-card.loss { border-left-color: #c62828; } 
    .match-card.upcoming { border-left-color: #ff9800; } 
    .match-header { display: flex; align-items: center; gap: 8px; font-size: 11px; color: #666; margin-bottom: 10px; border-bottom: 1px solid #f5f5f5; padding-bottom: 5px; }
    .teams { display: flex; flex-direction: column; gap: 8px; margin-bottom: 8px; }
    .team-row { display: flex; justify-content: space-between; align-items: center; width: 100%; }
    .team-info { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 14px; padding-right: 10px; }
    .my-team-text { color: #d32f2f; font-weight: 700; }
    .scores-wrapper { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
    .partials-inline { display: flex; flex-direction: row; gap: 3px; }
    .partial-badge { width: 24px; height: 24px; background-color: #7986cb; color: white; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; flex-shrink: 0; }
    .set-total { width: 28px; height: 28px; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 15px; flex-shrink: 0; }
    .bg-green { background-color: #2e7d32; } 
    .bg-red { background-color: #c62828; } 
    .bg-gray { background-color: #78909c; }
    .match-footer { margin-top: 8px; padding-top: 8px; border-top: 1px solid #f5f5f5; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; }
    .gym-name { font-size: 10px; color: #666; width: 100%; margin-bottom: 5px; }
    .action-buttons { display: flex; gap: 5px; width: 100%; justify-content: flex-end; }
    .btn { text-decoration: none; padding: 5px 10px; border-radius: 12px; font-size: 9px; font-weight: bold; display: flex; align-items: center; gap: 3px; border: 1px solid transparent; }
    .btn-map { background-color: #e3f2fd; color: #1565c0; border-color: #bbdefb; }
    .btn-cal { background-color: #f3e5f5; color: #7b1fa2; border-color: #e1bee7; } 
    .btn-wa { background-color: #e8f5e9; color: #2e7d32; border-color: #c8e6c9; } 

    /* Notifiche Calendario */
    .calendar-container { position: relative; display: none; }
    .calendar-container.has-events { display: inline-block; animation: pulse-icon 2s infinite; }
    .calendar-container.has-events::after { content: ''; position: absolute; top: 2px; right: 2px; width: 8px; height: 8px; background: #ffeb3b; border-radius: 50%; border: 2px solid #d32f2f; }
    @keyframes pulse-icon { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
	
    /* Modali */
    .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 2000; display: none; align-items: center; justify-content: center; backdrop-filter: blur(2px); }
    .modal-content { background: white; width: 90%; max-width: 400px; max-height: 80vh; border-radius: 12px; padding: 15px; overflow-y: auto; position: relative; }
    .modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px; }
    .modal-title { font-size: 16px; font-weight: bold; color: #d32f2f; }
    .close-btn { background: #eee; border: none; font-size: 20px; padding: 0 8px; border-radius: 5px; cursor: pointer; }

    /* Tools (Sort & Print) */
    .calendar-controls { display: flex; gap: 8px; margin-bottom: 12px; justify-content: flex-end; }
    .btn-tool { font-size: 10px; padding: 6px 12px; background: #fff; border: 1px solid #ccc; border-radius: 15px; cursor: pointer; color: #555; font-weight: bold; transition: 0.2s; }
    .btn-tool.active { background: #d32f2f; color: white; border-color: #d32f2f; }
	
    /* Footer Sottile */
    .footer-counter { text-align: center; padding: 8px 0; background: white; border-top: 1px solid #eee; flex-shrink: 0; }
    .footer-counter img { height: 16px; margin-bottom: 2px; }
    .version-text { font-size: 9px; color: #999; margin: 0; font-family: monospace; }
    .footer-msg { font-size: 10px; color: #d32f2f; margin: 0; font-weight: bold; }

    /* iOS Popup */
    .ios-install-popup { position: fixed; bottom: 15px; left: 50%; transform: translateX(-50%); background: white; padding: 12px; border-radius: 10px; box-shadow: 0 5px 20px rgba(0,0,0,0.3); z-index: 3000; width: 85%; max-width: 320px; text-align: center; display: none; }

    /* Print Stili */
    @media print {
        .app-header, .tab-bar, .nav-buttons, .calendar-controls, .footer-counter, .modal-overlay, .btn, .action-buttons, .ios-install-popup { display: none !important; }
        body { background: white; color: black; }
        .tab-content { display: block !important; }
        .match-card { border: 1px solid #ccc; break-inside: avoid; box-shadow: none; }
    }
</style>
<script>
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('sw.js')
            .then(registration => {
                registration.onupdatefound = () => {
                    const installingWorker = registration.installing;
                    installingWorker.onstatechange = () => {
                        if (installingWorker.state === 'installed') {
                            if (navigator.serviceWorker.controller) {
                                console.log('New content available; please refresh.');
                            } else {
                                console.log('Content is cached for offline use.');
                            }
                        }
                    };
                };
            })
            .catch(err => console.log('SW registration failed: ', err));
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
    function openModal() { document.getElementById('modal-overlay').style.display = 'flex'; }
    
    function tornaAlSettore() {
        const urlParams = new URLSearchParams(window.location.search);
        const origin = urlParams.get('from');
        if (origin === 'maschile') window.location.href = "maschile.html";
        else if (origin === 'femminile') window.location.href = "femminile.html";
        else window.location.href = "index.html";
    }

    // Toggle Details Function
    function toggleDetails(id) {
        const details = document.getElementById('details-' + id);
        const icon = document.getElementById('icon-' + id);
        if (details) {
            details.classList.toggle('open');
            if(icon) icon.classList.toggle('rotated');
        }
    }
    
    // Sort & Print Logic
    var originalOrder = {};
    
    function toggleSort(tabId) {
        const container = document.getElementById('calendar-container-' + tabId);
        const btn = document.getElementById('btn-sort-' + tabId);
        const isSorted = btn.getAttribute('data-sorted') === 'true';
        
        if (!originalOrder[tabId]) {
            originalOrder[tabId] = container.innerHTML;
        }
        
        if (!isSorted) {
            const cards = Array.from(container.querySelectorAll('.match-card'));
            const headers = container.querySelectorAll('h3');
            headers.forEach(h => h.style.display = 'none');
            
            cards.sort((a, b) => {
                const da = a.getAttribute('data-date-iso') || '9999-99-99';
                const db = b.getAttribute('data-date-iso') || '9999-99-99';
                return da.localeCompare(db);
            });
            
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
    
    function printCalendar() {
        window.print();
    }

    window.onload = function() {
        const isIos = /iphone|ipad|ipod/.test( window.navigator.userAgent.toLowerCase() );
        const isInStandaloneMode = ('standalone' in window.navigator) && (window.navigator.standalone);
        if (isIos && !isInStandaloneMode && document.getElementById('ios-popup')) {
            setTimeout(() => { document.getElementById('ios-popup').style.display = 'block'; }, 2000);
        }

        if (document.title.includes("Maschile") || document.title.includes("Femminile")) {
            const today = new Date();
            today.setHours(0,0,0,0);
            let nextMatches = {};
            
            document.querySelectorAll('.match-card.upcoming').forEach(card => {
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
                // RIMOZIONE STRINGA S.FEMMINILE / S.MASCHILE DAL TITOLO MODALE
                const campPulito = camp.replace(' S.Femminile', '').replace(' S.Maschile', '');
                popupHTML += `<h3>🏆 ${campPulito}</h3>`;
                popupHTML += data.html;
                count++;
            }
            
            if (count > 0) {
                const modalBody = document.getElementById('modal-body');
                const calContainer = document.getElementById('btn-calendar');
                if(modalBody && calContainer) {
                    modalBody.innerHTML = popupHTML;
                    calContainer.classList.add('has-events');
                    calContainer.style.display = 'inline-block';
                }
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
    .controls-bottom { display: flex; flex-direction: column; gap: 8px; width: 90%; margin-bottom: 10px; }
    .btn-ctrl { padding: 8px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; width: 100%; color: white; font-size: 12px; text-decoration: none; text-align: center; display: block; box-sizing: border-box; font-family: inherit; }
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
            if is_my_match:
                status_class = "win" if ((is_home and sc > so) or (is_away and so > sc)) else "loss"
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
        <div class="match-header">
            <span class="date-badge">📅 {r['Data']}</span> <span>|</span> <span>{r['Giornata']}</span>
        </div>
        <div class="teams">
            <div class="team-row"><span {cs}>{r['Squadra Casa']}</span><span class="team-score-wrapper">{sc_val}</span></div>
            <div class="team-row"><span {os}>{r['Squadra Ospite']}</span><span class="team-score-wrapper">{so_val}</span></div>
        </div>
        <div class="match-footer" onclick="event.stopPropagation()">
            <span class="gym-name">🏟️ {r['Impianto']}</span>
            <div class="action-buttons">{btns_html}</div>
        </div>
    </div>
    """

# ================= SCRAPING =================
def get_match_details_robust(driver, match_url):
    data_ora_full, data_iso, luogo, link_maps, parziali_str = "Data da definire", "", "Impianto non definito", "", ""
    try:
        driver.get(match_url)
        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CLASS_NAME, "divImpianto")))
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
        div_casa = soup.find('div', id='risultatoCasa')
        div_ospite = soup.find('div', id='risultatoOspite')
        if div_casa and div_ospite:
            nums_casa = [d.get_text(strip=True) for d in div_casa.find_all('div', class_='parziale') if re.search(r'\d+', d.get_text())]
            nums_ospite = [d.get_text(strip=True) for d in div_ospite.find_all('div', class_='parziale') if re.search(r'\d+', d.get_text())]
            parziali_str = ",".join([f"{nums_casa[i]}-{nums_ospite[i]}" for i in range(min(len(nums_casa), len(nums_ospite)))])
    except: pass
    return data_ora_full, data_iso, luogo, link_maps, parziali_str

def scrape_data():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    driver = webdriver.Chrome(options=chrome_options)
    all_results, all_standings = [], []
    for nome_camp, id_camp in ALL_CAMPIONATI.items():
        base_url = "https://www.fipavsalerno.it/mobile/"
        if "Serie C" in nome_camp or "Serie D" in nome_camp: base_url = "https://www.fipavcampania.it/mobile/"
        driver.get(f"{base_url}risultati.asp?CampionatoId={id_camp}")
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
        try:
            driver.get(f"{base_url}risultati.asp?CampionatoId={id_camp}&vis=classifica")
            tabs = pd.read_html(StringIO(driver.page_source))
            if tabs:
                df_s = tabs[0]
                df_s['Campionato'] = nome_camp
                all_standings.append(df_s)
        except: pass
    driver.quit()
    return pd.DataFrame(all_results), pd.concat(all_standings, ignore_index=True) if all_standings else pd.DataFrame()

# ================= GENERATORI PAGINE =================
def genera_landing_page():
    print(f"📄 Generazione Landing Page (Single Viewport)...")
    html = f"""<!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="theme-color" content="#d32f2f">
        <title>{NOME_VISUALIZZATO}</title>
        <link rel="icon" type="image/png" href="{URL_LOGO}">
        <link rel="apple-touch-icon" href="{URL_LOGO}">
        <meta name="apple-mobile-web-app-capable" content="yes">
        {CSS_BASE}
    </head>
    <body>
        <div class="app-header">
            <div class="header-left">
                <img src="{URL_LOGO}" alt="Logo" class="logo-main">
                <div><h1>{NOME_VISUALIZZATO}</h1></div>
            </div>
            <div class="nav-buttons">
                <a href="{FILE_SCORE}" title="Segnapunti"><img src="{BTN_SCOREBOARD}" class="nav-icon-img"></a>
            </div>
        </div>
        
        <div class="landing-container">
            <div class="instruction-text">Seleziona il settore:</div>
            
            <div class="choice-card">
                <img src="{URL_SPLIT_IMG}" alt="Scelta Campionato" class="choice-img">
                <div class="click-overlay">
                    <a href="{FILE_MALE}" class="click-area"></a>
                    <a href="{FILE_FEMALE}" class="click-area"></a>
                </div>
            </div>

            <div class="social-section">
                <div class="social-label">Seguici sui Social</div>
                <div class="social-icons">
                    <a href="https://www.facebook.com/111542261731361?ref=_xav_ig_profile_page_web" target="_blank">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/2021_Facebook_icon.svg" class="social-icon-img" alt="Facebook">
                    </a>
                    <a href="https://www.instagram.com/asdcspastena_volley/" target="_blank">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/e/e7/Instagram_logo_2016.svg" class="social-icon-img" alt="Instagram">
                    </a>
                </div>
            </div>
        </div>
        
        <div class="footer-counter">
            <img src="{URL_COUNTER}" alt="Visite"><br>
            <span class="version-text">{APP_VERSION}</span>
            <div class="footer-msg">{FOOTER_MSG}</div>
        </div>
    </body>
    </html>"""
    with open(FILE_LANDING, "w", encoding="utf-8") as f: 
        f.write(html)

def genera_pagina_app(df_ris, df_class, filename, campionati_target, mode="APP"):
    page_title = "Settore Maschile" if "maschile" in filename else "Settore Femminile"
    origin = "maschile" if "maschile" in filename else "femminile"
    nav_links = f'<a href="#" onclick="openModal(); return false;"><span id="btn-calendar" class="calendar-container"><img src="{BTN_CALENDAR_EVENTS}" class="nav-icon-img"></span></a><a href="{"generale_m.html" if origin=="maschile" else "generale_f.html"}?from={origin}"><img src="{BTN_ALL_RESULTS}" class="nav-icon-img"></a><a href="{FILE_SCORE}"><img src="{BTN_SCOREBOARD}" class="nav-icon-img"></a>'

    html = f'<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{page_title}</title>{CSS_BASE}</head><body>'
    html += f'<div id="modal-overlay" class="modal-overlay" onclick="closeModal()"><div class="modal-content" onclick="event.stopPropagation()"><div class="modal-header"><div class="modal-title">📅 Prossimi Appuntamenti</div><button class="close-btn" onclick="closeModal()">×</button></div><div id="modal-body"></div></div></div>'
    html += f'<div class="app-header"><div class="header-left" onclick="window.location.href=\'index.html\'"><img src="{URL_LOGO}" class="logo-main"><div><h1>{page_title}</h1><div class="last-update">{time.strftime("%d/%m %H:%M")}</div></div></div><div class="nav-buttons">{nav_links}</div></div>'

    campionati_disp = [c for c in campionati_target.keys() if c in df_class['Campionato'].unique()]
    html += '<div class="tab-bar">'
    for i, camp in enumerate(campionati_disp): html += f'<button id="btn-{i}" class="tab-btn {"active" if i==0 else ""}" onclick="openTab({i})">{camp.split(" S.")[0]}</button>'
    html += '</div>'

    for i, camp in enumerate(campionati_disp):
        html += f'<div id="content-{i}" class="tab-content {"active" if i==0 else ""}">'
        html += f"<h2>🏆 Classifica</h2>"
        df_c = df_class[df_class['Campionato'] == camp].sort_values(by='P.')
        html += '<div class="table-card"><div class="table-scroll"><table><thead><tr><th>Pos</th><th>Squadra</th><th>Pt</th><th>G</th><th>V</th><th>P</th><th>SF</th><th>SS</th></tr></thead><tbody>'
        for _, r in df_c.iterrows():
            cls = 'class="my-team-row"' if is_target_team(r['Squadra']) else ''
            html += f"<tr {cls}><td>{r.get('P.','-')}</td><td>{r.get('Squadra','?')}</td><td><b>{r.get('Pu.',0)}</b></td><td>{r.get('G.G.',0)}</td><td>{r.get('G.V.',0)}</td><td>{r.get('G.P.',0)}</td><td>{r.get('S.F.',0)}</td><td>{r.get('S.S.',0)}</td></tr>"
        html += '</tbody></table></div></div>'
        
        # AGGIUNTA PULSANTI E CONTAINER PER SORTING
        html += f"<h2>📅 Calendario TODIS</h2>"
        html += f'<div class="calendar-controls"><button class="btn-tool" id="btn-sort-{i}" data-sorted="false" onclick="toggleSort({i})">📅 Ordina per Data</button><button class="btn-tool" onclick="printCalendar()">🖨️ Stampa</button></div>'
        html += f'<div id="calendar-container-{i}">'
        df_todis = df_ris[(df_ris['Campionato'] == camp) & (df_ris['Squadra Casa'].apply(is_target_team) | df_ris['Squadra Ospite'].apply(is_target_team))]
        for _, r in df_todis.iterrows(): html += crea_card_html(r, camp, is_focus_mode=True)
        html += '</div></div>'

    html += f'<div class="footer-counter"><img src="{URL_COUNTER}"><br><span class="version-text">{APP_VERSION}</span></div></body></html>'
    with open(filename, "w", encoding="utf-8") as f: f.write(html)

def genera_pagina_generale(df_ris, df_class, filename, campionati_target, back_link):
    nav_links = f'<a href="#" onclick="tornaAlSettore(); return false;"><img src="{BTN_TODIS_RESULTS}" class="nav-icon-img"></a><a href="{FILE_SCORE}"><img src="{BTN_SCOREBOARD}" class="nav-icon-img"></a>'
    html = f'<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Risultati Completi</title>{CSS_BASE}</head><body>'
    html += f'<div class="app-header" style="background:#1976D2"><div class="header-left" onclick="window.location.href=\'index.html\'"><img src="{URL_LOGO}" class="logo-main"><h1>Risultati Completi</h1></div><div class="nav-buttons">{nav_links}</div></div>'
    
    campionati_disp = [c for c in campionati_target.keys() if c in df_class['Campionato'].unique()]
    html += '<div class="tab-bar">'
    for i, camp in enumerate(campionati_disp): html += f'<button id="btn-{i}" class="tab-btn {"active" if i==0 else ""}" onclick="openTab({i})">{camp.split(" S.")[0]}</button>'
    html += '</div>'

    for i, camp in enumerate(campionati_disp):
        html += f'<div id="content-{i}" class="tab-content {"active" if i==0 else ""}">'
        html += f'<h2>🏆 Classifica</h2>'
        df_c = df_class[df_class['Campionato'] == camp].sort_values(by='P.')
        html += '<div class="table-card"><div class="table-scroll"><table><thead><tr><th>Pos</th><th>Squadra</th><th>Pt</th><th>G</th><th>V</th><th>P</th><th>SF</th><th>SS</th></tr></thead><tbody>'
        for _, r in df_c.iterrows():
            cls = 'class="my-team-row"' if is_target_team(r['Squadra']) else ''
            html += f"<tr {cls}><td>{r.get('P.','-')}</td><td>{r.get('Squadra','?')}</td><td><b>{r.get('Pu.',0)}</b></td><td>{r.get('G.G.',0)}</td><td>{r.get('G.V.',0)}</td><td>{r.get('G.P.',0)}</td><td>{r.get('S.F.',0)}</td><td>{r.get('S.S.',0)}</td></tr>"
        html += '</tbody></table></div></div>'
        
        html += f'<h2>📅 Calendario</h2>'
        html += f'<div class="calendar-controls"><button class="btn-tool" id="btn-sort-{i}" data-sorted="false" onclick="toggleSort({i})">📅 Ordina per Data</button><button class="btn-tool" onclick="printCalendar()">🖨️ Stampa</button></div>'
        html += f'<div id="calendar-container-{i}">'
        df_r = df_ris[df_ris['Campionato'] == camp]
        for g in df_r['Giornata'].unique():
            html += f'<h3 style="background:#eee; padding:5px; border-radius:4px; margin:10px 0;">{g}</h3>'
            for _, r in df_r[df_r['Giornata'] == g].iterrows(): html += crea_card_html(r, camp, is_focus_mode=False)
        html += '</div></div>'

    html += f'<div class="footer-counter"><img src="{URL_COUNTER}"><br><span class="version-text">{APP_VERSION}</span></div></body></html>'
    with open(filename, "w", encoding="utf-8") as f: f.write(html)

def genera_segnapunti():
    html = f'<!DOCTYPE html><html lang="it"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Segnapunti</title>{SCOREBOARD_CODE}</head></html>'
    with open(FILE_SCORE, "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    df_ris, df_class = scrape_data()
    genera_landing_page()
    genera_pagina_app(df_ris, df_class, FILE_MALE, CAMPIONATI_MASCHILI)
    genera_pagina_app(df_ris, df_class, FILE_FEMALE, CAMPIONATI_FEMMINILI)
    genera_pagina_generale(df_ris, df_class, FILE_GEN_MALE, CAMPIONATI_MASCHILI, FILE_MALE)
    genera_pagina_generale(df_ris, df_class, FILE_GEN_FEMALE, CAMPIONATI_FEMMINILI, FILE_FEMALE)
    genera_segnapunti()
    print(f"✅ Generazione {APP_VERSION} completata!")

