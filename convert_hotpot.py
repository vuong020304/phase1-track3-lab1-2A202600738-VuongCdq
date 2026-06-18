import json
import random
from pathlib import Path


def convert(input_path: str, output_path: str, n_samples: int = 120):
    raw = json.loads(Path(input_path).read_text(encoding="utf-8"))
    samples = random.sample(raw, min(n_samples, len(raw)))

    result = []
    for item in samples:
        context = []
        for title, sentences in item["context"]:
            context.append({
                "title": title,
                "text": " ".join(sentences)
            })
        result.append({
            "qid": item["_id"],
            "difficulty": "medium",
            "question": item["question"],
            "gold_answer": item["answer"],
            "context": context
        })

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"Converted {len(result)} samples to {output_path}")


if __name__ == "__main__":
    convert(
        "data/hotpot_dev_distractor_v1.json",
        "data/hotpot_processed.json",
        n_samples=120
    )
