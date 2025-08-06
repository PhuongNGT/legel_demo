from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import random
import os
import json

app = Flask(__name__)

DATA_PATH = "outputs/merged_mcq.tsv"
EVAL_PATH = "data/evaluations.csv"

# Đọc dữ liệu MCQ đã tạo
df = pd.read_csv(DATA_PATH, sep='\t')

# Tạo file đánh giá nếu chưa có
if not os.path.exists(EVAL_PATH):
    pd.DataFrame(columns=["doctrine", "voted_model", "mcq_correct"]).to_csv(EVAL_PATH, index=False)


@app.route("/")
def index():
    doctrines = df["doctrine"].unique().tolist()
    return render_template("index.html", doctrines=doctrines)


@app.route("/evaluate/<doctrine>", methods=["GET", "POST"])
def evaluate(doctrine):
    rows = df[df["doctrine"] == doctrine]

    # Nếu không có mẫu nào thì render lỗi
    if rows.empty:
        return f"No data for doctrine: {doctrine}", 404

    # Chọn ngẫu nhiên 1 dòng để hiển thị
    row = rows.sample(1).iloc[0]

    try:
        mcqs = json.loads(row["mcqs_json"])
    except Exception:
        mcqs = [{"question": "Error loading MCQs", "options": [], "answer": ""}]

    story = {
        "model": row["model"],
        "story": row["story"],
        "mcqs": mcqs
    }

    if request.method == "POST":
        voted_model = request.form.get("voted_model")
        mcq_answer = request.form.get("mcq_answer")
        correct_answer = request.form.get("correct_answer")

        if not voted_model or not mcq_answer or not correct_answer:
            return render_template("evaluate.html", doctrine=doctrine, story=story)

        mcq_correct = int(mcq_answer == correct_answer)

        df_eval = pd.read_csv(EVAL_PATH)
        df_eval = pd.concat([df_eval, pd.DataFrame([{
            "doctrine": doctrine,
            "voted_model": voted_model,
            "mcq_correct": mcq_correct
        }])])
        df_eval.to_csv(EVAL_PATH, index=False)
        return redirect(url_for("result"))

    return render_template("evaluate.html", doctrine=doctrine, story=story)





@app.route("/result")
def result():
    df_eval = pd.read_csv(EVAL_PATH)
    total_votes = len(df_eval)
    votes = df_eval["voted_model"].value_counts().to_dict()
    votes_pct = df_eval["voted_model"].value_counts(normalize=True).mul(100).round(2).to_dict()
    mcq_acc = (df_eval["mcq_correct"].mean() * 100) if total_votes > 0 else 0.0

    model_acc = (
        df_eval.groupby("voted_model")["mcq_correct"]
        .mean()
        .mul(100)
        .round(2)
        .to_dict()
    )

    return render_template(
        "result.html",
        votes=votes,
        votes_pct=votes_pct,
        mcq_acc=mcq_acc,
        total_votes=total_votes,
        model_acc=model_acc
    )


if __name__ == "__main__":
    app.run(debug=True)

