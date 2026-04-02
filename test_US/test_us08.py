import threading
import time

from compte import Compte
from historique import Historique
from surveillance import Notification

notif = Notification()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

historique = Historique()

# ---------------------------------------------------------------------------
# Toutes les opérations sont horodatées et enregistrées
# ---------------------------------------------------------------------------
print("[Test 1] Enregistrement horodaté des opérations")

compte1 = Compte(1, notif, solde_initial=500)
compte2 = Compte(2, notif, solde_initial=300)

# Dépôt
compte1.deposer(100)
historique.enregistrer("depot", compte1.numero, 100)

# Retrait réussi
succes = compte1.retirer(50)
historique.enregistrer("retrait", compte1.numero, 50, succes)

# Retrait refusé
succes = compte2.retirer(500)
historique.enregistrer("retrait", compte2.numero, 500, succes)

# Virement
compte1.retirer(80)
compte2.deposer(80)
historique.enregistrer("virement", compte1.numero, 80)
historique.enregistrer("virement", compte2.numero, 80)

print(f"  {len(historique.get_toutes())} opérations enregistrées")
assert len(historique.get_toutes()) == 5
print("  OK")

# ---------------------------------------------------------------------------
# Lecture pendant que des opérations sont en cours (sans blocage)
# ---------------------------------------------------------------------------
print("\n[Test 2] Lecture pendant des écritures concurrentes")

historique2 = Historique()
compte3 = Compte(3, notif, solde_initial=1000)
lectures = []

def ecrire():
    for i in range(10):
        compte3.deposer(10)
        historique2.enregistrer("depot", compte3.numero, 10)
        time.sleep(0.01)

def lire():
    for _ in range(10):
        snap = historique2.get_toutes()   # lecture sans bloquer
        lectures.append(len(snap))
        time.sleep(0.015)

t_ecriture = threading.Thread(target=ecrire)
t_lecture  = threading.Thread(target=lire)
t_ecriture.start()
t_lecture.start()
t_ecriture.join()
t_lecture.join()

assert len(historique2.get_toutes()) == 10
print(f"  Tailles lues pendant les écritures : {lectures}")
print("  OK — lecture non bloquante")

# ---------------------------------------------------------------------------
# Ordre chronologique garanti avec des threads concurrents
# ---------------------------------------------------------------------------
print("\n[Test 3] Ordre chronologique avec threads concurrents")

historique3 = Historique()
compte4 = Compte(4, notif, solde_initial=5000)

def deposer_en_boucle(n):
    for _ in range(n):
        compte4.deposer(1)
        historique3.enregistrer("depot", compte4.numero, 1)

threads = [threading.Thread(target=deposer_en_boucle, args=(20,)) for _ in range(5)]
for t in threads: t.start()
for t in threads: t.join()

ops = historique3.get_toutes()
assert len(ops) == 100, f"Attendu 100 opérations, obtenu {len(ops)}"

# Vérifier que les horodatages sont triés
horodatages = [op["horodatage"] for op in ops]
assert horodatages == sorted(horodatages), "Ordre chronologique non respecté"
print(f"  100 opérations enregistrées par 5 threads, ordre chronologique : OK")

# ---------------------------------------------------------------------------
# Filtrage par compte et par type
# ---------------------------------------------------------------------------
print("\n[Test 4] Filtrage par compte et par type")

par_compte1 = historique.get_par_compte(1)
par_compte2 = historique.get_par_compte(2)
par_depot   = historique.get_par_type("depot")
par_retrait = historique.get_par_type("retrait")
par_virement = historique.get_par_type("virement")

assert len(par_compte1) == 3, f"Attendu 3 ops pour compte 1, obtenu {len(par_compte1)}"
assert len(par_compte2) == 2, f"Attendu 2 ops pour compte 2, obtenu {len(par_compte2)}"
assert len(par_depot)   == 1
assert len(par_retrait) == 2
assert len(par_virement) == 2
print(f"  Compte 1 : {len(par_compte1)} opérations | Compte 2 : {len(par_compte2)} opérations")
print(f"  Dépôts : {len(par_depot)} | Retraits : {len(par_retrait)} | Virements : {len(par_virement)}")
print("  OK")

# ---------------------------------------------------------------------------
# Affichage final
# ---------------------------------------------------------------------------
print("\nHistorique complet (Test 1) :")
historique.afficher()

print("\nTous les tests US-08 sont OK ✓")