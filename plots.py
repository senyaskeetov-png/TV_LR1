# Рисунки для ЛР №1. Этот файл вызывается из simulation.py.
# Расчёты бросков находятся в simulation.py, здесь только графики.

import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.transforms import Affine2D
from matplotlib.animation import FuncAnimation, PillowWriter


def make_plots(results, throws, folder):
    graphs = folder / 'graphs'
    graphs.mkdir(exist_ok=True)
    names = results['names']
    outcomes = np.array(results['outcomes'])
    p = results['p']
    colors = ['#2365a1', '#d27c21', '#32875a']
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10})

    # 1. Накопленные частоты компьютерных бросков.
    x = np.arange(1, len(outcomes) + 1)
    fig, axes = plt.subplots(3, 1, figsize=(8, 8), sharex=True)
    for i in range(3):
        frequency = np.cumsum(outcomes == i) / x
        axes[i].plot(x, frequency, color=colors[i], label='Компьютерная частота')
        axes[i].axhline(p[i], color='#a84040', linestyle='--', label='Модель по площадям')
        axes[i].set_xscale('log')
        axes[i].set_ylim(0, 1)
        axes[i].set_ylabel(names[i])
        axes[i].grid(alpha=0.2)
    axes[0].legend(fontsize=8)
    axes[2].set_xlabel('Число компьютерных испытаний n')
    fig.tight_layout()
    fig.savefig(graphs / 'convergence.png', dpi=180)
    plt.close(fig)

    # 2. Сравнение трёх наборов значений.
    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = np.arange(3)
    ax.bar(x - 0.24, p, 0.24, label='По площадям')
    ax.bar(x, results['physical_frequencies'], 0.24, label='Физический опыт')
    ax.bar(x + 0.24, results['simulation'][-1]['frequencies'], 0.24, label='Компьютерная модель')
    ax.set_xticks(x, names)
    ax.set_ylim(0, 1)
    ax.set_ylabel('Вероятность / относительная частота')
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.2)
    fig.tight_layout()
    fig.savefig(graphs / 'comparison.png', dpi=180)
    plt.close(fig)

    # 3. Накопленные частоты реальных бросков.
    fig, ax = plt.subplots(figsize=(8, 3.8))
    x = np.arange(1, len(throws) + 1)
    for i in range(3):
        numbers = np.cumsum(np.array(throws) == names[i])
        ax.plot(x, numbers / x, color=colors[i], label=names[i])
    ax.set(xlabel='Число физических испытаний n', ylabel='Накопленная частота', ylim=(0, 1))
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(graphs / 'physical.png', dpi=180)
    plt.close(fig)

    # 4. Положение банки в разные моменты полёта.
    r = results['r_m']
    a = results['h_m'] / 2
    rho = 0.001

    def draw(ax, example, fraction):
        t = example['time'] * fraction
        angle = example['angle'] + example['speed'] * t
        start = (a - rho) * abs(math.cos(example['angle']))
        start += (r - rho) * abs(math.sin(example['angle'])) + rho
        z = start + example['clearance'] - 9.81 * t ** 2 / 2
        shape = FancyBboxPatch((-r, -a), 2*r, 2*a,
                               boxstyle='round,pad=0,rounding_size=0.001',
                               facecolor='#c3d4df', edgecolor='#162c3d')
        shape.set_transform(Affine2D().rotate(-angle).translate(0, z) + ax.transData)
        ax.add_patch(shape)
        ax.plot(a * math.sin(angle), z + a * math.cos(angle), 'o', color=colors[0], markersize=3)
        if fraction == 1:
            u = np.array([math.sin(angle), math.cos(angle)])
            v = np.array([math.cos(angle), -math.sin(angle)])
            point = np.array([0., z]) - (a-rho)*np.sign(math.cos(angle))*u
            point += (r-rho)*np.sign(math.sin(angle))*v - np.array([0., rho])
            ax.plot(point[0], point[1], 'o', color='crimson', markersize=4)
        ax.axhline(0, color='black')
        ax.set(xlim=(-0.12, 0.12), ylim=(-0.015, 0.41), aspect='equal')
        ax.set_title(f't = {t:.3f} с', fontsize=9)
        ax.grid(alpha=0.15)

    fig, axes = plt.subplots(3, 4, figsize=(9, 8))
    for i in range(3):
        for j, fraction in enumerate([0, 0.35, 0.7, 1]):
            draw(axes[i, j], results['examples'][str(i)], fraction)
        axes[i, 0].set_ylabel(names[i] + '\nz, м')
    fig.suptitle('Синяя точка - верх банки, красная - первое касание', fontsize=11)
    fig.tight_layout()
    fig.savefig(graphs / 'motion.png', dpi=170)
    plt.close(fig)

    # Та же визуализация в виде короткой GIF-анимации.
    fig, axes = plt.subplots(1, 3, figsize=(6, 4))
    def frame(k):
        for i in range(3):
            axes[i].clear()
            draw(axes[i], results['examples'][str(i)], k / 39)
            axes[i].set_xlabel(names[i])
    animation = FuncAnimation(fig, frame, frames=40, interval=70)
    animation.save(graphs / 'motion.gif', writer=PillowWriter(fps=14))
    plt.close(fig)
