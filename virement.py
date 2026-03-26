import threading

from compte import Compte

def virement(debite: Compte, credite: Compte, montant: int):
    # Classement des locks toujours dans le même ordre pour éviter le deadlock
    first, second = sorted([debite, credite], key=lambda c: c.numero)

    # Acquisition des locks dans l'ordre reçu
    with first._lock:
        with second._lock:
            if debite._solde < montant:
                return False
            debite._solde -= montant
            credite._solde += montant
            return True

# Création des comptes à débiter et créditer
compte1 = Compte(1, 100)
compte2 = Compte(2, 100)

t1 = threading.Thread(target=virement, args=(compte1, compte2, 20))
t2 = threading.Thread(target=virement, args=(compte2, compte1, 30))

t1.start()
t2.start()

t1.join()
t2.join()

print("Solde du compte n°1 :", compte1.get_solde())
print("Solde du compte n°2 :", compte2.get_solde())