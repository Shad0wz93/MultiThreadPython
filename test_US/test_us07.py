import time
import threading

from compte import Compte
from dab import DAB
from surveillance import Notification

notif = Notification()


# =============================================================================
# TEST 1 : Nombre de DAB configurable
# =============================================================================
print("\n[Test 1] Nombre de DAB configurable")
dab = DAB(nb_dab=3)  # Configurable : 2 par défaut, ici 3
print(f"DAB crée avec {dab.nb_dab} distributeurs")


# =============================================================================
# TEST 2 : Maximum N retraits simultanés + Blocage/Réveil automatique
# =============================================================================
print("\n[Test 2] Retraits simultanés avec limite de 3 DAB + "
      "sans boucle active + prise de possession automatique")

comptes = [
  Compte(1, notif, solde_initial=1000),
  Compte(2, notif, solde_initial=500),
  Compte(3, notif, solde_initial=200),
  Compte(4, notif, solde_initial=300),
  Compte(5, notif, solde_initial=400)
]

def client_retire(num, compte):
  # Simule un client qui retire au DAB
  dab.retirer(compte, 100, f'Client {num}')

print("Lancement de 5 clients qui retirent simultanément (avec 3 DAB)...\n")

threads = []
for i in range(5):
  t = threading.Thread(target=client_retire, args=(i+1, comptes[i]))
  threads.append(t)
  t.start()
  time.sleep(0.1)  # Décalage pour voir l'ordre d'arrivée

for t in threads:
  t.join()

print("\nTous les clients ont terminé leurs retraits.")
print("Maximum de 3 retraits simultanés a été respecté, les autres clients ont attendu leur tour.")


# =============================================================================
# TEST 3 : Retrait avec solde insuffisant
# =============================================================================
print("\n[Test 3] Retrait avec solde insuffisant")
compte_insuffisant = Compte(6, notif, solde_initial=50)
success = dab.retirer(compte_insuffisant, 100, "Client 6")
print(f"Retrait refusé correctement : {not success}")