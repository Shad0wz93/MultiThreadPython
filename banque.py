from compte import Compte
from surveillance import Notification


class Banque:
    def __init__(self, notification: Notification):
        self._comptes: dict[int, Compte] = {}
        self._notification = notification

    def ajouter_compte(self, compte: Compte):
        """
        Méthode pour ajouter un compte dans la liste compte de la classe
        :param compte: Le compte à ajouter
        """
        self._comptes[compte.numero] = compte

    def virement(self, numero_source: int, numero_destination: int, montant: int) -> bool:
        """
        Méthode pour effectuer un virement entre 2 comptes
        :param numero_source: Numéro de compte du compte source (débité)
        :param numero_destination: Numéro de compte du compte destination (crédité)
        :param montant: Montant à envoyer
        :return: Si le virement est un succès ou non
        """
        if montant <= 0:
            raise ValueError("Le montant doit être positif.")

        source = self._comptes[numero_source]
        destination = self._comptes[numero_destination]

        premier, second = sorted([source, destination], key=lambda c: c.numero)

        with premier._lock:
            with second._lock:
                if source._solde < montant:
                    self._notification.alerter(source.numero)
                    return False
                source._solde -= montant
                destination._solde += montant
                return True