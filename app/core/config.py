
import yaml
from pathlib import Path

class Settings:
    def __init__(self, config_path=Path(__file__).parents[2] / "config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    @property
    def ffvb_csv_url(self):
        return self.config["ffvb"]["csv_url"]

    @property
    def ffvb_address_url(self):
        return self.config["ffvb"]["address_pdf_url"]

    @property
    def club(self):
        return self.config["club"]["name"]

    @property
    def club_id(self):
        return self.config["club"]["id"]

    @property
    def entities(self):
        return self.config["championnat"]["entities"]

    @property
    def categories(self):
        return self.config["championnat"]["categories"]

    @property
    def labels(self):
        return self.config["championnat"]["labels"]


    def get_season_config(self, saison: str, code: str) -> dict:
        """
        Récupère la configuration d'une catégorie pour une saison donnée.
        Retourne un dict vide si non trouvée.
        """
        try:
            return self.config["saisons"][saison][code]
        except KeyError:
            return {}


settings = Settings()
