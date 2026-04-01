import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from compte import Compte
from banque import Banque
from file_clients import FileClients, Client
from guichet import PoolGuichets
from dab import DAB
from historique import Historique
from surveillance import Notification, TableauDeBord

N_CLIENTS        = 50
N_COMPTES        = 10
N_GUICHETS       = 5
N_DAB            = 3
SOLDE_INIT       = 1000
CAPACITE_FILE    = 30
INTERVALLE_TABLO = 3

notification = Notification()

comptes = {i: Compte(i, notification, solde_initial=SOLDE_INIT)
           for i in range(N_COMPTES)}

banque = Banque(notification)
for c in comptes.values():
    banque.ajouter_compte(c)

file_clients  = FileClients(capacite_max=CAPACITE_FILE)
dab           = DAB(nb_dab=N_DAB)
historique    = Historique()
pool_guichets = PoolGuichets(n_guichets=N_GUICHETS, file_clients=file_clients, banque=banque)
tableau       = TableauDeBord(file_clients, pool_guichets, comptes, intervalle=INTERVALLE_TABLO)

nb_operations   = 0
lock_operations = threading.Lock()

def simuler_client(client_id: int):
    global nb_operations
    nom    = f"Client-{client_id:02d}"
    nb_ops = random.randint(1, 10)

    for _ in range(nb_ops):
        operation = random.choice(["depot", "retrait", "virement"])
        compte    = random.choice(list(comptes.values()))
        montant   = random.randint(10, 200)

        destination = None
        if operation == "virement":
            destination = random.choice(list(comptes.values()))
            if destination.numero == compte.numero:
                continue

        client = Client(
            nom=nom,
            operation=operation,
            montant=montant,
            compte=compte,
            compte_destination=destination
        )

        file_clients.rejoindre_file(client)
        with lock_operations:
            nb_operations += 1
        time.sleep(random.uniform(0.05, 0.2))

    return nb_ops

def lancer_surveillance_decouvert():
    t = threading.Thread(
        target=notification.surveiller,
        daemon=True,
        name="Surveillance-Découvert"
    )
    t.start()
    return t

def main():
    print("\n" + "=" * 50)
    print("   BankThread — Simulation de charge (US-09)")
    print("=" * 50)
    print(f"  Clients   : {N_CLIENTS}")
    print(f"  Comptes   : {N_COMPTES}")
    print(f"  Guichets  : {N_GUICHETS}")
    print(f"  DAB       : {N_DAB}")
    print("=" * 50 + "\n")

    solde_initial_total = sum(c.get_solde() for c in comptes.values())
    print(f"  Solde total initial : {solde_initial_total}€\n")

    # Démarrage des composants
    lancer_surveillance_decouvert()
    pool_guichets.demarrer()
    tableau.start()

    # Simulation
    print("  Simulation en cours...\n")
    debut = time.time()
    with ThreadPoolExecutor(max_workers=N_CLIENTS) as pool:
        futures = [pool.submit(simuler_client, i) for i in range(N_CLIENTS)]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"  [Erreur] {e}")

    duree = time.time() - debut

    # Arrêt propre
    pool_guichets.arreter()
    tableau.arreter()
    tableau.join()

    # Résultats finaux
    solde_final_total = sum(c.get_solde() for c in comptes.values())
    debit = nb_operations / duree if duree > 0 else 0

    print("\n" + "=" * 50)
    print("   Résultats")
    print("=" * 50)
    print(f"  Opérations : {nb_operations}")
    print(f"  Durée      : {duree:.2f}s")
    print(f"  Débit      : {debit:.1f} ops/seconde")
    print(f"  Solde initial : {solde_initial_total}€")
    print(f"  Solde final   : {solde_final_total}€")
    print("-" * 50)

    if solde_final_total == solde_initial_total:
        print("  OK — Invariant respecte, aucune race condition")
    else:
        diff = solde_final_total - solde_initial_total
        print(f"  ERREUR — Ecart de {diff}€ detecte (race condition !)")

    print("=" * 50 + "\n")

if __name__ == "__main__":
    main()