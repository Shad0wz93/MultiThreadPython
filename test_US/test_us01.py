import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from compte import Compte
from surveillance import Notification

notif = Notification()

print("Test 1 — double retrait simultané sur solde insuffisant")

compte = Compte(1, notif, solde_initial=100)
barrier = threading.Barrier(2)

def retrait_sync():
    barrier.wait()
    return compte.retirer(100)

with ThreadPoolExecutor(max_workers=2) as ex:
    f1 = ex.submit(retrait_sync)
    f2 = ex.submit(retrait_sync)
    resultats = [f1.result(), f2.result()]  # f.result() remonte les exceptions si crash

assert resultats.count(True) == 1,  f"ECHEC : {resultats.count(True)} retraits ont réussi (attendu 1)"
assert resultats.count(False) == 1, f"ECHEC : {resultats.count(False)} retraits ont échoué (attendu 1)"
assert compte.get_solde() == 0,     f"ECHEC : solde = {compte.get_solde()} (attendu 0)"
print(f"  OK — 1 retrait accepté, 1 refusé, solde final : {compte.get_solde()}")

print("Test 2 — forte contention dépôts/retraits")

# solde_initial=0 : certains retraits échoueront forcément
# → on calcule l'attendu dynamiquement plutôt que de le hardcoder
compte2 = Compte(2, notif, solde_initial=0)
NB = 50  # augmenter pour plus de pression (ex: 200)

with ThreadPoolExecutor(max_workers=NB * 2) as ex:
    futures_depots  = [ex.submit(compte2.deposer, 10) for _ in range(NB)]
    futures_retraits = [ex.submit(compte2.retirer, 10) for _ in range(NB)]
    # on attend tout et on récupère les exceptions éventuelles
    for f in as_completed(futures_depots + futures_retraits):
        f.result()

retraits_reussis = sum(1 for f in futures_retraits if f.result())
attendu = NB * 10 - retraits_reussis * 10
assert compte2.get_solde() == attendu, (
    f"ECHEC : solde = {compte2.get_solde()}, attendu {attendu} "
    f"({NB} dépôts, {retraits_reussis} retraits réussis)"
)
assert compte2.get_solde() >= 0, f"ECHEC : solde négatif {compte2.get_solde()}"
print(f"  OK — {retraits_reussis}/{NB} retraits réussis, solde final : {compte2.get_solde()}")

print("Test 3 — solde jamais négatif sous lecture concurrente")

compte3 = Compte(3, notif, solde_initial=10)
soldes_lus = []
barrier3 = threading.Barrier(2)

def lire():
    barrier3.wait()
    for _ in range(500):
        soldes_lus.append(compte3.get_solde())

def operer():
    barrier3.wait()
    for _ in range(200):
        compte3.retirer(10)
        compte3.deposer(10)

with ThreadPoolExecutor(max_workers=2) as ex:
    f_lire   = ex.submit(lire)
    f_operer = ex.submit(operer)
    f_lire.result()
    f_operer.result()

negatifs = [s for s in soldes_lus if s < 0]
assert not negatifs, f"ECHEC : valeurs négatives détectées : {negatifs}"
print(f"  OK — {len(soldes_lus)} lectures, min observé : {min(soldes_lus)}, aucune valeur négative")

print("Test 4 — get_solde() ne retourne jamais une valeur intermédiaire")

compte4 = Compte(4, notif, solde_initial=100)
# les seules valeurs légitimes : 100 au départ, puis 90 ou 100 selon retrait/dépôt en cours
VALEURS_VALIDES = set(range(0, 110, 10))
valeurs_invalides = []
barrier4 = threading.Barrier(2)

def lire_en_boucle():
    barrier4.wait()
    for _ in range(1000):
        s = compte4.get_solde()
        if s not in VALEURS_VALIDES:
            valeurs_invalides.append(s)

def retirer_deposer():
    barrier4.wait()
    for _ in range(300):
        compte4.retirer(10)
        compte4.deposer(10)

with ThreadPoolExecutor(max_workers=2) as ex:
    f1 = ex.submit(lire_en_boucle)
    f2 = ex.submit(retirer_deposer)
    f1.result()
    f2.result()

assert not valeurs_invalides, f"ECHEC : valeurs intermédiaires lues : {valeurs_invalides}"
print(f"  OK — 1000 lectures, aucune valeur intermédiaire détectée")
print("Tous les tests US-01 sont passés ✓")