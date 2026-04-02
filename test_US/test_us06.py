# test_US06.py
import threading
from banque import Banque
from compte import Compte
from surveillance import Notification
import time

# Setup
notification = Notification()
banque = Banque(notification)

compte1 = Compte(1, notification, solde_initial=50)
compte2 = Compte(2, notification, solde_initial=100)
banque.ajouter_compte(compte1)
banque.ajouter_compte(compte2)

# Thread de surveillance (passif, attend les alertes)
t_surveillance = threading.Thread(target=notification.surveiller, daemon=True)
t_surveillance.start()

# Test 1 — retrait insuffisant sur compte1 (solde 50, on retire 80 → alarme)
print("=== Test 1 : retrait insuffisant ===")
resultat = banque.virement(compte1.numero, compte2.numero, 80)
print(f"Virement refusé : {not resultat}")

# Test 2 — plusieurs déclenchements simultanés
time.sleep(0.2)
notification._decouvert.clear()

print("\n=== Test 2 : alertes simultanées ===")
t1 = threading.Thread(target=compte1.retirer, args=(80,))
t2 = threading.Thread(target=banque.virement, args=(compte1.numero, compte2.numero, 80))
t1.start()
t2.start()
t1.join()
t2.join()

time.sleep(0.5)

print(f"\nSolde compte 1 : {compte1.get_solde()}€")
print(f"Solde compte 2 : {compte2.get_solde()}€")