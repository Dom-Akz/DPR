"""
Commande Django : récupère les logs normalisés depuis l'API de la VM,
calcule les indicateurs KPI/KRI de niveau N0 et les enregistre en base.

Usage :
    python manage.py collect_indicators
    python manage.py collect_indicators --source firewall

Variables d'environnement requises (.env, comme le reste du projet) :
    VM_FILE_SERVER_BASE_URL   ex. https://kpikri-collecte.onee.interne
    VM_FILE_SERVER_API_KEY    clé API en clair fournie par la VM
    VM_FILE_SERVER_VERIFY_TLS true/false (true par défaut)

Déploiement recommandé : planifier via cron/systemd timer, comme
run_normalize.py côté VM (voir deploiement_vm.md).
"""
import os

from django.core.management.base import BaseCommand, CommandError

from dashboard.engine.client import NormalizedLogsClient
from dashboard.engine.collector import SOURCES, collect_all


class Command(BaseCommand):
    help = "Collecte les indicateurs KPI/KRI de niveau N0 depuis l'API de la VM."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=SOURCES,
            help="Ne traiter qu'une seule source (par défaut : toutes).",
        )

    def handle(self, *args, **options):
        base_url = os.environ.get("VM_FILE_SERVER_BASE_URL")
        api_key = os.environ.get("VM_FILE_SERVER_API_KEY")
        verify_tls = os.environ.get("VM_FILE_SERVER_VERIFY_TLS", "true").lower() == "true"

        if not base_url or not api_key:
            raise CommandError(
                "VM_FILE_SERVER_BASE_URL et VM_FILE_SERVER_API_KEY doivent être "
                "définis (.env)."
            )

        client = NormalizedLogsClient(
            base_url=base_url, api_key=api_key, verify_tls=verify_tls
        )

        sources = [options["source"]] if options["source"] else None
        total = collect_all(client, sources)

        self.stdout.write(
            self.style.SUCCESS(f"{total} mesure(s) d'indicateur enregistrée(s).")
        )
