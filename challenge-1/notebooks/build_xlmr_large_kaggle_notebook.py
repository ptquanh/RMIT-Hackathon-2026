"""Build the single-split XLM-R-large Kaggle notebook for 2xT4."""

import json
from pathlib import Path
from textwrap import dedent


OUT = Path(__file__).with_name("fine-tune-xlm-roberta-large-kaggle-2xt4.ipynb")


def cell(kind, source):
    source = dedent(source).strip()
    # Keep top-level statements at column zero in a few cells whose first line
    # is intentionally unindented in the triple-quoted source.
    if kind == "code" and (
        source.startswith("# Load the approved Kaggle model")
        or source.startswith("val_out = trainer.predict")
        or source.startswith("test_out = trainer.predict")
    ):
        lines = source.splitlines()
        if source.startswith("test_out = trainer.predict"):
            source = lines[0] + "\n" + "\n".join(
                line[4:] if line.startswith("    ") else line for line in lines[1:]
            )
        else:
            source = lines[0] + "\n" + dedent("\n".join(lines[1:]))
    result = {"cell_type": kind, "metadata": {}, "source": source.splitlines(True)}
    if kind == "code":
        result.update(execution_count=None, outputs=[])
    return result


cells = [
    cell("markdown", """
    # RMIT Hackathon 2026 · Challenge 1 · XLM-RoBERTa-large · Kaggle 2×T4

    **Approved backbone:** `FacebookAI/xlm-roberta-large` from Kaggle Models, `aisuko/xlm-roberta-large/Transformers/default`. **Maximum sequence length: 384**, matching the tested mmBERT configuration. Uses one stratified 80/20 train/validation split (seed 42), one model, no k-fold and no model blending. Trains with Hugging Face Trainer on both Kaggle T4 GPUs, validates macro-F1, then saves `/kaggle/working/submission.csv` based on `test.csv`.

    In Kaggle, attach the competition dataset and enable both T4 GPUs. For the model, the notebook first uses the normal attached path. If Kaggle reports `ERRORED_MOUNTING_DATASET`, remove XLM-R-large from **Notebook Inputs**, enable Internet, and rerun: the fallback disables Kaggle's shared mount cache and downloads the exact approved model/version over HTTP into `/kaggle/working`. The Trainer detects both visible GPUs. This notebook uses FP16 and gradient checkpointing for the 16-GB-per-GPU T4 memory limit. Effective batch size target: 16 total (4 examples/GPU × 2 GPUs × 2 accumulation steps).
    """),
    cell("code", """
    import os, gc, glob, json, time, random, inspect, warnings
    from pathlib import Path
    import numpy as np
    import pandas as pd
    import torch
    import torch.nn.functional as F
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import f1_score, accuracy_score, classification_report, confusion_matrix
    from scipy.optimize import minimize
    from transformers import (
        AutoConfig, AutoTokenizer, AutoModelForSequenceClassification,
        Trainer, TrainingArguments, EarlyStoppingCallback,
    )

    warnings.filterwarnings("ignore")
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["WANDB_DISABLED"] = "true"

    class CFG:
        SEED = 42
        KAGGLE_MODEL_HANDLE = "aisuko/xlm-roberta-large/Transformers/default/1"
        ATTACHED_MODEL_PATH = "/kaggle/input/models/aisuko/xlm-roberta-large/transformers/default/1"
        HTTP_MODEL_DIR = "/kaggle/working/xlm-roberta-large-model"
        MAX_LENGTH = 384
        LABELS = ["BENIGN", "JAILBREAK", "PROMPT_INJECTION"]
        LABEL2ID = {name: i for i, name in enumerate(LABELS)}
        ID2LABEL = {i: name for i, name in enumerate(LABELS)}
        VAL_SIZE = 0.20
        BATCH_SIZE = 4             # per GPU; effective global batch 16 with 2 GPUs and accumulation=2
        EVAL_BATCH_SIZE = 8        # per GPU
        GRAD_ACCUM = 2
        LR = 2e-5                  # tested mmBERT recipe
        WEIGHT_DECAY = 0.01
        WARMUP_RATIO = 0.10
        EPOCHS = 4
        PATIENCE = 2
        OUTPUT_DIR = "/kaggle/working/xlmr_large_single_split"
        SUBMISSION_PATH = "/kaggle/working/submission.csv"

    assert torch.cuda.is_available(), "Enable GPU in Kaggle notebook settings."
    n_gpu = torch.cuda.device_count()
    print("PyTorch:", torch.__version__, "| GPUs visible:", n_gpu)
    for gpu_i in range(n_gpu):
        print(f"GPU {gpu_i}: {torch.cuda.get_device_name(gpu_i)} · {torch.cuda.get_device_properties(gpu_i).total_memory / 2**30:.1f} GiB")
    assert n_gpu == 2, f"Expected Kaggle 2×T4 runtime; detected {n_gpu} GPU(s). Enable both T4 GPUs."
    assert all("T4" in torch.cuda.get_device_name(i) for i in range(n_gpu)), "This notebook is configured for 2×T4."
    random.seed(CFG.SEED); np.random.seed(CFG.SEED); torch.manual_seed(CFG.SEED); torch.cuda.manual_seed_all(CFG.SEED)
    torch.backends.cuda.matmul.allow_tf32 = True
    """),
    cell("code", """
    # Prefer the standard Kaggle-mounted model, exactly like the working mmBERT notebook.
    # If that model input cannot be mounted, remove it from Notebook Inputs and enable
    # Internet. DISABLE_KAGGLE_CACHE forces KaggleHub's HTTP resolver instead of asking
    # the same failing AttachDatasource/mount service to attach the model again.
    def resolve_model_path():
        if os.path.isdir(CFG.ATTACHED_MODEL_PATH):
            print("Using attached Kaggle Model:", CFG.ATTACHED_MODEL_PATH)
            return CFG.ATTACHED_MODEL_PATH

        os.environ["DISABLE_KAGGLE_CACHE"] = "1"
        os.environ["KAGGLEHUB_CACHE"] = "/kaggle/working/kagglehub-cache"
        try:
            import kagglehub
            downloaded = kagglehub.model_download(
                CFG.KAGGLE_MODEL_HANDLE,
                output_dir=CFG.HTTP_MODEL_DIR,
            )
        except Exception as exc:
            raise RuntimeError(
                "The attached XLM-R-large model is unavailable and HTTP fallback failed. "
                "Remove XLM-R-large from Notebook Inputs, enable Internet, then restart the session."
            ) from exc
        print("Downloaded approved Kaggle Model over HTTP:", downloaded)
        return downloaded

    model_path = resolve_model_path()
    assert os.path.isdir(model_path), f"Resolved model directory does not exist: {model_path}"
    model_config = AutoConfig.from_pretrained(model_path, local_files_only=True)
    assert model_config.model_type == "xlm-roberta" and model_config.hidden_size == 1024, (
        f"Expected XLM-R-large, got {model_config.model_type}/{model_config.hidden_size}"
    )

    def find_csv(name):
        matches = glob.glob(f"/kaggle/input/**/{name}", recursive=True)
        if not matches:
            raise FileNotFoundError(f"{name} not found under /kaggle/input. Attach the competition dataset.")
        # Prefer exact competition directory if Kaggle exposes the standard path.
        exact = [p for p in matches if "rmit-hackathon-2026" in p.lower()]
        return exact[0] if exact else matches[0]

    train_path, test_path = find_csv("train.csv"), find_csv("test.csv")
    train_df, test_df = pd.read_csv(train_path), pd.read_csv(test_path)
    assert {"id", "text", "label"}.issubset(train_df.columns)
    assert {"id", "text"}.issubset(test_df.columns)
    assert train_df[["id", "text", "label"]].notna().all().all()
    assert test_df[["id", "text"]].notna().all().all()
    assert train_df.id.is_unique and test_df.id.is_unique
    assert set(train_df.label) == set(CFG.LABELS)
    if "language" in train_df.columns:
        strata = train_df.label.astype(str) + "_" + train_df.language.astype(str)
    else:
        strata = train_df.label.astype(str)
    train_df["label_id"] = train_df.label.map(CFG.LABEL2ID).astype(int)
    train_part, val_part = train_test_split(
        train_df, test_size=CFG.VAL_SIZE, random_state=CFG.SEED, stratify=strata
    )
    train_part = train_part.reset_index(drop=True)
    val_part = val_part.reset_index(drop=True)
    print("Train/test:", train_df.shape, test_df.shape, "| split:", len(train_part), len(val_part))
    print("Train labels:\\n", train_part.label.value_counts(normalize=True).sort_index())
    print("Validation labels:\\n", val_part.label.value_counts(normalize=True).sort_index())
    """),
    cell("code", """
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, use_fast=True)

    def tokenize_frame(frame, with_labels=False):
        # Fixed 384-token truncation/padding reproduces the validated sequence-length setting.
        encoded = tokenizer(
            frame.text.fillna("").astype(str).tolist(),
            truncation=True, padding="max_length", max_length=CFG.MAX_LENGTH,
        )
        result = {"input_ids": encoded["input_ids"], "attention_mask": encoded["attention_mask"]}
        if with_labels:
            result["labels"] = frame.label_id.tolist()
        return HFDataset.from_dict(result)

    from datasets import Dataset as HFDataset
    train_ds = tokenize_frame(train_part, with_labels=True)
    val_ds = tokenize_frame(val_part, with_labels=True)
    test_ds = tokenize_frame(test_df, with_labels=False)
    print("Tokenized datasets:", len(train_ds), len(val_ds), len(test_ds), "| max_length:", CFG.MAX_LENGTH)
    """),
    cell("code", """
    class WeightedTrainer(Trainer):
        def __init__(self, class_weights=None, **kwargs):
            super().__init__(**kwargs)
            self.class_weights = class_weights

        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs["labels"]
            outputs = model(**{k: v for k, v in inputs.items() if k != "labels"})
            loss = F.cross_entropy(outputs.logits.float(), labels, weight=self.class_weights.to(outputs.logits.device))
            return (loss, outputs) if return_outputs else loss

    def compute_metrics(eval_pred):
        logits = eval_pred.predictions[0] if isinstance(eval_pred.predictions, tuple) else eval_pred.predictions
        preds = np.argmax(logits, axis=-1)
        return {"macro_f1": f1_score(eval_pred.label_ids, preds, labels=[0, 1, 2], average="macro", zero_division=0),
                "accuracy": accuracy_score(eval_pred.label_ids, preds)}

    counts = np.bincount(train_part.label_id.to_numpy(), minlength=3)
    class_weights = torch.tensor((counts[0] / counts) ** 0.5, dtype=torch.float32)
    print("Class counts:", counts, "| inverse-sqrt weights:", class_weights.tolist())
    model = AutoModelForSequenceClassification.from_pretrained(
        model_path, local_files_only=True, num_labels=3,
        id2label=CFG.ID2LABEL, label2id=CFG.LABEL2ID, ignore_mismatched_sizes=True,
    )
    model.config.use_cache = False
    ta_params = inspect.signature(TrainingArguments.__init__).parameters
    args_dict = dict(
        output_dir=CFG.OUTPUT_DIR, overwrite_output_dir=True,
        learning_rate=CFG.LR, weight_decay=CFG.WEIGHT_DECAY,
        per_device_train_batch_size=CFG.BATCH_SIZE,
        per_device_eval_batch_size=CFG.EVAL_BATCH_SIZE,
        gradient_accumulation_steps=CFG.GRAD_ACCUM,
        num_train_epochs=CFG.EPOCHS, warmup_ratio=CFG.WARMUP_RATIO,
        fp16=True, gradient_checkpointing=True,
        dataloader_num_workers=2, dataloader_pin_memory=True,
        logging_steps=50, save_strategy="epoch", save_total_limit=2,
        load_best_model_at_end=True, metric_for_best_model="macro_f1", greater_is_better=True,
        report_to="none", seed=CFG.SEED, data_seed=CFG.SEED,
        ddp_find_unused_parameters=False,
    )
    args_dict["eval_strategy" if "eval_strategy" in ta_params else "evaluation_strategy"] = "epoch"
    args_dict = {k: v for k, v in args_dict.items() if k in ta_params}
    training_args = TrainingArguments(**args_dict)
    """),
    cell("code", """
    # Trainer sees both GPUs and uses the available multi-GPU backend in Kaggle.
    trainer_params = inspect.signature(Trainer.__init__).parameters
    trainer_kwargs = dict(
        model=model, args=training_args, train_dataset=train_ds, eval_dataset=val_ds,
        compute_metrics=compute_metrics, class_weights=class_weights,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=CFG.PATIENCE)],
    )
    if "processing_class" in trainer_params:
        trainer_kwargs["processing_class"] = tokenizer
    elif "tokenizer" in trainer_params:
        trainer_kwargs["tokenizer"] = tokenizer
    trainer = WeightedTrainer(**trainer_kwargs)
    print("Trainer GPU count:", trainer.args.n_gpu, "| effective train batch:",
          CFG.BATCH_SIZE * trainer.args.n_gpu * CFG.GRAD_ACCUM)
    assert trainer.args.n_gpu == 2, "Trainer is not using both Kaggle GPUs."
    torch.cuda.reset_peak_memory_stats()
    start = time.time()
    train_result = trainer.train()
    elapsed_min = round((time.time() - start) / 60, 2)
    peak_gb = torch.cuda.max_memory_allocated() / 2**30
    print(f"Training done in {elapsed_min} min; process peak allocated VRAM={peak_gb:.2f} GiB")
    best_model_dir = "/kaggle/working/xlmr_large_best"
    trainer.save_model(best_model_dir)
    tokenizer.save_pretrained(best_model_dir)
    """),
    cell("code", """
    val_out = trainer.predict(val_ds)
    val_logits = val_out.predictions[0] if isinstance(val_out.predictions, tuple) else val_out.predictions
    val_labels = val_out.label_ids
    raw_pred = val_logits.argmax(axis=1)
    raw_f1 = f1_score(val_labels, raw_pred, average="macro", zero_division=0)
    print("Validation macro-F1 (argmax):", round(raw_f1, 6))
    print(classification_report(val_labels, raw_pred, target_names=CFG.LABELS, digits=4, zero_division=0))
    print("Confusion matrix:\\n", confusion_matrix(val_labels, raw_pred))

    # Small logit-bias optimization on the held-out validation split only.
    def bias_objective(bias_free):
        bias = np.r_[0.0, bias_free]
        return -f1_score(val_labels, (val_logits + bias).argmax(axis=1), labels=[0, 1, 2], average="macro", zero_division=0)
    opt = minimize(bias_objective, np.zeros(2), method="Powell", options={"maxiter": 150, "ftol": 1e-5})
    best_bias = np.r_[0.0, opt.x]
    tuned_f1 = -bias_objective(opt.x)
    final_bias = best_bias if tuned_f1 > raw_f1 else np.zeros(3)
    print("Validation macro-F1 with bias:", round(tuned_f1, 6), "| applied:", bool(tuned_f1 > raw_f1), "| bias:", final_bias)
    """),
    cell("code", """
    test_out = trainer.predict(test_ds)
    test_logits = test_out.predictions[0] if isinstance(test_out.predictions, tuple) else test_out.predictions
    test_pred = (test_logits + final_bias).argmax(axis=1)
    submission = pd.DataFrame({"id": test_df.id.astype(str), "label": [CFG.ID2LABEL[int(i)] for i in test_pred]})
    assert submission.columns.tolist() == ["id", "label"]
    assert len(submission) == len(test_df) == 6000
    assert submission.id.is_unique and submission.id.tolist() == test_df.id.astype(str).tolist()
    assert submission.notna().all().all() and set(submission.label).issubset(CFG.LABELS)
    submission.to_csv(CFG.SUBMISSION_PATH, index=False)
    pd.DataFrame({"id": val_part.id.astype(str), "label": val_part.label,
                  **{f"logit_{name}": val_logits[:, i] for i, name in enumerate(CFG.LABELS)}}).to_csv(
                      "/kaggle/working/xlmr_large_validation_logits.csv", index=False)
    run_meta = {
        "model": "aisuko/xlm-roberta-large/Transformers/default", "max_length": CFG.MAX_LENGTH,
        "validation": "stratified 80/20, seed 42", "kfold": False,
        "gpus": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
        "per_device_train_batch": CFG.BATCH_SIZE, "gradient_accumulation": CFG.GRAD_ACCUM,
        "validation_macro_f1_argmax": float(raw_f1), "validation_macro_f1_bias": float(tuned_f1),
        "bias_applied": bool(tuned_f1 > raw_f1), "bias": final_bias.tolist(),
        "train_minutes": elapsed_min, "peak_allocated_gib": round(float(peak_gb), 2),
    }
    Path("/kaggle/working/xlmr_large_run.json").write_text(json.dumps(run_meta, indent=2), encoding="utf-8")
    print("Saved:", CFG.SUBMISSION_PATH, "| prediction counts:\\n", submission.label.value_counts())
    display(submission.head())
    """),
]

for i, item in enumerate(cells):
    item["id"] = f"xlmr-kaggle-{i:02d}"

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
OUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(OUT)
