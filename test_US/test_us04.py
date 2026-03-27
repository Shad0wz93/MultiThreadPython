import threading

from banque import Banque
from compte import Compte

# Création des comptes à débiter et créditer
compte1 = Compte(1, 100)
compte2 = Compte(2, 100)

banque = Banque()
banque.ajouter_compte(compte1)
banque.ajouter_compte(compte2)

print("Solde du compte n°1 avant virement :", compte1.get_solde())
print("Solde du compte n°2 avant virement :", compte2.get_solde())

t1 = threading.Thread(target=banque.virement, args=(compte1.numero, compte2.numero, 20))
t2 = threading.Thread(target=banque.virement, args=(compte2.numero, compte1.numero, 30))

t1.start()
t2.start()

t1.join()
t2.join()

print("Solde du compte n°1 après virement :", compte1.get_solde())
print("Solde du compte n°2 après virement :", compte2.get_solde())