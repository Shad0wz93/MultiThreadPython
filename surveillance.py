import threading
import time


class TableauDeBord(threading.Thread):
    """
    Thread de monitoring affichant l'état du système en temps réel
    """

    def __init__(self, file_clients, pool_guichets, comptes, intervalle=2):
        """
        :param file_clients: FileClients partagée
        :param pool_guichets: PoolGuichets pour voir les guichets actifs
        :param comptes: Dict des comptes
        :param intervalle: Secondes entre chaque affichage
        """
        super().__init__(daemon=True)
        self.file_clients = file_clients
        self.pool_guichets = pool_guichets
        self.comptes = comptes
        self.intervalle = intervalle
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            self.afficher_etat()
            time.sleep(self.intervalle)

    def afficher_etat(self):
        """Affiche l'état global du système"""
        solde_total = sum(c.get_solde() for c in self.comptes.values())
        taille_file = self.file_clients.taille_file()

        print(f"\n[TableauDeBord] Solde total: {solde_total:.2f}€ | File: {taille_file} clients")

    def arreter(self):
        self._stop_event.set()


class Notification:
    def __init__(self):
        self.condition = threading.Condition()
        # liste des comptes en découvert
        self._decouvert = []

    def surveiller(self):
        """Thread passif qui attend les alertes"""
        with self.condition:
            while True:
                # attend qu'il y ait quelque chose
                while not self._decouvert:
                    self.condition.wait()
                # traite toutes les alertes en attente
                while self._decouvert:
                    numero = self._decouvert.pop(0)
                    print(f"[ALERTE] Compte n°{numero} : solde insuffisant (opération refusée)")

    def alerter(self, numero_compte: int):
        """
        Appelé par la Banque après un retrait ou un virement
        :param numero_compte: Le numéro du compte affecté par l'alerte
        """
        with self.condition:
            self._decouvert.append(numero_compte)
            self.condition.notify_all()