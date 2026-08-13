from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

_TIMEOUT = 15  # secondes


class FileServerError(RuntimeError):
    pass


class NormalizedLogsClient:
    def __init__(self, base_url: str, api_key: str, verify_tls: bool = True):
        self.base_url = base_url.rstrip("/")
        self._headers = {"X-API-Key": api_key}
        self._verify_tls = verify_tls

    def list_files(self, source: str) -> list[dict]:
        resp = requests.get(
            f"{self.base_url}/files/{source}",
            headers=self._headers,
            timeout=_TIMEOUT,
            verify=self._verify_tls,
        )
        if resp.status_code == 401:
            raise FileServerError("Clé API rejetée par le serveur de fichiers.")
        resp.raise_for_status()
        return resp.json()["files"]

    def fetch_latest(self, source: str) -> dict | None:
        files = self.list_files(source)
        if not files:
            logger.info("Aucun fichier normalisé disponible pour la source %s.", source)
            return None

        filename = files[0]["name"]  # déjà trié du plus récent au plus ancien
        resp = requests.get(
            f"{self.base_url}/files/{source}/{filename}",
            headers=self._headers,
            timeout=_TIMEOUT,
            verify=self._verify_tls,
        )
        if resp.status_code == 401:
            raise FileServerError("Clé API rejetée par le serveur de fichiers.")
        resp.raise_for_status()
        return resp.json()
