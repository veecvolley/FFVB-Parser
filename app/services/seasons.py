#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import html
import requests
import re
import unicodedata
from bs4 import BeautifulSoup

CODE_CLUB = "0775819"
SAISONS = ["2023/2024", "2024/2025", "2025/2026"]

BASE_URL = "https://www.ffvbbeach.org/ffvbapp/resu/planning_club_class.php"


def _norm(s: str) -> str:
    """Uppercase + suppression des accents + trim."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s.upper().strip()

def build_label(type_: str, genre: str, category: str, niveau: str = "") -> str:
    """
    Règles:
      - Senior + Volley-Ball: SM / SF / SX
      - Senior + Volley-Assis: SVA (genre ignoré, comme ton exemple)
      - Catégorie de type M## ou F## : M##G / M##F / M##X selon le genre
      - Senior + Beach-Volley: SMB / SFB / SXB (convention proposée)
      - Loisir: L + G/F/X (convention proposée)
      - Sinon: fallback = category (ou 'UNK')
    """
    t = _norm(type_)
    g = _norm(genre)
    c = _norm(category)
    # n = _norm(niveau)  # disponible si tu veux affiner selon le niveau

    # Normalisation genre -> suffixe
    gmap = {
        "M": "G", "MASC": "G", "MASCULIN": "G",
        "F": "F", "FEM": "F", "FEMININ": "F",
        "MIXTE": "X", "X": "X"
    }
    gsuf = gmap.get(g, "")

    # 1) Volley-Assis prioritaire (selon ton exemple: "SVA" pour senior)
    if t == "VOLLEY-ASSIS":
        if c == "SENIOR":
            return "SVA"
        # Jeunes en Volley-Assis (optionnel): M15VA + G/F/X si on veut marquer le genre
        m = re.fullmatch(r"[MF]?\d{1,2}", c)
        if m:
            return f"{c}VA{gsuf}" if gsuf else f"{c}VA"
        return "VA"

    # 2) Senior
    if c == "SENIOR":
        if t in ("BEACH-VOLLEY", "BEACH", "VOLLEY BEACH"):
            # Convention proposée pour le beach en senior
            if gsuf == "G": return "SMB"
            if gsuf == "F": return "SFB"
            return "SXB"
        # Volley-Ball (par défaut)
        if gsuf == "G": return "SM"
        if gsuf == "F": return "SF"
        return "SX"

    # 3) Jeunes (M## / F##)
    if re.fullmatch(r"[MF]?\d{1,2}", c):
        # ex: M15 + Masculin -> M15G ; M18 + Féminin -> M18F ; Mixte -> M18X
        return f"{c}{gsuf}" if gsuf else c

    # 4) Loisir (convention simple)
    if "LOISIR" in c:
        return f"L{gsuf}" if gsuf else "L"

    # 5) Par défaut
    return c or "UNK"

def normalize_season(s: str) -> str:
    return s.replace("/", "-")

def split_code_title(line: str):
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
    if "FÉM" in u:
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

import yaml
from pathlib import Path

def generate_config_seasons(code_club: str, saisons: list, output_file: str = "saisons.yaml"):
    data = {"saisons": {}}

    for saison in saisons:
        saison_key = normalize_season(saison)
        data["saisons"][saison_key] = {}

        try:
            lines = fetch_lines(code_club, saison)
        except Exception as e:
            data["saisons"][saison_key]["_error"] = f"{saison} fetch failed: {e}"
            continue

        for line in lines:
            code, title = split_code_title(line)
            u = line.upper()

            type_ = detect_type(u)
            gender = detect_gender(u)
            category = detect_category(u)
            level = detect_level(u)
            label = build_label(type_, gender, category)

            data["saisons"][saison_key][code] = {
                "titre": title,
                "type": type_,
                "genre": gender,
                "category": category,
                "niveau": level,
                "label": label,
            }

    output_path = Path(output_file)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, indent=2)
