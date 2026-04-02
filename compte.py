import threading
from surveillance import Notification

class Compte:
    def __init__(self, numero, notification: Notification, solde_initial=0, callback_op=None):
        """
        Représente un compte bancaire thread-safe.

        :param numero: Identifiant du compte
        :param notification
        :param solde_initial: Solde au démarrage
        :param callback_op: Fonction appelée après dépôt/retrait (type_op, montant, succes)
        """
        self.numero = numero
        self._solde = solde_initial

        # Lock pour protéger le solde contre les accès concurrents (US-1)
        self._lock = threading.Lock()

        # Sert à déclencher une alerte en cas de retrait refusé (US-5)
        self._notification = notification

        # callback_op(type_op: str, montant: float, succes: bool)
        self._callback_op = callback_op

    def deposer(self, montant):
        """
        Dépose de l'argent sur le compte (opération atomique grâce au lock).

        :param montant: montant à ajouter
        :raises ValueError: si montant <= 0
        """
        if montant <= 0:
            raise ValueError("Le montant doit être positif.")

        # Section critique : modification du solde
        with self._lock:
            self._solde += montant

        # dépôt réussi si pas d'exception
        if self._callback_op:
            self._callback_op("depot", montant, True)

    def retirer(self, montant) -> bool:
        """Retire de l'argent si le solde est suffisant

        :param montant: montant à retirer
        :return: True si retrait effectué, False sinon
        :raises ValueError: si montant <= 0
        """
        if montant <= 0:
            raise ValueError("Le montant doit être positif.")

        with self._lock:
            if self._solde >= montant:
                self._solde -= montant
                succes = True
            else:
                succes = False

        # alerte si opération refusée (solde insuffisant)
        if not succes:
            self._notification.alerter(self.numero)

        if self._callback_op:
            self._callback_op("retrait", montant, succes)

        return succes

    def get_solde(self) -> float:
        """
        Renvoie le solde actuel.

        On utilise le lock même pour lire, afin d'éviter de lire une valeur
        pendant qu'un autre thread est en train de la modifier.
        """
        with self._lock:
            return self._solde