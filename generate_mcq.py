import pandas as pd
import os
from dotenv import load_dotenv
import httpx
from tqdm import tqdm
import json
import re

# ==== Load API ====
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
headers = {"Authorization": f"Bearer {api_key}"}

# Đọc dữ liệu stories đã merge
df = pd.read_csv("outputs/merged_stories.tsv", sep='\t')
rows = []

# Hàm gọi API
def gen_mcq(story):
    prompt = f"""Given the following legal story:

\"\"\"{story}\"\"\"

Write 3 multiple-choice questions (with 4 options each, and mark the correct one) to test understanding of the story and the legal concept it illustrates. Return the result as a JSON array with each question as an object containing 'question', 'options' (list of 4), and 'answer'."""
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a legal teaching assistant."},
            {"role": "user", "content": prompt}
        ]
    }
    resp = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

# Hàm làm sạch JSON từ phản hồi
def clean_json_content(content):
    content = content.strip()
    content = re.sub(r"^```json", "", content, flags=re.IGNORECASE).strip()
    content = re.sub(r"^```", "", content).strip()
    content = re.sub(r"```$", "", content).strip()
    try:
        # Kiểm tra hợp lệ
        json.loads(content)
    except Exception as e:
        return json.dumps({"error": "Invalid JSON returned by model", "raw": content})
    return content

# Sinh MCQ cho từng story của từng model
for _, row in tqdm(df.iterrows(), total=len(df)):
    for model in ["mistral", "llama3", "gpt35"]:
        story = row[f"{model}_story"]
        try:
            mcqs_raw = gen_mcq(story)
            mcqs_clean = clean_json_content(mcqs_raw)
        except Exception as e:
            mcqs_clean = json.dumps({"error": str(e)})

        result_row = {
            "doctrine": row["doctrine"],
            "definition": row["definition"],
            "model": model,
            "story": story,
            "mcqs_json": mcqs_clean
        }
        rows.append(result_row)

        # Hiển thị ngay kết quả vừa xử lý
        print(f"\n✅ Done: {row['doctrine']} | Model: {model}")
        try:
            mcqs_parsed = json.loads(mcqs_clean)
            if isinstance(mcqs_parsed, list) and mcqs_parsed:
                print(f"  Q1: {mcqs_parsed[0]['question']}")
                print(f"  Options: {mcqs_parsed[0]['options']}")
                print(f"  Answer: {mcqs_parsed[0]['answer']}")
            else:
                print(f"  Error/Empty: {mcqs_parsed}")
        except Exception as e:
            print(f"  Failed to parse MCQs: {e}")


# Ghi ra file
pd.DataFrame(rows).to_csv("outputs/merged_mcq.tsv", sep='\t', index=False)
print("\n📋 Sample results:")
for r in rows[:3]:  # chỉ hiển thị 3 dòng đầu
    print(f"\nDoctrine: {r['doctrine']} | Model: {r['model']}")
    try:
        mcqs = json.loads(r["mcqs_json"])
        if isinstance(mcqs, list) and mcqs:
            print(f"Q1: {mcqs[0]['question']}")
            print(f"Options: {mcqs[0]['options']}")
            print(f"Answer: {mcqs[0]['answer']}")
        else:
            print(f"Error or Empty: {mcqs}")
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
print("✅ MCQs generated: outputs/merged_mcq.tsv")

