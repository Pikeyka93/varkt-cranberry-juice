import krpc
import time
import math
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

DT = 0.2
T_END = 25.0

G0 = 9.80665

m0 = 82_624.0
m_dry = 30_224.0
TWR0 = 2.015

R_KERBIN = 600_000.0
MU_KERBIN = 3.5316e12
g_surface = MU_KERBIN / (R_KERBIN ** 2)

F_THRUST = TWR0 * m0 * g_surface
ISP = 297.5
mdot = F_THRUST / (ISP * G0)

def mass_model(dt=DT, t_end=T_END):
    t = 0.0
    m = m0
    times, masses = [], []
    while t <= t_end + 1e-9:
        times.append(t)
        masses.append(m)
        m = max(m_dry, m - mdot * dt)
        t += dt
    return times, masses

def mass_ksp(dt=DT, t_end=T_END):
    conn = krpc.connect(name="Mass KSP vs Model")
    sc = conn.space_center
    vessel = sc.active_vessel

    while vessel.available_thrust <= 1e-3:
        time.sleep(0.05)

    start_ut = sc.ut
    times, masses = [], []

    while True:
        t = sc.ut - start_ut
        times.append(t)
        masses.append(vessel.mass)

        if t >= t_end:
            break

        time.sleep(dt)

    conn.close()
    return times, masses

print("Сбор массы из KSP (0–25 c)...")
t_ksp, m_ksp = mass_ksp()

print("Расчёт массы по физ-мат модели (0–25 c)...")
t_m, m_m = mass_model()

plt.figure(figsize=(10, 6))
plt.plot(t_ksp, m_ksp, linewidth=3, label="KSP: масса")
plt.plot(t_m, m_m, linewidth=3, label="Модель: масса")
plt.xlim(0, 25)
plt.ylim(bottom=0)
plt.xlabel("Время (с)")
plt.ylabel("Масса (кг)")
plt.title("Изменение массы за первые 25 секунд (KSP vs модель)")
plt.grid(True, linestyle="--", alpha=0.7)
plt.legend()
plt.tight_layout()
plt.show()

print(f"\nИтог на 25-й секунде:")
print(f"KSP: масса ≈ {m_ksp[-1]:.2f} кг")
print(f"Модель: масса ≈ {m_m[-1]:.2f} кг")
