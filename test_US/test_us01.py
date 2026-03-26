import threading
from compte import Compte

print("Dépôt et retrait")
c1 = Compte(1, 100)
print(f"Solde initial: {c1.get_solde()}")
c1.deposer(50)
print(f"Après dépôt de 50: {c1.get_solde()}")
c1.retirer(30)
print(f"Après retrait de 30: {c1.get_solde()}")
print()

print("Retrait avec solde insuffisant")
c2 = Compte(2, 50)
resultat = c2.retirer(100)
print(f"Retrait de 100 sur solde 50: {resultat}")
print(f"Solde inchangé: {c2.get_solde()}")
print()

print("les Deux threads retirent 60 sur 100")
c3 = Compte(3, 100)
resultats = []

def retrait_concurrent():
    resultat = c3.retirer(60)
    resultats.append(resultat)

t1 = threading.Thread(target=retrait_concurrent)
t2 = threading.Thread(target=retrait_concurrent)

t1.start()
t2.start()
t1.join()
t2.join()

print(f"Résultats: {resultats}")
print(f"Solde final: {c3.get_solde()}")
print()