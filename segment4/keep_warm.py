import time
import modal

Pricer = modal.Cls.lookup("pricer-service", "Pricer")
pricer = Pricer()
while True:
    reply = pricer.wake_up.remote()
    print(reply)
    time.sleep(60)