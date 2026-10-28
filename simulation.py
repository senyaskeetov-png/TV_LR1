# ЛР №1. Расчёт частот и моделирование бросков банки.
# Запуск: python simulation.py
# Перед запуском: pip install numpy scipy matplotlib pillow

import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import chisquare
from plots import make_plots

folder = Path(__file__).resolve().parent
with open(folder / 'throws_main.json', encoding='utf-8') as file:
    throws = json.load(file)['throws']

names = ['Верх', 'Низ', 'Бок']
areas = np.array([34.73, 34.73, 351.61])
p = areas / sum(areas)
counts = [throws.count(name) for name in names]
assert len(throws) == 100 and sum(counts) == 100
frequencies = np.array(counts) / len(throws)
chi2, p_value = chisquare(counts, len(throws) * p)

# Размеры эквивалентного цилиндра в метрах.
r = math.sqrt(34.73 / math.pi) / 100
height = 351.61 / (2 * math.pi * r * 100) / 100
a = height / 2
rho = 0.001  # Скругление обода 1 мм - условное упрощение.
g = 9.81


def support(angle):
    # Расстояние от центра банки до её нижней точки.
    return (a - rho) * abs(math.cos(angle)) + (r - rho) * abs(math.sin(angle)) + rho


def gap(t, angle, speed, clearance):
    z = support(angle) + clearance - g * t ** 2 / 2
    return z - support(angle + speed * t)


def throw(angle, speed, clearance):
    # Сначала ищем первый контакт с шагом 0,005 с.
    right = 0.0
    while gap(right, angle, speed, clearance) > 0:
        right += 0.005
    left = right - 0.005
    # Затем уточняем время касания делением отрезка пополам.
    for step in range(40):
        middle = (left + right) / 2
        if gap(middle, angle, speed, clearance) > 0:
            left = middle
        else:
            right = middle
    time = (left + right) / 2
    final_angle = angle + speed * time
    # Скруглённый обод делим между основанием и боком по порогу 45°.
    if abs(math.cos(final_angle)) < abs(math.sin(final_angle)):
        result = 2  # Бок
    elif math.cos(final_angle) < 0:
        result = 0  # Верх
    else:
        result = 1  # Низ
    return result, time


n = 100000
seed = 27102026
rng = np.random.default_rng(seed)
angles = rng.uniform(0, 2 * math.pi, n)
speeds = rng.uniform(-8, 8, n)  # Не измерено: выбранное допущение.
clearances = rng.uniform(0.15, 0.20, n)
outcomes = []
examples = {}
max_error = 0
for i in range(n):
    result, time = throw(angles[i], speeds[i], clearances[i])
    outcomes.append(result)
    error = abs(gap(time, angles[i], speeds[i], clearances[i]))
    max_error = max(max_error, error)
    if str(result) not in examples:
        examples[str(result)] = {
            'angle': angles[i], 'speed': speeds[i],
            'clearance': clearances[i], 'time': time
        }

rows = []
for size in [10, 100, 1000, 10000, 100000]:
    part = outcomes[:size]
    numbers = [part.count(i) for i in range(3)]
    row = {'N': size, 'counts': numbers, 'frequencies': [x / size for x in numbers]}
    rows.append(row)
    print(size, row['frequencies'])

results = {
    'names': names, 'p': p.tolist(), 'physical_counts': counts,
    'physical_frequencies': frequencies.tolist(),
    'delta': abs(frequencies - p).tolist(),
    'chi2': float(chi2), 'p_value': float(p_value),
    'simulation': rows, 'r_m': r, 'h_m': height, 'seed': seed,
    'max_contact_residual_m': float(max_error),
    'outcomes': outcomes, 'examples': examples
}
with open(folder / 'results.json', 'w', encoding='utf-8') as file:
    json.dump(results, file, ensure_ascii=False, indent=2)

make_plots(results, throws, folder)
print('Готово. Результаты - в results.json, рисунки - в папке graphs.')
