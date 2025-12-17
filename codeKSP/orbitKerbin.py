import krpc
import time

# Инициализация соединения и основных объектов

conn = krpc.connect()
vessel = conn.space_center.active_vessel
ap = vessel.auto_pilot
control = vessel.control
orbit = vessel.orbit
flight = vessel.flight(vessel.orbit.body.reference_frame)
body = vessel.orbit.body
antenna = vessel.parts.with_title("Коммунотрон 88-88")[0]

# Основные параметры
Target_apoapsis = 100_000
f = 0

# взлет
ap.target_pitch_and_heading(90, 90)
ap.engage()
control.throttle = 1
print('3')
time.sleep(1)
print('2')
time.sleep(1)
print('1')
time.sleep(1)
print('Поехали!')
control.activate_next_stage()

# Поворот под нужным углом
while orbit.apoapsis_altitude < Target_apoapsis:
    # количество твердого топлива в ускорителях
    srb_fuel = vessel.resources.amount('SolidFuel')

    if srb_fuel < 0.1 and f == 0:
        print('Ускорители отделились')
        control.activate_next_stage()
        f = 1

    # текущая высота
    altitude = flight.mean_altitude

    # Меняем наклон пока в атмосфере
    if 1000 < altitude < 70000:
        pitch = max(0, 90 - (altitude / 70000) * 90)
        ap.target_pitch_and_heading(pitch, 90)

    # Мягкое снижение тяги ближе к цели
    if orbit.apoapsis_altitude > 80000:
        control.throttle = 0.5
    if orbit.apoapsis_altitude > 90000:
        control.throttle = 0.2

    time.sleep(0.1)

control.throttle = 0.0
print("Апоцентр 100 км, летим к нему")

# Расчёт манёвра для округления орбиты вокруг Кербина

current_ut = conn.space_center.ut
time_to_ap = orbit.time_to_apoapsis
ut = current_ut + time_to_ap
node = control.add_node(ut)

# параметры тела и орбиты
mu = body.gravitational_parameter
r = body.equatorial_radius + orbit.apoapsis_altitude
a = orbit.semi_major_axis

# скорость в апоцентре и круговой
v_ap = (mu * (2 / r - 1 / a)) ** 0.5
v_circ = (mu / r) ** 0.5

# расчёт нужной дельта-V
delta_v = v_circ - v_ap
print(f'Для циркуляризации нужно примерно {delta_v:.1f} м/с')
node.prograde = delta_v

# Поставим манвер и наведемся на него автопилотом
node = control.nodes[0]
ap.reference_frame = node.reference_frame
burn_vec = node.burn_vector(node.reference_frame)
ap.target_direction = burn_vec
ap.engage()

# расчёт параметров прожига
F = vessel.available_thrust
Isp = vessel.specific_impulse * 9.81
m0 = vessel.mass
dlta_v = node.delta_v
m1 = m0 / (2.71828 ** (dlta_v / Isp))
flow_rate = F / Isp
burn_time = (m0 - m1) / flow_rate

time_to_node = node.time_to
burn_start = time_to_node - burn_time * 0.5
target_ut = conn.space_center.ut + burn_start - 3

while conn.space_center.ut < target_ut:
    time.sleep(0.1)
print(f"Время прожига {int(burn_time)} c")
print(f'Через {int(burn_start)} c после текущего момента нужно включить двигатель.')
# основной прожиг
control.throttle = 1
time.sleep(burn_time * 0.9)

last_dv = node.remaining_delta_v # переменная для отслежки дельта в, чтобы не рос
stable_counter = 0
# контороль аккуратного допрожига
while True:
    dv = node.remaining_delta_v

    if dv > 100:
        control.throttle = 1.0
    elif dv > 50:
        control.throttle = 0.6
    elif dv > 10:
        control.throttle = 0.3
    elif dv > 3:
        control.throttle = 0.15
    else:
        control.throttle = 0.1

    if dv >= last_dv - 0.05:
        stable_counter += 1
    else:
        stable_counter = 0

    if stable_counter > 5:
        print("dv стабилизировалась — узел пройден, стоп")
        control.throttle = 0
        break

    if dv < 0.8:
        control.throttle = 0
        print(f"Прожиг завершён: dv={dv:.2f} м/с")
        break

    last_dv = dv
    time.sleep(0.1)

ap.disengage()
node.remove()
print("Орбита 100 на 100")

# ==============================
# 🔹 Завершение орбитального выведения
# ==============================
time.sleep(2)
control.activate_next_stage()
time.sleep(2)
control.activate_next_stage()
time.sleep(2)
control.activate_next_stage()
time.sleep(2)
control.activate_next_stage()
print('Первая ступень отделилась')
time.sleep(2)
antenna.modules[0].trigger_event("Раскрыть антенну")
print('Антенна раскрылась.')
time.sleep(0.5)
print('Корабль готов к старту на межпланетную орбиту.')
conn.close()

