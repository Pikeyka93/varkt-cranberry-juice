import krpc
import time

# Подключаемся к игре и выбираем активный корабль
conn = krpc.connect()
vessel = conn.space_center.active_vessel


# Берём созданный узел для прожига
node = vessel.control.nodes[0]
print("Начинаем подготовку к прожигу")

# Включаем автопилот и наводимся на вектор прожига
ap = vessel.auto_pilot
ap.reference_frame = node.reference_frame
ap.target_direction = node.burn_vector(node.reference_frame)
ap.engage()

# === Оценка длительности прожига ===
F = vessel.available_thrust                  # сила тяги (Н)
Isp = vessel.specific_impulse * 9.81         # удельный импульс (м/с²)
m0 = vessel.mass                             # начальная масса корабля
dv = node.delta_v                            # требуемая Δv узла

# уравнение Циолковского
m1 = m0 / (2.71828 ** (dv / Isp))
flow_rate = F / Isp                          # расход топлива (кг/с)
burn_time = (m0 - m1) / flow_rate            # длительность прожига (с)

print(f"🔥 Расчётное время прожига: {burn_time:.1f} с")

# === Подготовка к прожигу ===
time_to_node = node.time_to
burn_start = time_to_node - burn_time / 2

# Перематываем время ближе к прожигу
if burn_start > 3:
    conn.space_center.warp_to(conn.space_center.ut + burn_start - 2)

# Выполнение прожига
vessel.control.throttle = 1.0
time.sleep(burn_time * 0.9)

# контроль аккуратного допрожига
while True:
    rem = node.remaining_delta_v  # Оставшаяся дельта v
    if rem > 10:
        vessel.control.throttle = 0.3
    elif rem > 3:
        vessel.control.throttle = 0.15
    else:
        vessel.control.throttle = 0.05

    # Проверка окончания манёвра
    if rem < 1:
        vessel.control.throttle = 0.0
        break

    time.sleep(0.1)

# Отключаем автопилот и удаляем узел
ap.disengage()
node.remove()

print("Манёвр успешно выполнен!")

# Отделяем вторую ступень
time.sleep(5)
vessel.control.activate_next_stage()  # переход на следующую ступень
time.sleep(2)
vessel.control.activate_next_stage()  # включение следующего двигателя
time.sleep(2)

conn.close()
print("Спутник летит к марсу")
