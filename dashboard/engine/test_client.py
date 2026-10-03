"""
Test d'appel de l'API du serveur de fichiers DEPUIS LE POSTE DASHBOARD
(ou votre machine locale), en utilisant client.py tel quel.

Prérequis : le serveur de fichiers doit tourner (localement en test via
`uvicorn server.file_server:app --host 127.0.0.1 --port 8001`, ou sur la
VM via https://kpikri-collecte.onee.interne en prod).

Usage :
    python3 test_client.py --base-url http://127.0.0.1:8001 --api-key <clé>
"""

from __future__ import annotations

import argparse
import json

from client import FileServerError, NormalizedLogsClient

SOURCES = ["firewall", "edr", "passerelle_mail", "vpn", "mfa", "waf", "pam"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="ex: http://127.0.0.1:8001 ou https://kpikri-collecte.onee.interne")
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--sources", nargs="*", default=SOURCES)
    parser.add_argument("--no-verify-tls", action="store_true", help="désactive la vérif TLS (jamais en prod, utile si certif interne non installé sur le poste de test)")
    args = parser.parse_args()

    client = NormalizedLogsClient(
        base_url=args.base_url,
        api_key=args.api_key,
        verify_tls=not args.no_verify_tls,
    )

    for source in args.sources:
        print(f"\n=== {source} ===")
        try:
            files = client.list_files(source)
            print(f"  Fichiers disponibles : {[f['name'] for f in files]}")

            payload = client.fetch_latest(source)
            if payload is None:
                print("  Aucun fichier -> rien à récupérer.")
                continue
            print(f"  Dernier fichier récupéré : {len(payload['records'])} enregistrements")
            print(f"  Exemple : {json.dumps(payload['records'][0], ensure_ascii=False)}")
        except FileServerError as exc:
            print(f"  [AUTH] {exc}")
        except Exception as exc:
            print(f"  [ERREUR RÉSEAU] {exc}")


if __name__ == "__main__":
    main()
