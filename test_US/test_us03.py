import time
import random

from compte import Compte
from file_clients import Client, FileClients
from guichet import PoolGuichets

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

N_GUICHETS = 3
N_CLIENTS = 8
SOLDE_INITIAL = 500.0

# ---------------------------------------------------------------------------
# TEST
# ---------------------------------------------------------------------------

def creer_client(nom, operation, compte, montant):
    """
    Création d'un compte client avec les attributs nécessaires
    """
    c = Client(nom)
    c.operation = operation
    c.compte = compte
    c.montant = montant
    return c

# ---------------------------------------------------------------------------
# Démo principale
# ---------------------------------------------------------------------------


print("=" * 10)
print("  BankThread — Démo US-03")
print("=" * 10)
print(f"  Guichets : {N_GUICHETS}  |  Clients : {N_CLIENTS + 1} (dont 1 cassé)")

# Comptes partagés
# Évite que 3 guichets travaillent sur les mêmes comptes en même temps
comptes = [Compte(f"CPT-{i}", SOLDE_INITIAL) for i in range(3)]

# File de clients (US-02 — ici stub)
file = FileClients(capacite_max=N_CLIENTS + 1)  # +1 pour le client cassé

# Pool de guichets — critère [1] : N configurable
pool = PoolGuichets(n_guichets=N_GUICHETS, file_clients=file)
pool.demarrer()

# Clients normaux
for i in range (N_CLIENTS):
    c = creer_client(
        nom = f"Client-{i + 1:02d}", # Client-01, Client_02, ...
        operation = random.choice(["depot", "retrait", "inconnu"]),
        compte = random.choice(comptes),
        montant = random.randint(10, 200),
    )
    file.rejoindre_file(c)
    time.sleep(0.10)

# Client cassé (isolation des erreurs)
file.rejoindre_file(creer_client("Client-erreur", "depot", None, 100))

# Attente que tous les clients soient servis
while not file.file_est_vide():
    time.sleep(0.10)

pool.arreter()

print(f"Solde final par compte :")
for c in comptes:
    print(f" {c.numero} a pour solde {c.get_solde()}€")

print(f"Demo terminée.")