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
NOME_SQUADRA_TARGET = "TODIS PASTENA VOLLEY"
FILE_HTML_OUTPUT = "index.html" # IMPORTANTE: index.html per GitHub Pages

# URL LOGO (Link RAW diretto all'immagine)
URL_LOGO = "https://raw.githubusercontent.com/robertobrigantino-blip/todis-volley/main/logo.jpg"

# ELENCO CAMPIONATI
CAMPIONATI = {
    "Serie C  Femminile Gir.A": "85471",
    "Under 18 Femminile Gir.B": "86850",
    "Under 16 Femminile Gir.A": "86853",
    "Under 14 Femminile Gir.C": "86860",
}

# ================= CSS STILE APP =================
CSS_STYLE = """
<style>
    body { font-family: 'Roboto', sans-serif; background-color: #f0f2f5; margin: 0; padding: 0; color: #333; padding-bottom: 60px; }
    
    .app-header { background-color: #d32f2f; color: white; padding: 12px 15px; display: flex; align-items: center; justify-content: center; gap: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .app-header img { height: 42px; width: 42px; border-radius: 50%; border: 2px solid white; object-fit: cover; }
    .app-header div { text-align: left; }
    .app-header h1 { margin: 0; font-size: 16px; text-transform: uppercase; line-height: 1.2; font-weight: 700; }
    .last-update { font-size: 11px; opacity: 0.9; }

    .tab-bar { background-color: white; display: flex; overflow-x: auto; white-space: nowrap; position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-bottom: 1px solid #eee; }
    .tab-btn { flex: 1; padding: 12px 15px; text-align: center; background: none; border: none; font-size: 13px; font-weight: 500; color: #666; border-bottom: 3px solid transparent; cursor: pointer; min-width: 100px; }
    .tab-btn.active { color: #d32f2f; border-bottom: 3px solid #d32f2f; font-weight: bold; }

    .tab-content { display: none; padding: 15px; max-width: 600px; margin: 0 auto; animation: fadeIn 0.3s; }
    .tab-content.active { display: block; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

    h2 { color: #d32f2f; font-size: 16px; border-left: 4px solid #d32f2f; padding-left: 8px; margin-top: 10px; margin-bottom: 12px; }
    h3 { font-size: 14px; background: #eee; padding: 5px 10px; border-radius: 4px; margin-top: 15px; margin-bottom: 10px; color: #555; }

    .table-card { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; width: 100%; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; white-space: nowrap; }
    th { background-color: #ffebee; color: #c62828; padding: 8px 5px; text-align: center; font-weight: bold; font-size: 11px; text-transform: uppercase; }
    td { padding: 8px 5px; text-align: center; border-bottom: 1px solid #f0f0f0; }
    td:nth-child(2) { text-align: left; min-width: 130px; font-weight: 500; position: sticky; left: 0; background-color: white; border-right: 1px solid #eee; }
    .my-team-row td { background-color: #fff3e0 !important; font-weight: bold; }

    .match-card { background: white; border-radius: 8px; padding: 12px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid #ddd; position: relative; overflow: hidden; }
    .match-card.win { border-left-color: #2e7d32; } 
    .match-card.loss { border-left-color: #c62828; } 
    .match-card.upcoming { border-left-color: #ff9800; } 

    .result-badge { position: absolute; top: 0; right: 0; font-size: 10px; padding: 4px 8px; border-bottom-left-radius: 8px; font-weight: bold; color: white; z-index: 10; }
    .badge-win { background-color: #2e7d32; }
    .badge-loss { background-color: #c62828; }

    .match-header { display: flex; align-items: center; justify-content: flex-start; gap: 10px; font-size: 12px; color: #555; margin-bottom: 12px; border-bottom: 1px solid #f5f5f5; padding-bottom: 5px; padding-right: 50px; }
    .date-badge { font-weight: bold; color: #d32f2f; display: flex; align-items: center; gap: 5px; }
    .separator { color: #ccc; }

    .teams { display: flex; flex-direction: column; gap: 6px; font-size: 14px; margin-bottom: 8px; }
    .team-row { display: flex; justify-content: space-between; align-items: center; }
    .my-team-text { color: #d32f2f; font-weight: 700; }
    .team-score { font-weight: bold; background: #eee; padding: 2px 8px; border-radius: 4px; min-width: 20px; text-align: center; }
    
    .match-footer { margin-top: 10px; padding-top: 10px; border-top: 1px solid #f5f5f5; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; }
    .gym-name { font-size: 11px; color: #666; width: 100%; margin-bottom: 5px; display: block; }
    
    .action-buttons { display: flex; gap: 8px; width: 100%; justify-content: flex-end; }
    .btn { text-decoration: none; padding: 6px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; display: flex; align-items: center; gap: 4px; flex-grow: 1; justify-content: center; max-width: 100px; }
    .btn-map { background-color: #E3F2FD; color: #1565C0; }
    .btn-cal { background-color: #F3E5F5; color: #7B1FA2; } 
    .btn-wa { background-color: #E8F5E9; color: #2E7D32; } 

    .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 2000; display: none; align-items: center; justify-content: center; backdrop-filter: blur(2px); }
    .modal-content { background: white; width: 90%; max-width: 400px; max-height: 80vh; border-radius: 12px; padding: 20px; overflow-y: auto; position: relative; box-shadow: 0 10px 25px rgba(0,0,0,0.2); animation: slideUp 0.3s; }
    @keyframes slideUp { from { transform: translateY(50px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    .modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px; }
    .modal-title { font-size: 18px; font-weight: bold; color: #d32f2f; }
    .close-btn { background: #eee; border: none; font-size: 20px; padding: 5px 10px; border-radius: 50%; }
    .modal-content .match-card { border: 1px solid #eee; box-shadow: none; padding: 10px; margin-bottom: 8px; }
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

    document.addEventListener("DOMContentLoaded", function() {
        const today = new Date();
        today.setHours(0,0,0,0);
        let nextMatches = {};
        const allMatches = document.querySelectorAll('.match-card.upcoming');
        
        allMatches.forEach(card => {
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
        });

        let popupHTML = "";
        let count = 0;
        for (const [camp, data] of Object.entries(nextMatches)) {
            popupHTML += `<h3>🏆 ${camp}</h3>`;
            popupHTML += data.html;
            count++;
        }
        if (count > 0) {
            document.getElementById('modal-body').innerHTML = popupHTML;
            document.getElementById('modal-overlay').style.display = 'flex';
        }
    });
    function closeModal() { document.getElementById('modal-overlay').style.display = 'none'; }
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
        except:
            dates = f"{row['DataISO'].replace('-','')}T120000/{row['DataISO'].replace('-','')}T140000"
    else:
        date_clean = row['DataISO'].replace('-', '')
        dates = f"{date_clean}/{date_clean}"

    return f"https://www.google.com/calendar/render?action=TEMPLATE&text={title}&dates={dates}&location={location}&details=Campionato+{quote(row['Campionato'])}"

def create_whatsapp_link(row):
    if row['Punteggio']:
        text = f"🏐 *Risultato {row['Campionato']}*\n{row['Squadra Casa']} {row['Set Casa']} - {row['Set Ospite']} {row['Squadra Ospite']}\nForza Todis! 💪"
    else:
        text = f"📅 *Prossima Gara {row['Campionato']}*\n{row['Data']}\n📍 {row['Impianto']}\n{row['Squadra Casa']} vs {row['Squadra Ospite']}"
    return f"https://wa.me/?text={quote(text)}"

# ================= SCRAPING =================
def get_match_details_robust(driver, match_url):
    data_ora_full, data_iso, luogo, link_maps = "Data da definire", "", "Impianto non definito", ""
    try:
        driver.get(match_url)
        time.sleep(0.5)
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
            # --- FIX SYNTAX ERROR GITHUB ---
            clean_gym_name = re.sub(r'\s+', ' ', luogo).strip()
            link_maps = f"https://www.google.com/maps/search/?api=1&query={quote(clean_gym_name)}"
    except: pass
    return data_ora_full, data_iso, luogo, link_maps

def scrape_data():
    print("🚀 Avvio scraping...")
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox") # Utile per Github Actions
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    
    driver = webdriver.Chrome(options=chrome_options)
    all_results, all_standings = [], []

    for nome_camp, id_camp in CAMPIONATI.items():
        print(f"   Analisi: {nome_camp}...")
        base_url = "https://www.fipavsalerno.it/mobile/"
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

                    if NOME_SQUADRA_TARGET.lower() in c.lower() or NOME_SQUADRA_TARGET.lower() in o.lower():
                        full_url = urljoin(base_url, el.get('href', ''))
                        print(f"      📍 {c} vs {o}...")
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

# ================= HTML GENERATION =================
def genera_html(df_ris, df_class):
    print("📱 Creazione HTML...")
    
    html_content = f"""<!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="theme-color" content="#d32f2f">
        <meta name="apple-mobile-web-app-title" content="Todis Volley">
        <meta name="application-name" content="Todis Volley">
        <link rel="icon" type="image/png" href="{URL_LOGO}">
        <link rel="apple-touch-icon" href="{URL_LOGO}">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <title>{NOME_SQUADRA_TARGET}</title>
        {CSS_STYLE}
    </head>
    <body>
        <div id="modal-overlay" class="modal-overlay" onclick="closeModal()">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="modal-header"><div class="modal-title">📅 Prossimi Appuntamenti</div><button class="close-btn" onclick="closeModal()">×</button></div>
                <div id="modal-body"></div>
                <div style="text-align:center; margin-top:15px;"><button onclick="closeModal()" style="background:#d32f2f; color:white; border:none; padding:8px 20px; border-radius:20px;">Chiudi</button></div>
            </div>
        </div>

        <div class="app-header">
            <img src="{URL_LOGO}" alt="Logo">
            <div><h1>{NOME_SQUADRA_TARGET}</h1><div class="last-update">Aggiornato: {time.strftime("%d/%m/%Y %H:%M")}</div></div>
        </div>
    """

    campionati_attivi = []
    if not df_class.empty:
        mask = df_class['Squadra'].str.contains(NOME_SQUADRA_TARGET, case=False, na=False)
        campionati_attivi = df_class[mask]['Campionato'].unique()

    if not campionati_attivi.any():
        html_content += "<p style='text-align:center; padding:20px'>Nessun dato.</p></body></html>"
        with open(FILE_HTML_OUTPUT, "w", encoding="utf-8") as f: f.write(html_content)
        return

    html_content += '<div class="tab-bar">'
    for i, camp in enumerate(campionati_attivi):
        p = camp.split()
        n = f"{p[0]} {p[1]}" if len(p) > 1 else camp
        if "Gir." in camp: n += " " + camp.split("Gir.")[1].strip()
        html_content += f'<button id="btn-{i}" class="tab-btn {"active" if i==0 else ""}" onclick="openTab({i})">{n}</button>'
    html_content += '</div>'

    for i, camp in enumerate(campionati_attivi):
        html_content += f'<div id="content-{i}" class="tab-content {"active" if i==0 else ""}">'
        
        # CLASSIFICA
        html_content += f"<h2>🏆 Classifica</h2>"
        df_c = df_class[df_class['Campionato'] == camp].sort_values(by='P.')
        html_content += """<div class="table-card"><div class="table-scroll"><table><thead><tr><th>Pos</th><th>Squadra</th><th>Pt</th><th>G</th><th>V</th><th>P</th><th>SF</th><th>SS</th></tr></thead><tbody>"""
        for _, r in df_c.iterrows():
            cls = 'class="my-team-row"' if NOME_SQUADRA_TARGET.upper() in str(r['Squadra']).upper() else ''
            html_content += f"<tr {cls}><td>{r.get('P.','-')}</td><td>{r.get('Squadra','?')}</td><td><b>{r.get('Pu.',0)}</b></td><td>{r.get('G.G.',0)}</td><td>{r.get('G.V.',0)}</td><td>{r.get('G.P.',0)}</td><td>{r.get('S.F.',0)}</td><td>{r.get('S.S.',0)}</td></tr>"
        html_content += '</tbody></table></div></div>'

        # PARTITE
        html_content += f"<h2>📅 Calendario</h2>"
        df_r = df_ris[df_ris['Campionato'] == camp]
        
        if df_r.empty: html_content += "<p>Nessuna partita.</p>"
        else:
            for _, r in df_r.iterrows():
                is_home = NOME_SQUADRA_TARGET.upper() in r['Squadra Casa'].upper()
                cs = 'class="team-name my-team-text"' if is_home else 'class="team-name"'
                os = 'class="team-name my-team-text"' if not is_home else 'class="team-name"'
                
                status_class = "upcoming"
                badge_html = ""
                
                if r['Punteggio']:
                    try:
                        sc, so = int(r['Set Casa']), int(r['Set Ospite'])
                        if (is_home and sc > so) or (not is_home and so > sc):
                            status_class = "win"
                            badge_html = '<span class="result-badge badge-win">VINTA</span>'
                        else:
                            status_class = "loss"
                            badge_html = '<span class="result-badge badge-loss">PERSA</span>'
                    except: status_class = "played"
                
                lnk_wa = create_whatsapp_link(r)
                lnk_cal = create_google_calendar_link(r) if not r['Punteggio'] else ""
                lnk_map = r['Maps']
                
                btns_html = ""
                if lnk_map: btns_html += f'<a href="{lnk_map}" target="_blank" class="btn btn-map">📍 Mappa</a>'
                if lnk_cal: btns_html += f'<a href="{lnk_cal}" target="_blank" class="btn btn-cal">📅 Salva</a>'
                if lnk_wa: btns_html += f'<a href="{lnk_wa}" target="_blank" class="btn btn-wa">💬 Invia</a>'

                html_content += f"""
                <div class="match-card {status_class}" data-date-iso="{r['DataISO']}" data-camp="{camp}">
                    {badge_html}
                    <div class="match-header">
                        <span class="date-badge">📅 {r['Data']}</span>
                        <span class="separator">|</span>
                        <span>{r['Giornata']}</span>
                    </div>
                    <div class="teams">
                        <div class="team-row"><span {cs}>{r['Squadra Casa']}</span><span class="team-score">{r['Set Casa']}</span></div>
                        <div class="team-row"><span {os}>{r['Squadra Ospite']}</span><span class="team-score">{r['Set Ospite']}</span></div>
                    </div>
                    <div class="match-footer"><span class="gym-name">🏟️ {r['Impianto']}</span><div class="action-buttons">{btns_html}</div></div>
                </div>
                """
        html_content += '</div>'

    html_content += "</body></html>"
    with open(FILE_HTML_OUTPUT, "w", encoding="utf-8") as f: f.write(html_content)
    print(f"✅ FILE CREATO: {FILE_HTML_OUTPUT}")

if __name__ == "__main__":
    df_ris, df_class = scrape_data()

    genera_html(df_ris, df_class)

