# analyze.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Cấu hình
EVAL_PATH = "data/evaluations.csv"
PLOT_DIR = "static/plots"
os.makedirs(PLOT_DIR, exist_ok=True)

df = pd.read_csv(EVAL_PATH)

# =========================
# FIGURE 1: Vote bar chart
# =========================
vote_counts = df["voted_model"].value_counts().sort_index()
sns.barplot(x=vote_counts.index, y=vote_counts.values)
plt.title("Vote Distribution by Model")
plt.ylabel("Vote Count")
plt.xlabel("Model")
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/votes.png")
plt.clf()

# ============================
# FIGURE 2: MCQ Accuracy chart
# ============================
acc_per_model = df.groupby("voted_model")["mcq_correct"].mean().mul(100).sort_index()
sns.barplot(x=acc_per_model.index, y=acc_per_model.values)
plt.title("MCQ Accuracy per Model")
plt.ylabel("Accuracy (%)")
plt.xlabel("Model")
plt.ylim(0, 100)
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/accuracy.png")
plt.clf()

# ==============================
# FIGURE 3: Likeable / Believable
# ==============================
for col in ["likeable", "believable"]:
    if col in df.columns:
        model_group = df.groupby("voted_model")[col].mean().sort_index()
        sns.barplot(x=model_group.index, y=model_group.values)
        plt.title(f"{col.capitalize()} Score per Model")
        plt.ylabel("Average Score")
        plt.xlabel("Model")
        plt.tight_layout()
        plt.savefig(f"{PLOT_DIR}/{col}.png")
        plt.clf()

# ==============================
# FIGURE 4: ROD / ROS charts
# ==============================
for col in ["rod", "ros"]:
    if col in df.columns:
        model_group = df.groupby("voted_model")[col].mean().sort_index()
        sns.barplot(x=model_group.index, y=model_group.values)
        plt.title(f"{col.upper()} Rate per Model")
        plt.ylabel("Proportion")
        plt.xlabel("Model")
        plt.tight_layout()
        plt.savefig(f"{PLOT_DIR}/{col}.png")
        plt.clf()
# ==============================
# FIGURE 5: Has Issues vs No Issues per MCQ Type
# ==============================
if "mcq_type" in df.columns and "error_type" in df.columns:
    df_issue = df.copy()
    df_issue["has_issue"] = df_issue["error_type"].apply(lambda x: x.strip().lower() != "none" and x.strip() != "")

    issue_summary = (
        df_issue.groupby(["mcq_type", "voted_model"])["has_issue"]
        .value_counts(normalize=True)
        .unstack(fill_value=0)
        .rename(columns={False: "No Issue", True: "Has Issues"})
        .reset_index()
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    issue_pivot = issue_summary.pivot(index="voted_model", columns="mcq_type", values="Has Issues")

    for i, col in enumerate(issue_pivot.columns):
        issue_part = issue_pivot[col]
        no_issue_part = 1 - issue_part
        bar1 = ax.barh(issue_part.index, no_issue_part, left=0.0, label='No Issue' if i == 0 else "")
        bar2 = ax.barh(issue_part.index, issue_part, left=no_issue_part, label='Has Issues' if i == 0 else "")

    ax.set_title("Issue Rate per MCQ Type")
    ax.set_xlabel("Proportion")
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/mcq_issues_stacked.png")
    plt.clf()
# ==============================
# FIGURE 6: Error Type Distribution per MCQ Type
# ==============================
if "mcq_type" in df.columns and "error_type" in df.columns:
    filtered_df = df[df["error_type"].notna() & (df["error_type"].str.strip() != "none") & (df["error_type"].str.strip() != "")]

    error_counts = (
        filtered_df.groupby(["mcq_type", "voted_model", "error_type"])
        .size()
        .reset_index(name="count")
    )

    error_pivot = error_counts.pivot_table(index=["mcq_type", "voted_model"], columns="error_type", values="count", fill_value=0)
    error_pivot_pct = error_pivot.div(error_pivot.sum(axis=1), axis=0)

    for (mcq_type, model), row in error_pivot_pct.iterrows():
        row.plot(kind="bar", stacked=True, title=f"Error Distribution - {mcq_type} - {model}")
        plt.ylabel("Proportion")
        plt.ylim(0, 1)
        plt.tight_layout()
        safe_mcq = mcq_type.replace("/", "_")
        plt.savefig(f"{PLOT_DIR}/error_dist_{safe_mcq}_{model}.png")
        plt.clf()
# ==============================
# TABLE 1: Accuracy by MCQ Type, Native, and Story
# ==============================
if {"mcq_type", "is_native", "with_story", "mcq_correct"}.issubset(df.columns):
    acc_table = (
        df.groupby(["is_native", "with_story", "mcq_type"])["mcq_correct"]
        .mean()
        .mul(100)
        .round(2)
        .unstack(level=2)
    )
    acc_table.to_csv(f"{PLOT_DIR}/accuracy_by_group.csv")
    
