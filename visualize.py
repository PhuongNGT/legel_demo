import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("outputs/story_evaluation.tsv", sep='\t')

metrics = ["word_count", "flesch_score", "ttr"]

for metric in metrics:
    plt.figure(figsize=(8,6))
    sns.boxplot(x="model", y=metric, data=df)
    plt.title(f"Comparison of {metric} across models")
    plt.savefig(f"outputs/{metric}_comparison.png")
    plt.close()

print("✅ Visualizations saved in outputs/")

