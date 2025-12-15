import random
import time
import math
import csv

# === Parameter ===
cluster_size = 30
mutation_chance = math.pi / 100
refresh_rate = 0.01  # Sekunden (einstellbar z. B. 0.05 oder 1.0)
logfile_name = "cluster_log.csv"

# === Primzahlen prüfen ===
def is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True

# === Fibonacci-Zeitpunkte vorbereiten ===
fibonacci_times = set()
a, b = 0, 1
while a < 1000000:
    fibonacci_times.add(a)
    a, b = b, a + b

# === Anfangszustand ===
cluster = [random.choice([0, 1]) for _ in range(cluster_size)]
t = 0
no_mutation_count = 0

# === CSV-Log öffnen ===
with open(logfile_name, mode="w", newline="") as logfile:
    writer = csv.writer(logfile)
    writer.writerow(["T", "Energie", "Symmetrie", "Bitstring"])

    print("Starte Cluster-Beobachtung mit Fibonacci + Primzahl-Mutation und Logging...")
    time.sleep(1)

    while True:
        energie = sum(cluster)
        symmetrie = sum(1 for i in range(cluster_size // 2)
                        if cluster[i] == cluster[-(i + 1)])
        bitstring = ''.join(str(bit) for bit in cluster)

        # Log in Datei schreiben
        writer.writerow([t, energie, symmetrie, bitstring])
        logfile.flush()

        # Terminalausgabe
        print(f"T={t:07d} | Energie={energie:02d} | Symmetrie={symmetrie:02d} | {bitstring}", flush=True)

        # Mutation
        mutation_occurred = False
        for i in range(cluster_size):
            if random.random() < mutation_chance:
                cluster[i] = 1 - cluster[i]
                mutation_occurred = True

        # Sondermutation bei Fibonacci- oder Primzahl-Zeitpunkten
        if t in fibonacci_times or is_prime(t):
            index = random.randint(0, cluster_size - 1)
            cluster[index] = 1 - cluster[index]
            mutation_occurred = True

        # Mutation-Überwachung mit Warnung
        if mutation_occurred:
            no_mutation_count = 0
        else:
            no_mutation_count += 1
            if no_mutation_count > 10:
                print(f"[Warnung] Kein Mutation seit {no_mutation_count} Schritten!", flush=True)

        t += 1
        time.sleep(refresh_rate)
