#!/usr/bin/env python3

import csv
import sys

def format_time(ms):
    if ms < 1000:
        return f"{ms:.0f}ms"
    elif ms < 10000:
        return f"{ms/1000:.2f}s"
    else:
        return f"{ms/1000:.1f}s"

def get_color(value, threshold_good, threshold_warn):
    if value <= threshold_good:
        return "\033[92m"
    elif value <= threshold_warn:
        return "\033[93m"
    else:
        return "\033[91m"

def print_results_table(csv_file, test_case="CP010"):
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        print("No hay datos en el archivo")
        return
    
    row = rows[0]
    
    print("\n" + "="*80)
    print(f"📊 RESULTADOS DE LA PRUEBA DE CARGA - {test_case}")
    print("="*80)
    print()
    
    print("┌" + "─"*78 + "┐")
    print("│ " + "MÉTRICAS PRINCIPALES".center(76) + "│")
    print("├" + "─"*78 + "┤")
    
    req_count = int(float(row['Request Count']))
    failures = int(float(row['Failure Count']))
    avg_time = float(row['Average Response Time'])
    min_time = float(row['Min Response Time'])
    max_time = float(row['Max Response Time'])
    median_time = float(row['Median Response Time'])
    req_per_sec = float(row['Requests/s'])
    failure_rate = (failures / req_count * 100) if req_count > 0 else 0
    
    print(f"│ {'Total de Requests:':<30} {req_count:>45} │")
    print(f"│ {'Requests Fallidas:':<30} {failures:>45} │")
    print(f"│ {'Tasa de Error:':<30} {failure_rate:.2f}%{' '*(43-len(f'{failure_rate:.2f}%'))} │")
    print(f"│ {'Requests por Segundo:':<30} {req_per_sec:.2f} req/s{' '*(38-len(f'{req_per_sec:.2f} req/s'))} │")
    print("├" + "─"*78 + "┤")
    
    if test_case == "CP010":
        avg_color = get_color(avg_time, 5000, 10000)
        max_color = get_color(max_time, 10000, 15000)
        median_color = get_color(median_time, 5000, 10000)
        avg_threshold = 5000
        max_threshold = 10000
    elif test_case == "CP011":
        avg_color = get_color(avg_time, 3000, 6000)
        max_color = get_color(max_time, 6000, 10000)
        median_color = get_color(median_time, 3000, 6000)
        avg_threshold = 3000
        max_threshold = 6000
    elif test_case == "CP012":
        avg_color = get_color(avg_time, 6000, 10000)
        max_color = get_color(max_time, 10000, 15000)
        median_color = get_color(median_time, 6000, 10000)
        avg_threshold = 6000
        max_threshold = 10000
    elif test_case == "CP013":
        avg_color = get_color(avg_time, 15000, 20000)
        max_color = get_color(max_time, 20000, 30000)
        median_color = get_color(median_time, 15000, 20000)
        avg_threshold = 15000
        max_threshold = 20000
    else:
        avg_color = get_color(avg_time, 5000, 10000)
        max_color = get_color(max_time, 10000, 15000)
        median_color = get_color(median_time, 5000, 10000)
        avg_threshold = 5000
        max_threshold = 10000
    
    print(f"│ {'Tiempo Promedio:':<30} {avg_color}{format_time(avg_time):>10}\033[0m{' '*(35)} │")
    print(f"│ {'Tiempo Mediano (50%):':<30} {median_color}{format_time(median_time):>10}\033[0m{' '*(35)} │")
    print(f"│ {'Tiempo Mínimo:':<30} {format_time(min_time):>10}{' '*(35)} │")
    print(f"│ {'Tiempo Máximo:':<30} {max_color}{format_time(max_time):>10}\033[0m{' '*(35)} │")
    print("└" + "─"*78 + "┘")
    
    print()
    print("┌" + "─"*78 + "┐")
    print("│ " + "PERCENTILES DE TIEMPO DE RESPUESTA".center(76) + "│")
    print("├" + "─"*78 + "┤")
    
    percentiles = {
        '50%': float(row['50%']),
        '66%': float(row['66%']),
        '75%': float(row['75%']),
        '80%': float(row['80%']),
        '90%': float(row['90%']),
        '95%': float(row['95%']),
        '98%': float(row['98%']),
        '99%': float(row['99%']),
        '99.9%': float(row['99.9%']),
        '100%': float(row['100%'])
    }
    
    for pct, value in percentiles.items():
        color = get_color(value, avg_threshold, max_threshold)
        print(f"│ {pct:>6} {'de requests responden en:':<30} {color}{format_time(value):>10}\033[0m{' '*(27)} │")
    
    print("└" + "─"*78 + "┘")
    
    print()
    print("┌" + "─"*78 + "┐")
    print(f"│ " + f"EVALUACIÓN DE UMBRALES ({test_case})".center(76) + "│")
    print("├" + "─"*78 + "┤")
    
    if test_case == "CP010":
        avg_ok = avg_time <= 5000
        max_ok = max_time <= 10000
        error_ok = failure_rate < 1.0
        avg_label = "Tiempo promedio ≤ 5s:"
        max_label = "Tiempo máximo ≤ 10s:"
    elif test_case == "CP011":
        avg_ok = avg_time <= 3000
        max_ok = max_time <= 6000
        error_ok = failure_rate < 1.0
        avg_label = "Tiempo promedio ≤ 3s:"
        max_label = "Tiempo máximo ≤ 6s:"
    elif test_case == "CP012":
        avg_ok = avg_time <= 6000
        max_ok = max_time <= 10000
        error_ok = failure_rate < 1.0
        avg_label = "Tiempo promedio ≤ 6s:"
        max_label = "Tiempo máximo:"
    elif test_case == "CP013":
        avg_ok = avg_time <= 15000
        max_ok = max_time <= 20000
        error_ok = failure_rate < 1.0
        avg_label = "Tiempo promedio ≤ 15s:"
        max_label = "Tiempo máximo:"
    else:
        avg_ok = avg_time <= 5000
        max_ok = max_time <= 10000
        error_ok = failure_rate < 1.0
        avg_label = "Tiempo promedio ≤ 5s:"
        max_label = "Tiempo máximo ≤ 10s:"
    
    error_status = "✅ CUMPLE" if error_ok else "❌ NO CUMPLE"
    avg_status = "✅ CUMPLE" if avg_ok else "❌ NO CUMPLE"
    max_status = "✅ CUMPLE" if max_ok else "❌ NO CUMPLE"
    
    avg_color = "\033[92m" if avg_ok else "\033[91m"
    max_color = "\033[92m" if max_ok else "\033[91m"
    error_color = "\033[92m" if error_ok else "\033[91m"
    
    print(f"│ {avg_label:<30} {avg_color}{avg_status:>15}\033[0m ({format_time(avg_time)}){' '*(23)} │")
    print(f"│ {max_label:<30} {max_color}{max_status:>15}\033[0m ({format_time(max_time)}){' '*(23)} │")
    print(f"│ {'Tasa de error < 1%:':<30} {error_color}{error_status:>15}\033[0m ({failure_rate:.2f}%){' '*(25)} │")
    print("└" + "─"*78 + "┘")
    
    print()
    all_ok = avg_ok and max_ok and error_ok
    if all_ok:
        print("\033[92m✅ TODOS LOS UMBRALES SE CUMPLEN\033[0m")
    else:
        print("\033[91m❌ ALGUNOS UMBRALES NO SE CUMPLEN\033[0m")
    print()

if __name__ == '__main__':
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'results_stats.csv'
    test_case = sys.argv[2] if len(sys.argv) > 2 else 'CP010'
    try:
        print_results_table(csv_file, test_case)
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {csv_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

