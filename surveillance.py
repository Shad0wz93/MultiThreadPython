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