import krpc, time

conn = krpc.connect(name='Fine tune orbit')
vessel = conn.space_center.active_vessel
body = vessel.orbit.body

# Данные
target_pe = 20_000_000
target_ap = 43_000_000
pe_alt = vessel.orbit.periapsis_altitude # текущий пе
ap_alt = vessel.orbit.apoapsis_altitude # текущий ап

# Подключаем автопилот
ap = vessel.auto_pilot
ap.reference_frame = body.non_rotating_reference_frame

# Этап 1: Уменьшаем перицентр
# Ускоряем время до апоцентра
conn.space_center.warp_to(conn.space_center.ut + vessel.orbit.time_to_apoapsis - 5)
ap.target_direction = vessel.flight(ap.reference_frame).retrograde
ap.engage()
time.sleep(1)

vessel.control.throttle = 0.05
while True:
    pe_alt = vessel.orbit.periapsis_altitude
    if pe_alt <= target_pe:
        print(f"\nПерицентр достиг цели: {pe_alt/1000:.1f} км")
        break
    time.sleep(0.2)

vessel.control.throttle = 0.0
ap.disengage()

# Этап 2: Поднимаем апоцентр
# Ускоряем время до апоцентра
conn.space_center.warp_to(conn.space_center.ut + vessel.orbit.time_to_periapsis - 5)
ap.target_direction = vessel.flight(ap.reference_frame).prograde
ap.engage()
time.sleep(1)

vessel.control.throttle = 0.05
while True:
    ap_alt = vessel.orbit.apoapsis_altitude
    if ap_alt >= target_ap:
        print(f"\nАпоцентр достиг цели: {ap_alt/1000:.1f} км")
        break
    time.sleep(0.2)
vessel.control.throttle = 0.0
ap.disengage()

print(f"Итоговая орбита: Pe={vessel.orbit.periapsis_altitude/1000:.1f} км, Ap={vessel.orbit.apoapsis_altitude/1000:.1f} км")

