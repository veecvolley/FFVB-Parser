
import requests
import csv
import io
import pdfplumber
import re
from app.core.config import settings

def get_gymnase_address(codmatch, codent):
    url = settings.ffvb_address_url
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'codmatch': codmatch, 'codent': codent}
    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200 or response.headers.get('Content-Type') != 'application/pdf':
        print("Erreur lors du téléchargement du PDF.")
        return None

    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        text = ''
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + '\n'

        match = re.search(r'Salle\s*\n(.*?)(Sol\s*:|Arbitre\.s|$)', text, re.DOTALL)
        if match:
            salle_block = match.group(1)
            lines = [line.strip() for line in salle_block.split('\n') if line.strip()]
            if lines:
                nom = lines[0]
                adresse = ' '.join(lines[1:])
                match_adr = re.search(r"(.+)\s(\d{5})\s(.+)", adresse)
                if match_adr:
                    rue = match_adr.group(1).strip().lower()
                    code_postal = match_adr.group(2)
                    ville = match_adr.group(3).strip()
                    return {'nom': nom, 'rue': rue, 'code_postal': code_postal, 'ville': ville}
    return None

def parse_csv_rows():
    url = settings.ffvb_csv_url
    payload = {
        "cnclub": settings.club_id,
        "cal_saison": settings.saison,
        "typ_edition": "E",
        "type": "RES"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post(url, data=payload, headers=headers)
    r.raise_for_status()
    csv_latin1_bytes = r.content
    csv_utf8_str = csv_latin1_bytes.decode('latin1').encode('utf-8').decode('utf-8')
    csvfile = io.StringIO(csv_utf8_str)
    return csv.reader(csvfile, delimiter=";", quotechar='"')

def parse_local_csv_rows():
    with open("export20242025_utf8.csv", newline="", encoding="utf-8") as csvfile:
        return csv.reader(csvfile, delimiter=";", quotechar='"')
