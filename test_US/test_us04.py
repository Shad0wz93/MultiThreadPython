import threading

from banque import Banque
from compte import Compte
from surveillance import Notification

notif = Notification()

solde_initial_compte1 = 100
solde_initial_compte2 = 100

# Création des comptes à débiter et créditer
compte1 = Compte(1, notif, solde_initial=solde_initial_compte1)
compte2 = Compte(2, notif, solde_initial=solde_initial_compte2)

banque = Banque(notif)
banque.ajouter_compte(compte1)
banque.ajouter_compte(compte2)

print("Solde du compte n°1 avant virement :", compte1.get_solde())
print("Solde du compte n°2 avant virement :", compte2.get_solde())

t1 = threading.Thread(target=banque.virement, args=(compte1.numero, compte2.numero, 20))
t2 = threading.Thread(target=banque.virement, args=(compte2.numero, compte1.numero, 30))

t1.start()
t2.start()

t1.join(timeout=5)
t2.join(timeout=5)

solde_final_compte1 = compte1.get_solde()
solde_final_compte2 = compte2.get_solde()

assert solde_initial_compte1 + solde_initial_compte2 == solde_final_compte1 + solde_final_compte2, "Les montants totaux de départ et d'arrivé sont différents : " \
    f"\nMontant total initial : {solde_initial_compte1 + solde_initial_compte2}" \
    f"\nMontant total final : {solde_final_compte1 + solde_final_compte2}"

print("Solde du compte n°1 après virement :", compte1.get_solde())
print("Solde du compte n°2 après virement :", compte2.get_solde())