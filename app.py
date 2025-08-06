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
    pd.DataFrame(columns=[
        "doctrine", "voted_model", "mcq_correct", "mcq_type", "is_native", 
        "with_story", "error_type", "rod", "ros", "likeable", "believable"
    ]).to_csv(EVAL_PATH, index=False)



@app.route("/")
def index():
    doctrines = df["doctrine"].unique().tolist()
    return render_template("index.html", doctrines=doctrines)


@app.route("/evaluate/<doctrine>", methods=["GET", "POST"])
def evaluate(doctrine):
    rows = df[df["doctrine"] == doctrine]

    # Lấy MCQ duy nhất từ model đầu tiên
    mcq = None
    for _, row in rows.iterrows():
        try:
            mcqs = json.loads(row["mcqs_json"])
            if mcqs:
                mcq = mcqs[0]  # Lấy câu hỏi đầu tiên
                break
        except Exception:
            continue

    # Lấy 3 story từ 3 model khác nhau (nếu có)
    stories = []
    seen_models = set()
    for _, row in rows.iterrows():
        model = row["model"]
        if model not in seen_models:
            stories.append({
                "model": model,
                "story": row["story"]
            })
            seen_models.add(model)
        if len(stories) == 3:
            break

    if request.method == "POST":
        form = request.form
        voted_model = form.get("voted_model")
        mcq_answer = form.get("mcq_answer")
        correct_answer = form.get("correct_answer")

        if not voted_model or mcq_answer is None or correct_answer is None:
            return render_template("evaluate.html", doctrine=doctrine, stories=stories, mcq=mcq)

        mcq_correct = int(mcq_answer == correct_answer)

        # Các trường bổ sung
        new_data = {
            "doctrine": doctrine,
            "voted_model": voted_model,
            "mcq_correct": mcq_correct,
            "mcq_type": form.get("mcq_type"),
            "is_native": int(form.get("is_native")),
            "with_story": int(form.get("with_story")),
            "error_type": form.get("error_type") or "",
            "rod": float(form.get("rod")),
            "ros": float(form.get("ros")),
            "likeable": int(form.get("likeable")),
            "believable": int(form.get("believable")),
        }

        df_eval = pd.read_csv(EVAL_PATH)
        df_eval = pd.concat([df_eval, pd.DataFrame([new_data])])
        df_eval.to_csv(EVAL_PATH, index=False)
        os.system("python analyze.py")
        return redirect(url_for("result"))

    return render_template("evaluate.html", doctrine=doctrine, stories=stories, mcq=mcq)







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

    # Lấy toàn bộ ảnh trong static/plots/
    plot_folder = "static/plots"
    all_images = [
        f for f in os.listdir(plot_folder)
        if f.endswith(".png") and os.path.isfile(os.path.join(plot_folder, f))
    ]

    return render_template(
        "result.html",
        votes=votes,
        votes_pct=votes_pct,
        mcq_acc=mcq_acc,
        total_votes=total_votes,
        model_acc=model_acc,
        all_images=all_images
    )

if __name__ == "__main__":
    app.run(debug=True)

