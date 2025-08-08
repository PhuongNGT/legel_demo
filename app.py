from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
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
        "doctrine", "voted_model", 
        "concept_correct", "ending_correct", "limitation_correct", "mcq_total_correct",
        "is_native", "with_story", "error_type", "rod", "ros", 
        "likeable", "believable"
    ]).to_csv(EVAL_PATH, index=False)


@app.route("/")
def index():
    doctrines = df["doctrine"].unique().tolist()
    return render_template("index.html", doctrines=doctrines)


@app.route("/evaluate/<doctrine>", methods=["GET", "POST"])
def evaluate(doctrine):
    rows = df[df["doctrine"] == doctrine]

    # Lấy 3 story từ 3 model khác nhau
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

    # Lấy MCQs từ model đầu tiên có dữ liệu hợp lệ
    mcqs_by_type = {"concept": None, "ending": None, "limitation": None}
    for _, row in rows.iterrows():
        try:
            mcqs = json.loads(row["mcqs_json"])
            for q in mcqs:
                qtype = q.get("type", "").lower()
                if qtype in mcqs_by_type and mcqs_by_type[qtype] is None:
                    mcqs_by_type[qtype] = q
            if all(mcqs_by_type.values()):
                break
        except Exception:
            continue

    if request.method == "POST":
        form = request.form
        voted_model = form.get("voted_model")
        is_native = int(form.get("is_native", 0))
        with_story = int(form.get("with_story", 1))

        # Thu thập đáp án và đáp án đúng
        concept_correct = int(form.get("answer_concept") == form.get("correct_concept"))
        ending_correct = int(form.get("answer_ending") == form.get("correct_ending"))
        limitation_correct = int(form.get("answer_limitation") == form.get("correct_limitation"))
        mcq_total = concept_correct + ending_correct + limitation_correct

        # Ghi dữ liệu
        new_data = {
            "doctrine": doctrine,
            "voted_model": voted_model,
            "concept_correct": concept_correct,
            "ending_correct": ending_correct,
            "limitation_correct": limitation_correct,
            "mcq_total_correct": mcq_total,
            "is_native": is_native,
            "with_story": with_story,
            "error_type": form.get("error_type", ""),
            "rod": float(form.get("rod", 0.0)),
            "ros": float(form.get("ros", 0.0)),
            "likeable": int(form.get("likeable", 0)),
            "believable": int(form.get("believable", 0)),
        }

        df_eval = pd.read_csv(EVAL_PATH)
        df_eval = pd.concat([df_eval, pd.DataFrame([new_data])])
        df_eval.to_csv(EVAL_PATH, index=False)

        os.system("python analyze.py")  # nếu có script phân tích
        return redirect(url_for("result"))

    return render_template(
        "evaluate.html", 
        doctrine=doctrine, 
        stories=stories, 
        mcqs=mcqs_by_type
    )


@app.route("/result")
def result():
    df_eval = pd.read_csv(EVAL_PATH)
    total_votes = len(df_eval)

    # ====== Thống kê số phiếu bầu ======
    model_votes = df_eval["voted_model"].value_counts().to_dict()
    model_votes_pct = df_eval["voted_model"].value_counts(normalize=True).mul(100).round(2).to_dict()

    # ====== Accuracy trung bình từng loại ======
    concept_acc = df_eval["concept_correct"].mean() * 100 if total_votes > 0 else 0
    ending_acc = df_eval["ending_correct"].mean() * 100 if total_votes > 0 else 0
    limitation_acc = df_eval["limitation_correct"].mean() * 100 if total_votes > 0 else 0

    # ====== MCQ Accuracy overall ======
    if total_votes > 0:
        mcq_acc = df_eval[["concept_correct", "ending_correct", "limitation_correct"]].mean().mean() * 100
    else:
        mcq_acc = 0

    # ====== Accuracy tổng hợp theo model ======
    if total_votes > 0:
        model_acc = (
            df_eval.groupby("voted_model")[["concept_correct", "ending_correct", "limitation_correct"]]
            .mean()
            .mean(axis=1)   # lấy trung bình cả 3 loại
            .mul(100)
            .round(2)
            .to_dict()
        )
    else:
        model_acc = {}

    # ====== Lấy ảnh kết quả ======
    plot_folder = "static/plots"
    all_images = [
        f for f in os.listdir(plot_folder)
        if f.endswith(".png") and os.path.isfile(os.path.join(plot_folder, f))
    ]

    return render_template(
        "result.html",
        total_votes=total_votes,
        model_votes=model_votes,
        model_votes_pct=model_votes_pct,
        mcq_acc=round(mcq_acc, 2),
        concept_acc=round(concept_acc, 2),
        ending_acc=round(ending_acc, 2),
        limitation_acc=round(limitation_acc, 2),
        model_acc=model_acc,
        all_images=all_images
    )



if __name__ == "__main__":
    app.run(debug=True)
