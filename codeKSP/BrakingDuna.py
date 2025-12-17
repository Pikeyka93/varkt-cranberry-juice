import krpc
import time

# === 1. Подключение и начальные данные ===
conn = krpc.connect(name='Duna Capture')
vessel = conn.space_center.active_vessel

print("Ожидание входа в сферу влияния Дюны...")

# Ждём входа в SOI Дюны
body = vessel.orbit.body
while body.name != "Duna":
    time.sleep(5)
    body = vessel.orbit.body

print("Вошли в сферу влияния Дюны")

# Расчёт параметров тормозного манёвра
body = vessel.orbit.body
mu = body.gravitational_parameter
r_p = vessel.orbit.periapsis
a = vessel.orbit.semi_major_axis
v_current = (mu * (2 / r_p - 1 / a))**0.5
v_circ = (mu / r_p)**0.5
delta_v_capture = v_current - v_circ

# Разворот на ретроград и подготовка прожига
ap = vessel.auto_pilot
ap.reference_frame = body.non_rotating_reference_frame
ap.target_direction = vessel.flight(ap.reference_frame).retrograde
ap.engage()

print("Наводимся на ретроград")
time.sleep(2)

# Расчёт длительности прожига
F = vessel.available_thrust
Isp = vessel.specific_impulse * 9.81
m0 = vessel.mass
dv = delta_v_capture

m1 = m0 / (2.71828 ** (dv / Isp))
flow_rate = F / Isp
burn_time = (m0 - m1) / flow_rate
print(f"Оценка времени прожига: {burn_time:.1f} сек")

# === 5. Перемотка и выполнение торможения ===
time_to_peri = vessel.orbit.time_to_periapsis
burn_start = time_to_peri - burn_time / 2

if burn_start > 5:
    print("Перематываем к точке начала прожига")
    conn.space_center.warp_to(conn.space_center.ut + burn_start - 2)

print("Начинаем торможение в перицентре Дюны")

# Начинаем прожиг
vessel.control.throttle = 1.0
time.sleep(burn_time * 0.9)

# Небольшой дожиг для идеальной скорости
while True:
    v_speed = vessel.flight(body.non_rotating_reference_frame).speed # скорость корабля (относительно неподвижной Дюны)
    v_target = v_circ # скорость круговой орбиты
    if v_speed <= v_target:
        break
    vessel.control.throttle = 0.1
    time.sleep(0.1)

vessel.control.throttle = 0
ap.disengage()

print("Торможение завершено, мы на орбите Дюны")
print(f"Pe = {vessel.orbit.periapsis_altitude:.0f} м, Ap = {vessel.orbit.apoapsis_altitude:.0f} м")

