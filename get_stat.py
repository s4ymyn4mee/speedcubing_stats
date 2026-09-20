import sys
import os
import glob
import math
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
from numpy.lib.stride_tricks import sliding_window_view

# ==========================================
# 0. ПАРСИНГ АРГУМЕНТОВ КОМАНДНОЙ СТРОКИ
# ==========================================
parser = argparse.ArgumentParser(
    description="Генератор статистики и дашборда спидкубинга из CSV csTimer"
)
parser.add_argument(
    "-c", "--cutoff",
    type=float,
    default=25.0,
    help="Порог отсечения выбросов в секундах (по умолчанию: 25.0)"
)
parser.add_argument(
    "-f", "--file",
    type=str,
    default=None,
    help="Путь к CSV файлу (по умолчанию: times.csv)"
)
parser.add_argument(
    "extra_args",
    nargs="*",
    help="Свободные аргументы: имя файла или число cutoff"
)

args = parser.parse_args()

# Определение файла и cutoff из аргументов
csv_file = args.file
CUTOFF = args.cutoff

for raw in args.extra_args:
    raw_str = raw.strip()
    lower = raw_str.lower()
    if lower.startswith("cutoff="):
        CUTOFF = float(raw_str.split("=")[1])
    elif lower.endswith(".csv"):
        csv_file = raw_str
    elif raw_str.replace(".", "", 1).isdigit():
        CUTOFF = float(raw_str)

if not csv_file:
    if os.path.exists("times.csv"):
        csv_file = "times.csv"
    else:
        found_csv = glob.glob("*.csv")
        csv_file = found_csv[0] if found_csv else "times.csv"

if not os.path.exists(csv_file):
    print(f"Ошибка: файл '{csv_file}' не найден в текущей папке.")
    sys.exit(1)

# ==========================================
# 1. ЧТЕНИЕ И ПАРСИНГ CSV ФАЙЛА
# ==========================================
try:
    # utf-8-sig прозрачно обрабатывает UTF-8 с BOM и без него
    df_input = pd.read_csv(csv_file, sep=';', encoding='utf-8-sig', dtype=str)
except Exception as e:
    print(f"Ошибка чтения CSV: {e}")
    sys.exit(1)

if 'Time' not in df_input.columns:
    print(f"Ошибка: в файле {csv_file} отсутствует колонка 'Time'.")
    sys.exit(1)

def parse_time_token(token: str):
    """Разбирает время: 19.93, 18.11+, DNF(13.64), DNF, 1:05.12+"""
    token = str(token).strip()
    is_dnf = token.startswith('DNF')
    is_plus2 = token.endswith('+') and not is_dnf
    
    clean_token = token.rstrip('+')
    if is_dnf:
        time_val = np.inf
    elif ':' in clean_token:
        parts = clean_token.split(':')
        time_val = float(parts[0]) * 60 + float(parts[1])
    else:
        try:
            time_val = float(clean_token)
        except ValueError:
            time_val = np.nan
            
    return time_val, is_dnf, is_plus2

parsed = [parse_time_token(t) for t in df_input['Time']]
df_raw = pd.DataFrame(parsed, columns=['Time', 'is_dnf', 'is_plus2'])

# Сохраняем исходный номер сборки из No. или индекса
if 'No.' in df_input.columns:
    df_raw['No'] = df_input['No.'].values
else:
    df_raw['No'] = np.arange(1, len(df_raw) + 1)

total_solves = len(df_raw)

# ==========================================
# 2. РАСЧЕТ WCA TRIMMED MEAN (AoX)
# ==========================================
def compute_wca_rolling_ao(series: pd.Series, window_size: int) -> pd.Series:
    n = window_size
    if len(series) < n:
        return pd.Series(np.nan, index=series.index)
    
    k = 1 if n in (5, 12) else math.ceil(0.05 * n)
    vals = series.to_numpy(dtype=float)
    
    windows = sliding_window_view(vals, window_shape=n)
    sorted_w = np.sort(windows, axis=1)
    
    # Если на позиции n - k - 1 стоит inf, значит число DNF > k
    is_dnf = np.isinf(sorted_w[:, n - k - 1])
    
    trimmed_slice = sorted_w[:, k : n - k]
    means = np.mean(trimmed_slice, axis=1)
    means[is_dnf] = np.nan
    
    result = np.empty(len(vals))
    result[:n - 1] = np.nan
    result[n - 1:] = means
    return pd.Series(result, index=series.index)

windows = [5, 12, 100, 500, 1000]
best_aos = {}
for w in windows:
    col = f'ao{w}'
    if total_solves >= w:
        df_raw[col] = compute_wca_rolling_ao(df_raw['Time'], w)
        val = df_raw[col].min()
        best_aos[f'Ao{w}'] = f"{val:.2f} с" if pd.notna(val) else "DNF"
    else:
        df_raw[col] = None
        best_aos[f'Ao{w}'] = "N/A"

# ==========================================
# 3. СТАТИСТИКА И ПОДГОТОВКА ДАННЫХ
# ==========================================
completed_solves = df_raw[np.isfinite(df_raw['Time'])]
df_clean = completed_solves[completed_solves['Time'] < CUTOFF].copy()

dnf_count = int(df_raw['is_dnf'].sum())
plus2_count = int(df_raw['is_plus2'].sum())
dnf_pct = (dnf_count / total_solves) * 100
plus2_pct = (plus2_count / total_solves) * 100

slow_count = int((completed_solves['Time'] >= CUTOFF).sum())
removed_total = dnf_count + slow_count

pb_single = completed_solves['Time'].min()
worst_single = completed_solves['Time'].max()
mean_single = completed_solves['Time'].mean()
median_single = completed_solves['Time'].median()
std_single = completed_solves['Time'].std()

cutoff_label = f"{int(CUTOFF)}" if CUTOFF.is_integer() else f"{CUTOFF:.1f}"

# Вывод сводки в консоль
print("=" * 55)
print(f"Файл:              {csv_file}")
print(f"Всего попыток:     {total_solves}")
print(f"DNF (незачет):     {dnf_count} ({dnf_pct:.2f}%)")
print(f"Штраф (+2):        {plus2_count} ({plus2_pct:.2f}%)")
print(f"Порог отсечения:   < {cutoff_label} с")
print(f"PB Single:         {pb_single:.2f} с")
print(f"Mean (Single):     {mean_single:.2f} с")
print("=" * 55)

# ==========================================
# 4. ПОСТРОЕНИЕ ДАШБОРДА
# ==========================================
sns.set_theme(style="whitegrid")
fig = plt.figure(figsize=(16, 14))

# hspace=0.45 дает свободное пространство между осями
gs = fig.add_gridspec(3, 1, height_ratios=[1.25, 4.5, 4.5], hspace=0.45)

ax0 = fig.add_subplot(gs[0])
ax1 = fig.add_subplot(gs[1])
ax2 = fig.add_subplot(gs[2])

# --- БЛОК 0: Карточки с метриками ---
ax0.axis('off')

stats_col1 = (
    "ОБЪЕМ ДАННЫХ И ШТРАФЫ\n"
    f"• Файл: {os.path.basename(csv_file)}\n"
    f"• Всего попыток: {total_solves}\n"
    f"• DNF (незачет): {dnf_count} ({dnf_pct:.2f}%)\n"
    f"• Штраф (+2):    {plus2_count} ({plus2_pct:.2f}%)\n"
    f"• Отсеяно (> {cutoff_label}с + DNF): {removed_total} ({removed_total/total_solves*100:.1f}%)"
)

stats_col2 = (
    "ОСНОВНЫЕ МЕТРИКИ (SINGLE)\n"
    f"• PB (Single): {pb_single:.2f} с\n"
    f"• Среднее (Mean): {mean_single:.2f} с\n"
    f"• Медиана: {median_single:.2f} с\n"
    f"• Станд. откл. (σ): {std_single:.2f} с\n"
    f"• Худшее (без DNF): {worst_single:.2f} с"
)

stats_col3 = (
    "ЛУЧШИЕ WCA СРЕДНИЕ (TRIMMED)\n"
    f"• Best Ao5:    {best_aos['Ao5']}\n"
    f"• Best Ao12:   {best_aos['Ao12']}\n"
    f"• Best Ao100:  {best_aos['Ao100']}\n"
    f"• Best Ao500:  {best_aos['Ao500']}\n"
    f"• Best Ao1000: {best_aos['Ao1000']}"
)

box_style = dict(boxstyle='round,pad=0.8', facecolor='#F8FAFC', edgecolor='#CBD5E1', linewidth=1.2)
ax0.text(0.02, 0.5, stats_col1, transform=ax0.transAxes, fontsize=10, va='center', linespacing=1.35, bbox=box_style)
ax0.text(0.35, 0.5, stats_col2, transform=ax0.transAxes, fontsize=10, va='center', linespacing=1.35, bbox=box_style)
ax0.text(0.68, 0.5, stats_col3, transform=ax0.transAxes, fontsize=10, va='center', linespacing=1.35, bbox=box_style, family='monospace')

# --- БЛОК 1: Градиентная гистограмма ---
df_clean['Group'] = df_clean['Time'].astype(int)
min_sec = df_clean['Group'].min()
max_sec = df_clean['Group'].max()
group_counts = df_clean['Group'].value_counts().reindex(range(min_sec, max_sec + 1), fill_value=0)

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

labels = [str(v) if v > 0 else '' for v in group_counts.values]
ax1.bar_label(bars, labels=labels, padding=3, fontsize=9, fontweight='bold', color='#1E293B')

ax1.set_ylim(0, group_counts.max() * 1.12)
ax1.set_title(f'Распределение успешных сборок кубика Рубика 3x3 по секундам (< {cutoff_label} с)', fontsize=12, pad=10, fontweight='bold')
ax1.set_xlabel('Группа времени (секунды)', fontsize=10, labelpad=8)
ax1.set_ylabel('Количество сборок', fontsize=10)
ax1.set_xticks(range(len(group_counts)))
ax1.set_xticklabels([f"{sec}.xx" for sec in group_counts.index], rotation=45, ha='right', fontsize=9)

# --- БЛОК 2: График прогресса WCA Ao ---
solve_numbers = np.arange(1, total_solves + 1)

ax2.plot(solve_numbers, df_raw['Time'], color='#94A3B8', alpha=0.25, linewidth=0.6, label='Сборка (raw)')

trend_styles = [
    ('ao5', 'Ao5', '#F59E0B', 1.0, 0.8),
    ('ao12', 'Ao12', '#EF4444', 1.2, 0.9),
    ('ao100', 'Ao100', '#2563EB', 1.8, 1.0),
    ('ao500', 'Ao500', '#9333EA', 2.2, 1.0),
    ('ao1000', 'Ao1000', '#059669', 2.5, 1.0),
]

for col, label_name, color, lw, alpha in trend_styles:
    if col in df_raw and df_raw[col].notna().any():
        ax2.plot(solve_numbers, df_raw[col], color=color, linewidth=lw, alpha=alpha, label=label_name)

ax2.set_title('Прогресс за всю сессию (Скользящие средние по правилам WCA)', fontsize=12, pad=10, fontweight='bold')
ax2.set_xlabel('Номер сборки (по порядку в сессии)', fontsize=10)
ax2.set_ylabel('Время (сек)', fontsize=10)
ax2.set_ylim(pb_single - 0.5, CUTOFF + 0.5)
ax2.legend(loc='upper right', ncol=6, frameon=True, facecolor='white', framealpha=0.9)

# ==========================================
# 5. СОХРАНЕНИЕ
# ==========================================
output_file = 'speedcubing_stats.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Дашборд сохранен в файл: {output_file}")
