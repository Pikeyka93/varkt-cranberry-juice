import krpc
import time
import math
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

DT = 0.2
T_END = 25.0

# -----------------------------
# ФИЗМАТ МОДЕЛЬ
# -----------------------------
G0 = 9.80665

m0 = 82_624.0
m_dry = 30_224.0
TWR0 = 2.015

R_KERBIN = 600_000.0
MU_KERBIN = 3.5316e12
g_surface = MU_KERBIN / R_KERBIN**2

F_THRUST = TWR0 * m0 * g_surface
ISP = 297.5
mdot = F_THRUST / (ISP * G0)

def model_dv(dt=DT, t_end=T_END):
    t = 0.0
    m = m0
    dv = 0.0

    times = []
    dv_hist = []

    while t <= t_end + 1e-9:
        a = F_THRUST / m
        dv += a * dt

        times.append(t)
        dv_hist.append(dv)

        m = max(m_dry, m - mdot * dt)
        t += dt

    return times, dv_hist

# -----------------------------
# KSP (через kRPC)
# -----------------------------
def ksp_dv(dt=DT, t_end=T_END):
    conn = krpc.connect(name="Δv KSP vs Model")
    sc = conn.space_center
    vessel = sc.active_vessel

    while vessel.available_thrust <= 1e-3:
        time.sleep(0.05)

    start_ut = sc.ut
    dv = 0.0

    times = []
    dv_hist = []

    while True:
        t = sc.ut - start_ut

        m = vessel.mass
        T = vessel.available_thrust

        a = (T / m) if m > 1e-6 else 0.0
        dv += a * dt

        times.append(t)
        dv_hist.append(dv)

        if t >= t_end:
            break

        time.sleep(dt)

    conn.close()
    return times, dv_hist

# -----------------------------
# ЗАПУСК
# -----------------------------
print("Сбор Δv из KSP (0–25 c)...")
t_ksp, dv_ksp = ksp_dv()

print("Расчёт Δv по физ-мат модели (0–25 c)...")
t_m, dv_m = model_dv()

# -----------------------------
# ГРАФИК
# -----------------------------
plt.figure(figsize=(10, 6))
plt.plot(t_ksp, dv_ksp, linewidth=3, label="KSP")
plt.plot(t_m, dv_m, linewidth=3, label="Физ-мат модель")
plt.xlim(0, 25)
plt.ylim(bottom=0)
plt.xlabel("Время (с)")
plt.ylabel("Δv (м/с)")
plt.title("Изменение Δv за первые 25 секунд")
plt.grid(True, linestyle="--", alpha=0.7)
plt.legend()
plt.tight_layout()
plt.show()

print(f"\nИтог на 25-й секунде:")
print(f"KSP: Δv ≈ {dv_ksp[-1]:.2f} м/с")
print(f"Модель: Δv ≈ {dv_m[-1]:.2f} м/с")