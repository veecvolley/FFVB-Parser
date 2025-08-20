#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import html
import requests
from bs4 import BeautifulSoup

CODE_CLUB = "0775819"
SAISONS = ["2023/2024", "2024/2025", "2025/2026"]

BASE_URL = "https://www.ffvbbeach.org/ffvbapp/resu/planning_club_class.php"

def normalize_season(s: str) -> str:
    return s.replace("/", "-")

def split_code_label(line: str):
    if " - " in line:
        code, label = line.split(" - ", 1)
        return code.strip(), label.strip()
    return line.strip(), ""

def detect_type(u: str) -> str:
    if "BEACH" in u:
        return "Beach-Volley"
    if "ASSIS" in u:
        return "Volley-Assis"
    return "Volley-Ball"

def detect_gender(u: str) -> str:
    if "MASC" in u:
        return "Masculin"
    if "FEM" in u:
        return "Féminin"
    return "Mixte"

def detect_category(u: str) -> str:
    if "SENIOR" in u:
        return "Sénior"
    for cat in ("M11", "M13", "M15", "M18", "M21"):
        if cat in u:
            return cat
    if "LOISIR" in u:
        return "Loisir"
    return "Sénior"

def detect_level(u: str) -> str:
    if "CHAMPIONNAT DE FRANCE" in u:
        return "Championnat de France"
    if "COUPE DE FRANCE" in u:
        return "Coupe de France"
    if "REG" in u:
        return "Championnat Régional"
    if "DEP" in u:
        return "Championnat Départemental"
    if "LIB" in u:
        return "Championnat Loisir Compet'Lib"
    return "Championnat Départemental"

def fetch_lines(code_club: str, saison: str):
    params = {"cnclub": code_club, "saison": saison}
    r = requests.get(BASE_URL, params=params, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    cells = soup.select("td.titrepoule")

    lines = []
    for td in cells:
        txt = td.get_text(" ", strip=True)
        txt = html.unescape(txt)
        if " - " in txt:
            lines.append(txt)

    return lines

def main():
    print("saisons:")
    for saison in SAISONS:
        saison_key = normalize_season(saison)
        print(f"  {saison_key}:")
        try:
            lines = fetch_lines(CODE_CLUB, saison)
        except Exception as e:
            print(f"    _error: \"{saison} fetch failed: {e}\"")
            continue

        for line in lines:
            code, label = split_code_label(line)
            u = line.upper()

            type_ = detect_type(u)
            gender = detect_gender(u)
            category = detect_category(u)
            level = detect_level(u)

            # Écriture YAML
            print(f"    {code}:")
            print(f"      titre: \"{label}\"")
            print(f"      type: \"{type_}\"")
            print(f"      genre: \"{gender}\"")
            print(f"      category: \"{category}\"")
            print(f"      niveau: \"{level}\"")

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        CODE_CLUB = sys.argv[1]
    if len(sys.argv) >= 3:
        SAISONS[:] = sys.argv[2:]
    main()
