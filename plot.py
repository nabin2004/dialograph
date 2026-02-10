import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# =========================
# Load JSON Data
# =========================
data_file = Path("experiments/summary/metrics_all_runs.json")  # adjust path
with open(data_file) as f:
    data = json.load(f)

# Convert to DataFrame
df = pd.DataFrame(data)

# =========================
# Aggregate Metrics
# =========================
agg_df = df.groupby(["learner", "condition"]).agg(
    mean_confidence=("mean_confidence", "mean"),
    std_confidence=("mean_confidence", "std"),
    mean_retention=("mean_retention", "mean"),
    std_retention=("mean_retention", "std"),
    mean_memory_strength=("mean_memory_strength", "mean"),
    std_memory_strength=("mean_memory_strength", "std"),
    mean_advance_rate=("advance_rate", "mean"),
    std_advance_rate=("advance_rate", "std"),
    mean_misconception_rate=("misconception_rate", "mean"),
    std_misconception_rate=("misconception_rate", "std")
).reset_index()

print("Aggregated Metrics:\n", agg_df)

# =========================
# Visualization Setup
# =========================
sns.set(style="whitegrid")
metrics = ["mean_confidence", "mean_retention", "mean_memory_strength", 
           "mean_advance_rate", "mean_misconception_rate"]

for metric in metrics:
    plt.figure(figsize=(7,5))
    sns.barplot(
        data=agg_df, 
        x="learner", 
        y=metric, 
        hue="condition",
        capsize=0.1
    )
    plt.title(metric.replace("_", " ").title())
    plt.ylabel(metric.replace("_", " ").title())
    plt.xlabel("Learner Type")
    plt.ylim(0, 1.1 if "rate" in metric else None)
    plt.legend(title="Policy Condition")
    plt.tight_layout()
    plt.show()
