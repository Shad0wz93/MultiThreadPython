import sys
import os
import threading
import time
import random
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from banque import Banque
from compte import Compte
from file_clients import FileClients, Client
from guichet import PoolGuichets
from historique import Historique
from surveillance import Notification

# ---------------------------------------------------------------------------
# US-09 : CONFIGURATION DES LOGS (Terminal + Fichier résultat)
# ---------------------------------------------------------------------------
# On utilise le module logging qui est thread-safe
log_file = "resultat_simulation.txt"

# Configuration du logger racine
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Supprimer les anciens handlers s'ils existent (évite les doublons lors des re-runs)
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Handler pour le fichier (UTF-8)
file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
file_handler.setFormatter(logging.Formatter('%(message)s'))
root_logger.addHandler(file_handler)

# Handler pour la console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(message)s'))
root_logger.addHandler(console_handler)

# Remplacement de la fonction print par logging.info pour tout rediriger
def print_log(*args, **kwargs):
    msg = " ".join(map(str, args))
    logging.info(msg)

# On écrase le print localement dans ce fichier, mais pour les autres modules,
# ils devront utiliser sys.stdout. Pour être sûr, on redirige sys.stdout.
class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w", encoding="utf-8")

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            logging.log(logging.INFO, line.rstrip())
    def flush(self):
        pass

sys.stdout = Logger(log_file)

# ---------------------------------------------------------------------------
# Configuration de la simulation
# ---------------------------------------------------------------------------
PRINT_LOGS = True 

print_log("\n" + "="*50)
print_log(" US-09 : SIMULATION DE CHARGE (STRESS TEST) ".center(50, "="))
print_log("="*50 + "\n")

# US-06 Compatibilité
notification = Notification()
banque = Banque(notification)

historique = Historique()
file_clients = FileClients(capacite_max=200, verbose=PRINT_LOGS) 

# 10 comptes à 1000 eu de base
comptes = [Compte(i, notification, 1000) for i in range(1, 11)]
for c in comptes:
    banque.ajouter_compte(c)

initial_total = sum(c.get_solde() for c in comptes)
print_log(f"[*] Configuration : 10 comptes")
print_log(f"[*] Solde total initial : {initial_total:.2f} EUR")

# Démarrage
pool_guichets = PoolGuichets(n_guichets=5, file_clients=file_clients, banque=banque, historique=historique, verbose=PRINT_LOGS)
pool_guichets.demarrer()

# Dashboard US-05
stop_dashboard = threading.Event()
def monitoring():
    while not stop_dashboard.is_set():
        current = sum(c.get_solde() for c in comptes)
        print_log(f"\n  >>> [Dashboard] File: {file_clients.taille_file()} | Total Banque: {current:.2f} EUR\n")
        time.sleep(2)

monitor_thread = threading.Thread(target=monitoring, daemon=True)
monitor_thread.start()

# Tâche Client
def tache_client(id_client):
    """Effectue entre 1 et 10 opérations aléatoires (Critère US-09)"""
    nb_ops = random.randint(1, 10)
    ops_ok = 0
    for _ in range(nb_ops):
        c_src = random.choice(comptes)
        c_dest = random.choice([c for c in comptes if c.numero != c_src.numero])
        montant = random.randint(1, 10)
        
        
        client = Client(f"C-{id_client:02d}", operation="virement", montant=montant, compte=c_src, compte_destination=c_dest)
        
        if file_clients.rejoindre_file(client, block=True):
            ops_ok += 1
    return ops_ok

# Exécution US-09
nb_clients = 60
start_time = time.time()

print_log(f"[*] Simulation en cours : {nb_clients} clients simultanés...")
print_log(f"[*] Les logs sont sauvegardés dans '{log_file}'\n")

total_charge = 0
with ThreadPoolExecutor(max_workers=nb_clients) as pool:
    futures = [pool.submit(tache_client, i) for i in range(nb_clients)]
    for f in as_completed(futures):
        total_charge += f.result()

while not file_clients.file_est_vide():
    time.sleep(0.5)

time.sleep(1)
stop_dashboard.set()
pool_guichets.arreter()

end_time = time.time()
duree = end_time - start_time

# Bilan
final_total = sum(c.get_solde() for c in comptes)
ecart = abs(initial_total - final_total)

print_log("\n" + "="*50)
print_log(" BILAN FINAL US-09 ".center(50, "="))
print_log("="*50)
print_log(f"  Opérations totales : {total_charge}")
print_log(f"  Temps d'exécution  : {duree:.2f} secondes")
print_log(f"  Débit moyen        : {total_charge / duree:.2f} ops/sec")
print_log("-" * 50)
print_log(f"  Solde Initial      : {initial_total:,.2f} EUR")
print_log(f"  Solde Final        : {final_total:,.2f} EUR")
print_log(f"  Écart (Invariant)  : {ecart:,.2f} EUR")

if ecart < 0.01:
    print_log("\n✓ L'invariant de solde est respecté.")
    print_log("✓ US-09 validée avec succès ✓")
else:
    print_log(f"\n❌ ERREUR : Écart de {ecart} EUR détecté !")

print_log("="*50 + "\n")
