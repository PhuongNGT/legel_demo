import pandas as pd
import os
from dotenv import load_dotenv
import httpx
from tqdm import tqdm
import json
import re
import matplotlib.pyplot as plt
import seaborn as sns

# ==== Load data ====
df = pd.read_csv("outputs/merged_mcq.tsv", sep="\t")

# ==== Parse mcqs_json ====
def parse_mcq_json(mcq_json):
    try:
        mcqs = json.loads(mcq_json)
        if isinstance(mcqs, dict) and "error" in mcqs:
            return None
        if isinstance(mcqs, list):
            return mcqs
    except:
        return None

df["mcqs"] = df["mcqs_json"].apply(parse_mcq_json)

# ==== Stats ====
n_doctrines = df["doctrine"].nunique()
n_rows = len(df)
n_errors = df["mcqs"].isnull().sum()

valid_counts = df.groupby("model")["mcqs"].apply(lambda x: x.notnull().sum())

def mcq_stats(mcqs):
    if mcqs is None:
        return (0, 0)
    num_q = len(mcqs)
    avg_opts = round(sum(len(q["options"]) for q in mcqs) / num_q, 2) if num_q else 0
    return (num_q, avg_opts)

df[["num_questions", "avg_options"]] = df["mcqs"].apply(lambda x: pd.Series(mcq_stats(x)))
mcq_summary = df.groupby("model")[["num_questions", "avg_options"]].mean().round(2)

# ==== Save CSV ====
summary_csv = "outputs/mcq_summary.csv"
mcq_summary.to_csv(summary_csv)

# ==== Plot ====
plot_path = "outputs/mcq_valid_counts.png"
plt.figure(figsize=(6,4))
sns.barplot(x=valid_counts.index, y=valid_counts.values)
plt.title("Valid MCQs per Model")
plt.ylabel("Valid Samples")
plt.xlabel("Model")
plt.tight_layout()
plt.savefig(plot_path)

# ==== Save Markdown ====
report_md = "outputs/mcq_report.md"
with open(report_md, "w") as f:
    f.write(f"# MCQ Analysis Report\n\n")
    f.write(f"- Total doctrines: **{n_doctrines}**\n")
    f.write(f"- Total samples: **{n_rows}**\n")
    f.write(f"- Invalid MCQs: **{n_errors}**\n\n")
    f.write(f"## Valid MCQs per model\n")
    f.write(valid_counts.to_string())
    f.write("\n\n## Avg questions & options per model\n")
    f.write(mcq_summary.to_string())

print(f"✅ CSV: {summary_csv}")
print(f"✅ PNG: {plot_path}")
print(f"✅ Markdown: {report_md}")

# ==== Save HTML ====
report_html = "outputs/mcq_report.html"
with open(report_html, "w") as f:
    f.write(f"""
<html>
<head>
<title>MCQ Analysis Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
table {{ border-collapse: collapse; }}
th, td {{ border: 1px solid #ddd; padding: 8px; }}
th {{ background-color: #f2f2f2; }}
</style>
</head>
<body>

<h1>MCQ Analysis Report</h1>

<ul>
<li><b>Total doctrines:</b> {n_doctrines}</li>
<li><b>Total samples:</b> {n_rows}</li>
<li><b>Invalid MCQs:</b> {n_errors}</li>
</ul>

<h2>Valid MCQs per model</h2>
<table>
<tr><th>Model</th><th>Valid Samples</th></tr>
""")
    for model, count in valid_counts.items():
        f.write(f"<tr><td>{model}</td><td>{count}</td></tr>\n")
    f.write(f"""
</table>

<h2>Average Questions & Options per model</h2>
<table>
<tr><th>Model</th><th>Avg Questions</th><th>Avg Options</th></tr>
""")
    for model, row in mcq_summary.iterrows():
        f.write(f"<tr><td>{model}</td><td>{row['num_questions']}</td><td>{row['avg_options']}</td></tr>\n")
    f.write(f"""
</table>

<h2>Valid MCQs per Model (Plot)</h2>
<img src="mcq_valid_counts.png" alt="MCQ Valid Counts">

</body>
</html>
""")

print(f"✅ HTML: {report_html}")

