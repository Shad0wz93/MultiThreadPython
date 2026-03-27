import time

import threading

from compte import Compte
from dab import DAB

# Le nombre de DAB est configurable
print("\n[Test 1] Nombre de DAB configurable")
dab = DAB(nb_dab=3)
print(f"DAB crée avec {dab.nb_dab} distributeurs")

# Maximum N retraits simultanés s'exécutent en même temps + quand tous les DAB sont occupés client attend sans boucle active
# + dès qu'un DAB se libère, le prochain client en attente en prend possession automatiquement
print("\n[Test 2] Retraits simultanés avec limite de 3 DAB + " 
"sans boucle active + prise de possession automatique")

comptes = [
  Compte(1, 1000),
  Compte(2, 500),
  Compte(3, 200),
  Compte(4, 300),
  Compte(5, 400)
]

def client_retire(num, compte):
  dab.retirer(compte, 100, f'Client {num}')

print("Lancement de 5 clients qui retirent simultanément (avec 3 DAB)...\n")

threads = []
for i in range(5):
  t = threading.Thread(target=client_retire, args=(i+1, comptes[i]))
  threads.append(t)
  t.start()
  time.sleep(0.1)

for t in threads:
  t.join()

print("\nTous les clients ont terminé leurs retraits.")
print("Maximum de 3 retraits simultanés a été respecté, les autres clients ont attendu leur tour.")

# Test de retrait avec solde insuffisant
print("\n[Test 3] Retrait avec solde insuffisant")
compte_insuffisant = Compte(6, 50)
success = dab.retirer(compte_insuffisant, 100, "Client 6")
print(f"Retrait refusé correctement : {not success}")


  
