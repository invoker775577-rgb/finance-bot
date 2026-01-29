import matplotlib.pyplot as plt
import io

plt.switch_backend('Agg')

def create_pie_chart(stats, currency_symbol="$"):
    # Сортируем
    sorted_stats = dict(sorted(stats.items(), key=lambda item: item[1], reverse=True))
    
    labels = list(sorted_stats.keys())
    values = list(sorted_stats.values())
    
    colors = plt.cm.tab20(range(len(labels)))
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    def make_autopct(pct):
        return f'{pct:.1f}%'

    wedges, texts, autotexts = ax.pie(
        values, 
        autopct=make_autopct,
        startangle=140, 
        colors=colors,
        pctdistance=0.85,
        explode=[0.02]*len(labels),
        wedgeprops=dict(width=0.6, edgecolor='w')
    )
    
    plt.setp(autotexts, size=9, weight="bold", color="black")
    
    # Вставляем символ валюты в легенду
    legend_labels = [f"{l}: {v} {currency_symbol}" for l, v in zip(labels, values)]
    
    ax.legend(wedges, legend_labels,
              title="Расходы",
              loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1),
              fontsize=10)
    
    ax.set_title(f"Структура расходов ({currency_symbol})", fontsize=16, fontweight='bold')
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    plt.close(fig)
    
    return buffer