import threading
from compte import Compte
from surveillance import Notification

# si deux threads retirent en même temps avec solde insuffisant, un seul réussit
print("Deux retraits simultanés sur solde insuffisant")

notif = Notification()
compte = Compte(1, notif, solde_initial=100)

resultats = []

def tenter_retrait():
    resultats.append(compte.retirer(100))

t1 = threading.Thread(target=tenter_retrait)
t2 = threading.Thread(target=tenter_retrait)
t1.start(); t2.start()
t1.join();  t2.join()

assert resultats.count(True) == 1, "ECHEC :les deux retraits ont réussi"
assert compte.get_solde() == 0
print(f"  OK — solde final : {compte.get_solde()}")

# dépôt et retrait simultanés produisent toujours un résultat cohérent
print("Dépôts et retraits simultanés")

compte2 = Compte(2, notif, solde_initial=50)

threads = (
    [threading.Thread(target=compte2.deposer, args=(10,)) for _ in range(10)] +
    [threading.Thread(target=compte2.retirer, args=(10,)) for _ in range(5)]
)
for t in threads: t.start()
for t in threads: t.join()

assert compte2.get_solde() == 100, f"ECHEC :solde = {compte2.get_solde()}"
print(f"  OK — solde final : {compte2.get_solde()}")

# le solde ne devient jamais négatif et get_solde() retourne toujours une valeur cohérente
print("get_solde() ne retourne jamais une valeur négative")

compte3 = Compte(3, notif, solde_initial=50)
soldes_lus = []

def lire():
    for _ in range(200):
        soldes_lus.append(compte3.get_solde())

def operer():
    for _ in range(100):
        compte3.retirer(10)
        compte3.deposer(10)

thread_lire = threading.Thread(target=lire)
thread_operer = threading.Thread(target=operer)
thread_lire.start()
thread_operer.start()
thread_lire.join()
thread_operer.join()

assert all(s >= 0 for s in soldes_lus), "ECHEC : solde négatif détecté"
print(f"  OK — {len(soldes_lus)} lectures, solde toujours >= 0")