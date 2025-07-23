# curl -X POST 'https://www.ffvbbeach.org/ffvbapp/resu/vbspo_calendrier_export_club.php'   -H 'Content-Type: application/x-www-form-urlencoded'   -d 'cnclub=0775819&cal_saison=2024/2025&typ_edition=E&type=RES' > export20242025.csv
# iconv -f latin1 -t utf-8 export20242025.csv > export20242025_utf8.csv

curl -X POST 'https://www.ffvbbeach.org/ffvbapp/resu/vbspo_calendrier_export_club.php'   -H 'Content-Type: application/x-www-form-urlencoded'   -d 'cnclub=0775819&cal_saison=2025/2026&typ_edition=E&type=RES' > export20252026.csv
iconv -f latin1 -t utf-8 export20252026.csv > export20252026_utf8.csv