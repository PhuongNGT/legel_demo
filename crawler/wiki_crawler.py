import csv
import wikipedia
import os

def load_doctrine_names(csv_path):
    doctrines = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            doctrine = row[0].strip()
            if doctrine and doctrine.lower() != "doctrine":
                doctrines.append(doctrine)
    return doctrines

def crawl_definitions(doctrine_list, output_csv):
    results = []
    for doctrine in doctrine_list:
        try:
            summary = wikipedia.summary(doctrine, auto_suggest=False)
            print(f"[✓] {doctrine}")
            results.append({"doctrine": doctrine, "definition": summary})
        except Exception as e:
            print(f"[✗] Failed: {doctrine} → {e}")
    
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["doctrine", "definition"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

if __name__ == "__main__":
    doctrine_csv = "complex-law-doctrine-list.csv"
    output_path = "../data/legal_doctrines_294.csv"
    doctrine_list = load_doctrine_names(doctrine_csv)
    crawl_definitions(doctrine_list, output_path)

