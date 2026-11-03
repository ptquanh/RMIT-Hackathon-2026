"""Patch the Wolf notebook to produce a verified test.csv submission."""

import json
from pathlib import Path


NOTEBOOK = Path(__file__).with_name("rmit-mel-segfault-c1-0.97-public.ipynb")
nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))

nb["cells"][0]["source"] = """import os
import inspect
import json
import time
import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
)

NAME = "wolf4"
SEED = 42
LABELS = ["BENIGN", "JAILBREAK", "PROMPT_INJECTION"]
L2I = {label: i for i, label in enumerate(LABELS)}
I2L = {i: label for i, label in enumerate(LABELS)}
SUBMISSION_PATH = "/kaggle/working/submission.csv"

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)

def find_competition_data():
    preferred = "/kaggle/input/competitions/rmit-hackathon-2026"
    if os.path.isfile(f"{preferred}/train.csv") and os.path.isfile(f"{preferred}/test.csv"):
        return preferred
    candidates = [
        root for root, _, files in os.walk("/kaggle/input")
        if "train.csv" in files and "test.csv" in files
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one train/test data directory; found: {candidates}")
    return candidates[0]

def find_wolf_model():
    preferred = "/kaggle/input/models/aisuko/wolf-defender-prompt-injection/transformers/default/1"
    if os.path.isfile(f"{preferred}/config.json"):
        return preferred
    candidates = [
        root for root, _, files in os.walk("/kaggle/input")
        if "config.json" in files and "wolf" in root.lower()
    ]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one approved Wolf model directory; found: {candidates}")
    return candidates[0]

D = find_competition_data()
MODEL = find_wolf_model()
print("Competition data:", D)
print("Approved model:", MODEL)

train = pd.read_csv(f"{D}/train.csv")
test = pd.read_csv(f"{D}/test.csv")
assert {"id", "text", "language", "label"}.issubset(train.columns)
assert {"id", "text", "language"}.issubset(test.columns)
assert len(train) == 14000 and len(test) == 6000
assert train[["id", "text", "language", "label"]].notna().all().all()
assert test[["id", "text", "language"]].notna().all().all()
assert train.id.is_unique and test.id.is_unique
assert set(train.label) == set(LABELS)

train["y"] = train["label"].map(L2I).astype(int)
print(train.groupby(["language", "label"]).size().unstack())
""".splitlines(True)

nb["cells"][1]["source"] = """MAXLEN = 256
tok = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)

class DS(Dataset):
    def __init__(self, texts, labels_y=None):
        self.e = tok(
            list(texts),
            truncation=True,
            max_length=MAXLEN,
        )
        self.y = labels_y

    def __len__(self):
        return len(self.e["input_ids"])

    def __getitem__(self, i):
        item = {key: value[i] for key, value in self.e.items()}
        if self.y is not None:
            item["labels"] = int(self.y[i])
        return item

strat = train["language"].astype(str) + "_" + train["label"].astype(str)
tr, va = train_test_split(
    train,
    test_size=0.1,
    stratify=strat,
    random_state=SEED,
)
tr = tr.reset_index(drop=True)
va = va.reset_index(drop=True)

cnt = np.bincount(tr["y"], minlength=3)
w = torch.tensor((len(tr) / (3 * cnt)) ** 0.5, dtype=torch.float)

class WT(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        y = inputs.pop("labels")
        out = model(**inputs)
        loss = nn.CrossEntropyLoss(weight=w.to(out.logits.device))(out.logits, y)
        return (loss, out) if return_outputs else loss

def metrics(prediction):
    return {
        "macro_f1": f1_score(
            prediction.label_ids,
            prediction.predictions.argmax(1),
            average="macro",
        )
    }

print(
    "Wolf's approved checkpoint has a 2-class classifier. "
    "The 3-class competition head will be freshly initialized and fine-tuned below."
)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL,
    local_files_only=True,
    num_labels=3,
    id2label=I2L,
    label2id=L2I,
    ignore_mismatched_sizes=True,
)

# A unique directory prevents accidental checkpoint reuse from an earlier session.
RUN_DIR = f"/kaggle/working/out_{NAME}_{int(time.time())}"
ta_params = inspect.signature(TrainingArguments.__init__).parameters
args_dict = {
    "output_dir": RUN_DIR,
    "overwrite_output_dir": True,
    "num_train_epochs": 4,
    "per_device_train_batch_size": 16,
    "gradient_accumulation_steps": 2,
    "per_device_eval_batch_size": 64,
    "learning_rate": 3e-5,
    "warmup_steps": 100,
    "weight_decay": 0.01,
    "save_strategy": "epoch",
    "load_best_model_at_end": True,
    "metric_for_best_model": "macro_f1",
    "greater_is_better": True,
    "save_total_limit": 1,
    "fp16": torch.cuda.is_available(),
    "report_to": "none",
    "seed": SEED,
    "data_seed": SEED,
}
if "eval_strategy" in ta_params:
    args_dict["eval_strategy"] = "epoch"
elif "evaluation_strategy" in ta_params:
    args_dict["evaluation_strategy"] = "epoch"
else:
    raise RuntimeError("This Transformers version has no supported evaluation strategy argument.")

unsupported_args = sorted(set(args_dict) - set(ta_params))
if unsupported_args:
    print("Ignoring unsupported TrainingArguments for this Transformers version:", unsupported_args)
args = TrainingArguments(**{key: value for key, value in args_dict.items() if key in ta_params})

t = WT(
    model=model,
    args=args,
    train_dataset=DS(tr["text"], tr["y"].to_numpy()),
    eval_dataset=DS(va["text"], va["y"].to_numpy()),
    data_collator=DataCollatorWithPadding(tok, pad_to_multiple_of=8),
    compute_metrics=metrics,
)

print("Starting real fine-tuning; this should take minutes, not 10 seconds.")
train_started = time.time()
train_result = t.train()
train_seconds = time.time() - train_started
assert train_result.global_step > 0
assert train_result.metrics.get("train_runtime", 0) > 0
print(f"Fine-tuning completed: {train_seconds / 60:.2f} minutes, {train_result.global_step} optimizer steps")
""".splitlines(True)

nb["cells"][2]["cell_type"] = "markdown"
nb["cells"][2]["metadata"] = {}
nb["cells"][2]["source"] = """## Validation and calibration

The following cells evaluate the newly trained model, choose a small validation-only logit bias, then perform inference on every row of `test.csv`.
""".splitlines(True)
nb["cells"][2].pop("execution_count", None)
nb["cells"][2].pop("outputs", None)

nb["cells"][3]["source"] = """pv_output = t.predict(DS(va["text"], va["y"].to_numpy()))
pv = pv_output.predictions
assert len(pv) == len(va) and pv.shape[1] == 3

print(classification_report(
    va["y"],
    pv.argmax(1),
    target_names=LABELS,
    digits=4,
    zero_division=0,
))

for language, group in va.assign(prediction=pv.argmax(1)).groupby("language"):
    print(language, f1_score(group["y"], group["prediction"], average="macro"))

best = (
    f1_score(va["y"], pv.argmax(1), average="macro"),
    np.zeros(3),
)
for b1 in np.arange(-1, 1.01, 0.25):
    for b2 in np.arange(-1, 2.01, 0.25):
        bias = np.array([0, b1, b2])
        score = f1_score(va["y"], (pv + bias).argmax(1), average="macro")
        if score > best[0] + 1e-3:
            best = (score, bias)

print("Best calibrated validation Macro-F1 and bias:", best)
""".splitlines(True)

nb["cells"][4]["source"] = """print(f"Running inference on all {len(test)} rows from test.csv...")
predict_started = time.time()
test_ds = DS(test["text"])
pt_output = t.predict(test_ds)
pt = pt_output.predictions
predict_seconds = time.time() - predict_started

assert len(test_ds) == len(test) == 6000
assert pt.shape == (len(test), 3)
test_pred_ids = (pt + best[1]).argmax(1)

submission = pd.DataFrame({
    "id": test["id"].astype(str).to_numpy(),
    "label": [I2L[int(i)] for i in test_pred_ids],
})

# Strict submission checks: source, row count, order and label vocabulary.
assert submission.columns.tolist() == ["id", "label"]
assert len(submission) == len(test) == 6000
assert submission.id.is_unique
assert submission.id.tolist() == test["id"].astype(str).tolist()
assert submission.notna().all().all()
assert set(submission.label).issubset(set(LABELS))
submission.to_csv(SUBMISSION_PATH, index=False)

np.save(f"/kaggle/working/val_{NAME}.npy", pv)
np.save(f"/kaggle/working/test_{NAME}.npy", pt)
np.save("/kaggle/working/val_y.npy", va["y"].to_numpy())
with open(f"/kaggle/working/run_{NAME}.json", "w", encoding="utf-8") as fp:
    json.dump({
        "model": MODEL,
        "train_rows": len(tr),
        "validation_rows": len(va),
        "test_rows": len(test),
        "max_length": MAXLEN,
        "train_seconds": train_seconds,
        "predict_seconds": predict_seconds,
        "validation_macro_f1": float(best[0]),
        "bias": best[1].tolist(),
    }, fp, indent=2)

reloaded = pd.read_csv(SUBMISSION_PATH, dtype={"id": str})
assert reloaded.id.tolist() == test["id"].astype(str).tolist()
assert reloaded.label.isin(LABELS).all()

print(f"Test inference completed in {predict_seconds:.2f}s")
print("Submission saved:", SUBMISSION_PATH, submission.shape)
print(submission["label"].value_counts(normalize=True))
display(submission.head())
""".splitlines(True)

# Remove stale embedded outputs so Kaggle cannot display old results as if this
# version had just executed them.
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        cell["execution_count"] = None
        cell["outputs"] = []

NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(NOTEBOOK)
