import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns

# 1. Читаем файл
with open('times.txt', 'r', encoding='utf-8') as file:
    text = file.read()

# 2. Извлекаем сырые времена
times_str = re.findall(r'^\d+\.\s+(\d+\.\d+)', text, re.MULTILINE)
raw_times = [float(t) for t in times_str]

if not raw_times:
    print("Не удалось найти время сборок.")
    exit()

df_raw = pd.DataFrame({'Time': raw_times})
total_initial = len(df_raw)

# 3. Фильтрация выбросов (отсекаем все, что >= 25.00 сек)
CUTOFF = 25.00
df = df_raw[df_raw['Time'] < CUTOFF].copy().reset_index(drop=True)
removed_count = total_initial - len(df)
removed_pct = (removed_count / total_initial) * 100

# Группы по целым секундам
df['Group'] = df['Time'].astype(int)

# 4. Расчет скользящих средних
windows = [5, 12, 100, 500, 1000]
for w in windows:
    if len(df) >= w:
        df[f'ao{w}'] = df['Time'].rolling(w).mean()
    else:
        df[f'ao{w}'] = None

# Базовые метрики
pb_single = df['Time'].min()
worst_time = df['Time'].max()
mean_time = df['Time'].mean()
median_time = df['Time'].median()
std_dev = df['Time'].std()

# Поиск лучших скользящих средних сессии
best_aos = {}
for w in windows:
    col = f'ao{w}'
    if col in df and df[col].notna().any():
        best_aos[f'Ao{w}'] = f"{df[col].min():.2f} с"
    else:
        best_aos[f'Ao{w}'] = "N/A"

# 5. Построение дашборда
sns.set_theme(style="whitegrid")
fig = plt.figure(figsize=(16, 14))

# hspace=0.45 дает достаточный зазор между графиками
gs = fig.add_gridspec(3, 1, height_ratios=[1.2, 4.5, 4.5], hspace=0.45)

ax0 = fig.add_subplot(gs[0])
ax1 = fig.add_subplot(gs[1])
ax2 = fig.add_subplot(gs[2])

# --- БЛОК 0: Сводная статистика (Инфо-панель) ---
ax0.axis('off')

stats_col1 = (
    "ОБЪЕМ ДАННЫХ\n"
    f"• Всего сборок: {total_initial}\n"
    f"• Валидных (< {CUTOFF:.0f} с): {len(df)}\n"
    f"• Отсеяно фейлов: {removed_count} ({removed_pct:.1f}%)"
)

stats_col2 = (
    "ОСНОВНЫЕ МЕТРИКИ\n"
    f"• PB (Single): {pb_single:.2f} с\n"
    f"• Среднее (Mean): {mean_time:.2f} с\n"
    f"• Медиана: {median_time:.2f} с\n"
    f"• Станд. откл. (σ): {std_dev:.2f} с\n"
    f"• Худшее (в выборке): {worst_time:.2f} с"
)

stats_col3 = (
    "ЛУЧШИЕ СРЕДНИЕ (BEST ROLLING)\n"
    f"• Best Ao5:    {best_aos['Ao5']}\n"
    f"• Best Ao12:   {best_aos['Ao12']}\n"
    f"• Best Ao100:  {best_aos['Ao100']}\n"
    f"• Best Ao500:  {best_aos['Ao500']}\n"
    f"• Best Ao1000: {best_aos['Ao1000']}"
)

box_style = dict(boxstyle='round,pad=0.8', facecolor='#F8FAFC', edgecolor='#CBD5E1', linewidth=1.2)
ax0.text(0.02, 0.5, stats_col1, transform=ax0.transAxes, fontsize=10, va='center', linespacing=1.4, bbox=box_style)
ax0.text(0.35, 0.5, stats_col2, transform=ax0.transAxes, fontsize=10, va='center', linespacing=1.4, bbox=box_style)
ax0.text(0.68, 0.5, stats_col3, transform=ax0.transAxes, fontsize=10, va='center', linespacing=1.4, bbox=box_style, family='monospace')

# --- БЛОК 1: Градиентная гистограмма ---
min_sec = df['Group'].min()
max_sec = df['Group'].max()
group_counts = df['Group'].value_counts().reindex(range(min_sec, max_sec + 1), fill_value=0)

# Цветовой градиент: Изумрудный -> Зеленый -> Лайм -> Золотой -> Оранжевый -> Красный
palette = ['#15803D', '#22C55E', '#84CC16', '#EAB308', '#F97316', '#EF4444']
speed_cmap = mcolors.LinearSegmentedColormap.from_list('speed_gradient', palette)
norm = mcolors.Normalize(vmin=min_sec, vmax=max_sec)
bar_colors = [speed_cmap(norm(sec)) for sec in group_counts.index]

bars = ax1.bar(
    range(len(group_counts)),
    group_counts.values,
    color=bar_colors,
    edgecolor='white',
    width=0.82
)

# Точные числа над столбиками
labels = [str(v) if v > 0 else '' for v in group_counts.values]
ax1.bar_label(bars, labels=labels, padding=3, fontsize=9, fontweight='bold', color='#1E293B')

ax1.set_ylim(0, group_counts.max() * 1.12)
ax1.set_title(f'Распределение сборок 3x3 по секундам (очищенная выборка < {CUTOFF:.0f} с)', fontsize=12, pad=10, fontweight='bold')
ax1.set_xlabel('Группа времени (секунды)', fontsize=10, labelpad=8)
ax1.set_ylabel('Количество сборок', fontsize=10)
ax1.set_xticks(range(len(group_counts)))
ax1.set_xticklabels([f"{sec}.xx" for sec in group_counts.index], rotation=45, ha='right', fontsize=9)

# --- БЛОК 2: График тренда (Raw + Ao5 + Ao12 + Ao100 + Ao500 + Ao1000) ---
solve_numbers = range(1, len(df) + 1)

ax2.plot(solve_numbers, df['Time'], color='#94A3B8', alpha=0.3, linewidth=0.6, label='Сборка (raw)')

trend_styles = [
    ('ao5', 'Ao5', '#F59E0B', 1.0, 0.8),       # Янтарный
    ('ao12', 'Ao12', '#EF4444', 1.2, 0.9),     # Красный
    ('ao100', 'Ao100', '#2563EB', 1.8, 1.0),   # Синий
    ('ao500', 'Ao500', '#9333EA', 2.2, 1.0),   # Фиолетовый
    ('ao1000', 'Ao1000', '#059669', 2.5, 1.0), # Зеленый
]

for col, label_name, color, lw, alpha in trend_styles:
    if col in df and df[col].notna().any():
        ax2.plot(solve_numbers, df[col], color=color, linewidth=lw, alpha=alpha, label=label_name)

ax2.set_title('Прогресс за всю сессию (Скользящие средние)', fontsize=12, pad=10, fontweight='bold')
ax2.set_xlabel('Номер сборки (по порядку)', fontsize=10)
ax2.set_ylabel('Время (сек)', fontsize=10)
ax2.set_ylim(df['Time'].min() - 0.5, CUTOFF + 0.5)
ax2.legend(loc='upper right', ncol=6, frameon=True, facecolor='white', framealpha=0.9)

# 6. Сохранение
output_file = 'speedcubing_stats.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Готово! График обновлен и сохранен в: {output_file}")
