import threading
import time
from queue import Queue
from random import random

from compte import Compte
from guichet import Guichet, PoolGuichets

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

N_GUICHETS = 3
N_CLIENTS = 8
SOLDE_INITIAL = 500.0

# ---------------------------------------------------------------------------
# TEST
# ---------------------------------------------------------------------------

def creer_clients(comptes: list[Compte], n: int) -> list[Compte]:
    """
    Génère une liste de clients avec des opérations aléatoires
    """
    operations = ["depot", "retrait"]
    clients = []
    for i in range(n):
        op = random.choice(operations)
        clients.append({
            "nom": f"Client-{i + 1:02d}",
            "operation": op,
            "compte": random.choice(comptes),
            "montant": random.randint(10, 200),
        })

        # Ajout d'un client "cassé" pour tester l'isolation des erreurs
        clients.insert(5, {
            "nom": "Client-ERREUR",
            "operation": "depot",
            "compte": None,
            "montant": 100,
        })

        return clients

# ---------------------------------------------------------------------------
# Démo principale
# ---------------------------------------------------------------------------

def main():
    print("=" * 10)
    print("  BankThread — Démo US-03")
    print("=" * 10)
    print(f"  Guichets : {N_GUICHETS}  |  Clients : {N_CLIENTS + 1} (dont 1 cassé)")

    # Comptes partagés
    # Évite que 3 guichets travaillent sur les mêmes comptes en même temps
    comptes = [Compte(f"CPT-{i}", SOLDE_INITIAL) for i in range(3)]
    solde_initial_total = sum(c.get_solde() for c in comptes)

    # File de clients (US-02 — ici stub)
    file = FileClients(maxsize=N_CLIENTS + 1)  # +1 pour le client cassé