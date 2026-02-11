import pandas as pd
import re
import matplotlib.pyplot as plt
import os

# ------------------------------
# Parse the .txt file
# ------------------------------
with open("experiments/summary/experiment_report.txt", "r") as f:
    lines = f.readlines()

data = []
current_learner = None
current_condition = None

for line in lines:
    line = line.strip()
    
    if not line:
        continue
    
    m = re.match(r"LEARNER: (\w+)", line)
    if m:
        current_learner = m.group(1)
        continue
    
    m = re.match(r"Condition: (\w+)", line)
    if m:
        current_condition = m.group(1)
        continue
    
    m = re.match(r"(\w+): ([0-9.]+) ± ([0-9.]+)", line)
    if m:
        metric, value, error = m.groups()
        data.append({
            "learner": current_learner,
            "condition": current_condition,
            "metric": metric,
            "value": float(value),
            "error": float(error)
        })

df = pd.DataFrame(data)

# ------------------------------
# Save DataFrame as CSV
# ------------------------------
output_dir = "experiments/summary/output"
os.makedirs(output_dir, exist_ok=True)
csv_path = os.path.join(output_dir, "experiment_metrics.csv")
df.to_csv(csv_path, index=False)
print(f"Data saved to {csv_path}")

# ------------------------------
# Plot mean_confidence
# ------------------------------
df_conf = df[df["metric"] == "mean_confidence"]

plt.figure(figsize=(8,5))
for learner in df_conf['learner'].unique():
    subset = df_conf[df_conf['learner'] == learner]
    plt.bar(subset['condition'] + "_" + learner, subset['value'], yerr=subset['error'], label=learner)

plt.ylabel("Mean Confidence")
plt.title("Mean Confidence per Learner and Condition")
plt.xticks(rotation=45)
plt.tight_layout()

# Save plot as PNG
plot_path = os.path.join(output_dir, "mean_confidence.png")
plt.savefig(plot_path, dpi=300)
print(f"Plot saved to {plot_path}")

plt.show()
