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
    stories = []
    for _, row in rows.iterrows():
        try:
            mcqs = json.loads(row["mcqs_json"])  # dùng đúng tên cột bạn đang lưu
        except Exception:
            mcqs = [{"question": "Error loading MCQs", "options": [], "answer": ""}]
        stories.append({
            "model": row["model"],
            "story": row["story"],
            "mcqs": mcqs
        })
    random.shuffle(stories)

    if request.method == "POST":
        voted_model = request.form.get("voted_model")
        if not voted_model:
            # Không chọn model
            return render_template("evaluate.html", doctrine=doctrine, stories=stories)

        mcq_answer = request.form.get(f"mcq_answer_{voted_model}")
        correct_answer = request.form.get(f"correct_answer_{voted_model}")

        if mcq_answer is None or correct_answer is None:
            # Không chọn đáp án
            return render_template("evaluate.html", doctrine=doctrine, stories=stories)

        mcq_correct = int(mcq_answer == correct_answer)

        df_eval = pd.read_csv(EVAL_PATH)
        df_eval = pd.concat([df_eval, pd.DataFrame([{
            "doctrine": doctrine,
            "voted_model": voted_model,
            "mcq_correct": mcq_correct
        }])])
        df_eval.to_csv(EVAL_PATH, index=False)
        return redirect(url_for("result"))

    # Luôn render trang khi không POST hoặc POST thất bại
    return render_template("evaluate.html", doctrine=doctrine, stories=stories)




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

