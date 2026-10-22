"""Build the standalone Colab notebook for XLM-RoBERTa-large."""

import json
from pathlib import Path
from textwrap import dedent


OUT = Path(__file__).with_name("fine-tune-xlm-roberta-large-a100.ipynb")


def markdown(source):
    return {"cell_type": "markdown", "metadata": {}, "source": dedent(source).strip().splitlines(True)}


def code(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": dedent(source).strip().splitlines(True),
    }


cells = [
    markdown("""
    # RMIT Hackathon 2026 · Challenge 1 · XLM-RoBERTa-large on A100

    **Approved pretrained backbone:** `FacebookAI/xlm-roberta-large` downloaded from Kaggle Models using `aisuko/xlm-roberta-large/Transformers/default`.  
    **Metric:** 3-class macro F1. **Output:** `/content/submission.csv` plus aligned OOF/test probabilities, backed up to Google Drive.

    This is a standalone Colab notebook. Put the competition CSVs in the configured Google Drive data folder, add a Colab Secret named `KAGGLE_API_TOKEN` if Kaggle requires authentication, select **A100 GPU**, then Run All. The backbone is fetched from the approved Kaggle Model (not Hugging Face). Rename the Kaggle notebook to the required `<university>_<campus>_<team>_C1` pattern before submitting. It trains five language×label-stratified folds, averages their test probabilities, and uses `test.csv` to write a valid submission. `PROMPT_INJECTION` is rare (7%); inverse-square-root class weighting matches the proven mmBERT and Wolf baselines, while class-bias adjustment is accepted only when cross-fitted OOF improves. Public score is based on 30% of test data, so a higher public score is not guaranteed.

    The existing mmBERT notebook uses seed 42 and a stratified 80/20 split. This notebook uses the same seed but full OOF; compare its fold 1 metrics with mmBERT only as a rough signal, not a strict paired test. A fair model comparison requires matching fold indices and saved probabilities.
    """),
    code("""
    # Colab package setup (run once per fresh runtime)
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-U", "transformers", "accelerate", "sentencepiece", "kagglehub"])
    """),
    code("""
    # 1. Configuration, Google Drive and A100 environment
    import gc
    import inspect
    import json
    import os
    import random
    import shutil
    import time
    from pathlib import Path

    import numpy as np
    import pandas as pd
    import torch
    import torch.nn.functional as F
    from sklearn.metrics import classification_report, confusion_matrix, f1_score
    from sklearn.model_selection import StratifiedKFold
    from torch.utils.data import Dataset
    from transformers import (
        AutoConfig, AutoModelForSequenceClassification, AutoTokenizer,
        DataCollatorWithPadding, EarlyStoppingCallback, Trainer, TrainingArguments,
    )

    from google.colab import drive
    drive.mount("/content/drive")

    # CPU tokenization uses multiple threads; the small CSVs and tokenized rows remain cached in RAM.
    os.environ["TOKENIZERS_PARALLELISM"] = "true"
    os.environ["WANDB_DISABLED"] = "true"

    class CFG:
        KAGGLE_MODEL_HANDLE = "aisuko/xlm-roberta-large/Transformers/default"
        DATA_CANDIDATES = [
            Path("/content/drive/MyDrive/RMIT-Hackathon-2026/challenge-1/data/input/rmit-hackathon-2026"),
            Path("/content/drive/MyDrive/rmit-hackathon-2026"),
            Path("/content/data/rmit-hackathon-2026"),
            Path("/content"),
        ]
        LABELS = ["BENIGN", "JAILBREAK", "PROMPT_INJECTION"]
        LABEL2ID = {name: i for i, name in enumerate(LABELS)}
        ID2LABEL = {i: name for i, name in enumerate(LABELS)}
        SEED = 42
        N_FOLDS = 5
        MAX_LENGTH = 512
        EPOCHS = 4
        LR = 1.5e-5
        WEIGHT_DECAY = 0.01
        CLASS_WEIGHT_POWER = 0.5  # same inverse-square-root recipe as mmBERT and Wolf baselines
        OUTPUT = Path("/content")
        DRIVE_OUTPUT = Path("/content/drive/MyDrive/RMIT-Hackathon-2026/outputs/xlmr-large")

    assert torch.cuda.is_available(), "In Colab, select Runtime > Change runtime type > A100 GPU."
    gpu_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / 2**30
    assert "A100" in gpu_name, f"This configuration targets A100; detected {gpu_name}."
    # On the target 80-GiB A100, use a larger physical batch and avoid activation
    # recomputation. Smaller configurations remain available for lower-memory A100s.
    CFG.TRAIN_BATCH = 32 if vram_gb >= 70 else (16 if vram_gb >= 35 else 8)
    CFG.EVAL_BATCH = min(64, CFG.TRAIN_BATCH * 2)
    CFG.GRAD_ACCUM = 1
    CFG.BF16 = torch.cuda.is_bf16_supported()
    assert CFG.BF16, "A100 should support BF16; check CUDA/PyTorch runtime."
    torch.backends.cuda.matmul.allow_tf32 = True
    if hasattr(torch.backends.cudnn, "allow_tf32"):
        torch.backends.cudnn.allow_tf32 = True
    random.seed(CFG.SEED)
    np.random.seed(CFG.SEED)
    torch.manual_seed(CFG.SEED)
    torch.cuda.manual_seed_all(CFG.SEED)
    print(f"GPU: {gpu_name} · {vram_gb:.1f} GiB · BF16 · train batch={CFG.TRAIN_BATCH} · eval batch={CFG.EVAL_BATCH} · grad accumulation={CFG.GRAD_ACCUM}")
    """),
    code("""
    # 2. Download the approved Kaggle Model and load train.csv / test.csv from Drive
    import kagglehub

    def resolve_model():
        # KaggleHub reads KAGGLE_API_TOKEN from Colab Secrets automatically when present.
        # Public model downloads may work without a token; if auth is required, add the Secret and rerun.
        return kagglehub.model_download(CFG.KAGGLE_MODEL_HANDLE)

    def resolve_data():
        for p in CFG.DATA_CANDIDATES:
            if (p / "train.csv").exists() and (p / "test.csv").exists():
                return p
        raise FileNotFoundError("Attach the RMIT Hackathon 2026 competition data.")

    model_path = resolve_model()
    model_cfg = AutoConfig.from_pretrained(model_path, local_files_only=True)
    assert model_cfg.model_type == "xlm-roberta" and model_cfg.hidden_size == 1024, (
        f"Expected XLM-RoBERTa-large, got {model_cfg.model_type}/{model_cfg.hidden_size}"
    )
    data_path = resolve_data()
    train_df = pd.read_csv(data_path / "train.csv")
    test_df = pd.read_csv(data_path / "test.csv")
    sample_path = data_path / "sample_submission.csv"
    assert set(["id", "text", "language", "label"]).issubset(train_df.columns)
    assert set(["id", "text", "language"]).issubset(test_df.columns)
    assert len(train_df) == 14000 and len(test_df) == 6000
    assert train_df[["id", "text", "language", "label"]].notna().all().all()
    assert test_df[["id", "text", "language"]].notna().all().all()
    assert train_df.id.is_unique and test_df.id.is_unique
    assert set(train_df.label) == set(CFG.LABELS)
    assert set(train_df.language) == set(test_df.language) == {"en", "fr", "it", "pt"}
    if sample_path.exists():
        sample = pd.read_csv(sample_path)
        assert sample.id.astype(str).tolist() == test_df.id.astype(str).tolist()
    y = train_df.label.map(CFG.LABEL2ID).to_numpy(dtype=np.int64)
    strata = train_df.language.astype(str) + "_" + train_df.label.astype(str)
    print("Kaggle Model:", CFG.KAGGLE_MODEL_HANDLE)
    print("Downloaded model files:", model_path)
    print("Data:", data_path, "Train:", train_df.shape, "Test:", test_df.shape)
    print(train_df.groupby(["language", "label"]).size().to_string())
    """),
    code("""
    # 3. Token-level head + tail, preserving the final attack instruction in long prompts
    tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=True, local_files_only=True)
    # XLM-R single sequences use <s> ... </s>. Construct these explicitly because
    # some Transformers/tokenizer combinations omit build_inputs_with_special_tokens.
    special_count = tokenizer.num_special_tokens_to_add(pair=False)
    assert special_count == 2 and tokenizer.bos_token_id is not None and tokenizer.eos_token_id is not None
    budget = CFG.MAX_LENGTH - special_count
    assert budget > 0 and tokenizer.model_max_length >= CFG.MAX_LENGTH

    def encode_texts(texts, batch_size=1024):
        rows = []
        lengths = []
        for start in range(0, len(texts), batch_size):
            batch = [str(t) for t in texts[start:start + batch_size]]
            # Long raw inputs are intentionally head-tail truncated below. Suppress
            # the tokenizer's generic >model_max_length warning for this intermediate step.
            raw = tokenizer(batch, add_special_tokens=False, truncation=False, verbose=False)["input_ids"]
            for ids in raw:
                lengths.append(len(ids))
                if len(ids) > budget:
                    head = budget // 2
                    ids = ids[:head] + ids[-(budget - head):]
                ids = [tokenizer.bos_token_id] + ids + [tokenizer.eos_token_id]
                assert len(ids) <= CFG.MAX_LENGTH
                rows.append({"input_ids": ids, "attention_mask": [1] * len(ids)})
        return rows, np.asarray(lengths)

    train_rows, train_lengths = encode_texts(train_df.text.tolist())
    test_rows, test_lengths = encode_texts(test_df.text.tolist())
    print("Token length quantiles (train):", np.quantile(train_lengths, [0.5, 0.9, 0.95, 0.99, 1.0]))
    print("Head+tail used for", int((train_lengths > budget).sum()), "train rows and", int((test_lengths > budget).sum()), "test rows")

    class PromptDataset(Dataset):
        def __init__(self, rows, indices=None, labels=None):
            self.rows = rows
            self.indices = np.arange(len(rows)) if indices is None else np.asarray(indices)
            self.labels = labels
        def __len__(self):
            return len(self.indices)
        def __getitem__(self, index):
            pos = int(self.indices[index])
            item = self.rows[pos].copy()
            if self.labels is not None:
                item["labels"] = int(self.labels[pos])
            return item

    collator = DataCollatorWithPadding(tokenizer, pad_to_multiple_of=8)
    """),
    code("""
    # 4. Weighted loss, version-compatible Trainer setup and macro-F1
    class WeightedTrainer(Trainer):
        def __init__(self, class_weights=None, **kwargs):
            super().__init__(**kwargs)
            self.class_weights = class_weights
        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs["labels"]
            outputs = model(**{k: v for k, v in inputs.items() if k != "labels"})
            logits = outputs.logits
            loss = F.cross_entropy(logits.float(), labels, weight=self.class_weights.to(logits.device))
            return (loss, outputs) if return_outputs else loss

    def metrics(eval_pred):
        logits = eval_pred.predictions
        if isinstance(logits, tuple):
            logits = logits[0]
        pred = np.argmax(logits, axis=1)
        return {"macro_f1": f1_score(eval_pred.label_ids, pred, labels=[0, 1, 2], average="macro", zero_division=0)}

    ta_params = inspect.signature(TrainingArguments.__init__).parameters
    tr_params = inspect.signature(Trainer.__init__).parameters

    def make_args(output_dir, seed):
        kwargs = dict(
            output_dir=str(output_dir), overwrite_output_dir=True,
            learning_rate=CFG.LR, weight_decay=CFG.WEIGHT_DECAY,
            per_device_train_batch_size=CFG.TRAIN_BATCH,
            per_device_eval_batch_size=CFG.EVAL_BATCH,
            gradient_accumulation_steps=CFG.GRAD_ACCUM,
            num_train_epochs=CFG.EPOCHS, warmup_ratio=0.08,
            bf16=CFG.BF16, gradient_checkpointing=False,
            dataloader_num_workers=4, dataloader_pin_memory=True,
            dataloader_persistent_workers=True, logging_steps=100,
            optim="adamw_torch_fused",
            save_strategy="epoch", save_total_limit=1,
            load_best_model_at_end=True, metric_for_best_model="macro_f1",
            greater_is_better=True, eval_accumulation_steps=8,
            report_to="none", seed=seed, data_seed=CFG.SEED,
        )
        kwargs["eval_strategy" if "eval_strategy" in ta_params else "evaluation_strategy"] = "epoch"
        return TrainingArguments(**{k: v for k, v in kwargs.items() if k in ta_params})

    def make_trainer(model, args, tr_ds, va_ds, weights):
        kwargs = dict(
            model=model, args=args, train_dataset=tr_ds, eval_dataset=va_ds,
            data_collator=collator, compute_metrics=metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
        )
        if "processing_class" in tr_params:
            kwargs["processing_class"] = tokenizer
        elif "tokenizer" in tr_params:
            kwargs["tokenizer"] = tokenizer
        return WeightedTrainer(class_weights=weights, **kwargs)

    def probabilities(logits):
        if isinstance(logits, tuple):
            logits = logits[0]
        z = torch.as_tensor(logits, dtype=torch.float32)
        return torch.softmax(z, dim=1).numpy()
    """),
    code("""
    # 5. Five-fold A100 training. Each fold contributes one OOF block and test probabilities.
    skf = StratifiedKFold(n_splits=CFG.N_FOLDS, shuffle=True, random_state=CFG.SEED)
    oof_probs = np.zeros((len(train_df), 3), dtype=np.float32)
    test_probs = np.zeros((len(test_df), 3), dtype=np.float32)
    fold_ids = np.full(len(train_df), -1, dtype=np.int8)
    fold_results = []
    checkpoint_root = CFG.OUTPUT / f"xlmr_large_cv_{time.strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    test_ds = PromptDataset(test_rows)

    for fold, (tr_idx, va_idx) in enumerate(skf.split(train_df, strata), 1):
        fold_dir = checkpoint_root / f"fold_{fold}"
        if fold_dir.exists() and any(fold_dir.iterdir()):
            raise FileExistsError(f"Refusing to overwrite existing checkpoints: {fold_dir}")
        fold_dir.mkdir(exist_ok=True)
        counts = np.bincount(y[tr_idx], minlength=3)
        weights = (counts[0] / counts) ** CFG.CLASS_WEIGHT_POWER
        weights = torch.tensor(weights, dtype=torch.float32)
        torch.manual_seed(CFG.SEED + fold)
        torch.cuda.manual_seed_all(CFG.SEED + fold)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_path, local_files_only=True, num_labels=3,
            id2label=CFG.ID2LABEL, label2id=CFG.LABEL2ID,
            ignore_mismatched_sizes=True,
        )
        if hasattr(model, "config"):
            model.config.use_cache = False
        trainer = make_trainer(
            model, make_args(fold_dir, CFG.SEED + fold),
            PromptDataset(train_rows, tr_idx, y), PromptDataset(train_rows, va_idx, y), weights,
        )
        start = time.time()
        torch.cuda.reset_peak_memory_stats()
        trainer.train()
        val_output = trainer.predict(PromptDataset(train_rows, va_idx, y))
        test_output = trainer.predict(test_ds)
        oof_probs[va_idx] = probabilities(val_output.predictions)
        test_probs += probabilities(test_output.predictions) / CFG.N_FOLDS
        fold_ids[va_idx] = fold
        fold_f1 = f1_score(y[va_idx], oof_probs[va_idx].argmax(1), average="macro")
        peak_vram_gb = torch.cuda.max_memory_allocated() / 2**30
        fold_results.append({"fold": fold, "f1": float(fold_f1), "best_checkpoint": trainer.state.best_model_checkpoint, "minutes": round((time.time() - start) / 60, 1), "peak_vram_gb": round(peak_vram_gb, 2)})
        print(f"Fold {fold}/{CFG.N_FOLDS}: macro-F1={fold_f1:.5f}, elapsed={fold_results[-1]['minutes']} min, peak VRAM={peak_vram_gb:.1f} GiB")
        del trainer, model, val_output, test_output
        gc.collect()
        torch.cuda.empty_cache()
        shutil.rmtree(fold_dir)  # only this notebook's completed fold checkpoints

    assert np.all(fold_ids > 0)
    assert np.allclose(oof_probs.sum(1), 1, atol=1e-5)
    assert np.allclose(test_probs.sum(1), 1, atol=1e-5)
    print("OOF macro-F1:", f1_score(y, oof_probs.argmax(1), average="macro"))
    print(pd.DataFrame(fold_results).to_string(index=False))
    """),
    code("""
    # 6. Conservative class-bias tuning, evaluated by cross-fitting across OOF folds
    # Each fold's labels are excluded when selecting its evaluation bias.
    def macro_f1_fast(target, pred):
        cm = np.bincount(3 * target + pred, minlength=9).reshape(3, 3)
        tp = np.diag(cm)
        den = cm.sum(0) + cm.sum(1)
        return float(np.mean(np.divide(2 * tp, den, out=np.zeros(3), where=den > 0)))

    def best_bias(logp, target):
        best = np.zeros(3, dtype=np.float32)
        best_score = macro_f1_fast(target, logp.argmax(1))
        # Small, predeclared grid. Bias for BENIGN is fixed to zero.
        for jb in np.arange(-1.0, 1.001, 0.2):
            for pi in np.arange(-1.0, 1.001, 0.2):
                bias = np.array([0.0, jb, pi], dtype=np.float32)
                score = macro_f1_fast(target, (logp + bias).argmax(1))
                if score > best_score + 1e-9:
                    best_score, best = score, bias
        return best, best_score

    log_oof = np.log(np.clip(oof_probs, 1e-7, 1.0))
    log_test = np.log(np.clip(test_probs, 1e-7, 1.0))
    crossfit_pred = np.zeros(len(y), dtype=np.int8)
    bias_by_fold = []
    for fold in range(1, CFG.N_FOLDS + 1):
        fit = fold_ids != fold
        val = ~fit
        bias, _ = best_bias(log_oof[fit], y[fit])
        bias_by_fold.append(bias)
        crossfit_pred[val] = (log_oof[val] + bias).argmax(1)

    raw_f1 = macro_f1_fast(y, log_oof.argmax(1))
    crossfit_f1 = macro_f1_fast(y, crossfit_pred)
    fold_gains = [
        macro_f1_fast(y[fold_ids == fold], crossfit_pred[fold_ids == fold])
        - macro_f1_fast(y[fold_ids == fold], log_oof[fold_ids == fold].argmax(1))
        for fold in range(1, CFG.N_FOLDS + 1)
    ]
    use_bias = crossfit_f1 >= raw_f1 + 0.0015 and sum(g > 0 for g in fold_gains) >= 3
    final_bias = best_bias(log_oof, y)[0] if use_bias else np.zeros(3, dtype=np.float32)
    final_pred = (log_test + final_bias).argmax(1)
    print(f"Raw OOF F1={raw_f1:.5f}; cross-fitted bias F1={crossfit_f1:.5f}; fold gains={np.round(fold_gains, 4)}")
    print("Bias applied:", use_bias, final_bias)
    print(classification_report(y, oof_probs.argmax(1), target_names=CFG.LABELS, digits=4))
    print("Confusion matrix (raw OOF):\\n", confusion_matrix(y, oof_probs.argmax(1)))
    for lang in sorted(train_df.language.unique()):
        mask = train_df.language.eq(lang).to_numpy()
        print(lang, "n=", mask.sum(), "macro-F1=", round(macro_f1_fast(y[mask], oof_probs[mask].argmax(1)), 5))
    """),
    code("""
    # 7. Save aligned artifacts and validate submission before spending a Kaggle attempt
    submission = pd.DataFrame({
        "id": test_df.id.astype(str).to_numpy(),
        "label": [CFG.ID2LABEL[int(v)] for v in final_pred],
    })
    assert submission.columns.tolist() == ["id", "label"]
    assert len(submission) == len(test_df) == 6000
    assert submission.id.is_unique and submission.notna().all().all()
    assert submission.id.tolist() == test_df.id.astype(str).tolist()
    assert set(submission.label).issubset(set(CFG.LABELS))
    submission_path = CFG.OUTPUT / "submission.csv"
    submission.to_csv(submission_path, index=False)
    pd.DataFrame({
        "id": train_df.id.astype(str), "fold": fold_ids,
        "label": train_df.label,
        **{f"p_{name}": oof_probs[:, i] for i, name in enumerate(CFG.LABELS)},
    }).to_csv(CFG.OUTPUT / "xlmr_large_oof.csv", index=False)
    pd.DataFrame({
        "id": test_df.id.astype(str),
        **{f"p_{name}": test_probs[:, i] for i, name in enumerate(CFG.LABELS)},
    }).to_csv(CFG.OUTPUT / "xlmr_large_test_probs.csv", index=False)
    (CFG.OUTPUT / "xlmr_large_run.json").write_text(json.dumps({
        "model": CFG.KAGGLE_MODEL_HANDLE, "seed": CFG.SEED, "folds": CFG.N_FOLDS,
        "max_length": CFG.MAX_LENGTH, "epochs_cap": CFG.EPOCHS,
        "learning_rate": CFG.LR, "class_weight_power": CFG.CLASS_WEIGHT_POWER,
        "train_batch": CFG.TRAIN_BATCH, "eval_batch": CFG.EVAL_BATCH,
        "gradient_accumulation": CFG.GRAD_ACCUM, "bf16": CFG.BF16,
        "gradient_checkpointing": False,
        "fold_results": fold_results, "raw_oof_macro_f1": raw_f1,
        "crossfit_bias_oof_macro_f1": crossfit_f1,
        "bias_used": bool(use_bias), "bias": final_bias.tolist(),
        "labels": CFG.LABELS,
    }, indent=2), encoding="utf-8")
    reloaded = pd.read_csv(submission_path, dtype={"id": str})
    assert reloaded.id.tolist() == test_df.id.astype(str).tolist()
    assert reloaded.label.isin(CFG.LABELS).all()
    print("Ready to submit:", submission_path)
    print("Predicted class distribution:\\n", submission.label.value_counts().to_string())
    display(submission.head())
    """),
    markdown("""
    ## Colab run and submission

    Put `train.csv`, `test.csv` and `sample_submission.csv` in one of the configured Drive folders. KaggleHub downloads the approved `aisuko/xlm-roberta-large/Transformers/default` checkpoint. If Kaggle asks for authentication, add `KAGGLE_API_TOKEN` under the Colab key icon (**Secrets**) and grant notebook access. Select **A100 GPU**, run all cells, and wait for the final backup/stop cell. It copies the submission generated from `test.csv` and probability artifacts from `/content` to `MyDrive/RMIT-Hackathon-2026/outputs/xlmr-large`, waits 10 seconds, then stops this Colab runtime. Submit the copied `submission.csv` to Kaggle and rename the Kaggle notebook to `<university>_<campus>_<team>_C1`.

    Keep the OOF/test probability files for an OOF-validated blend with Wolf Defender. All probability columns follow the fixed order `BENIGN`, `JAILBREAK`, `PROMPT_INJECTION`. Public leaderboard uses only 30% of test, so a small public-score movement is noisy.
    """),
    code("""
    # 8. Back up deliverables to Google Drive, then stop this Colab runtime after 10 seconds
    deliverables = [
        "submission.csv",
        "xlmr_large_oof.csv",
        "xlmr_large_test_probs.csv",
        "xlmr_large_run.json",
    ]
    CFG.DRIVE_OUTPUT.mkdir(parents=True, exist_ok=True)
    copied = []
    for filename in deliverables:
        source = CFG.OUTPUT / filename
        assert source.is_file(), f"Missing output artifact: {source}"
        destination = CFG.DRIVE_OUTPUT / filename
        shutil.copy2(source, destination)
        assert destination.is_file() and destination.stat().st_size == source.stat().st_size
        copied.append(str(destination))
    print("Backed up to Google Drive:")
    print("\\n".join(copied))
    print("Stopping Colab runtime in 10 seconds...")
    time.sleep(10)
    from google.colab import runtime
    runtime.unassign()
    """),
]

for index, cell in enumerate(cells):
    cell["id"] = f"xlmr-large-{index:02d}"

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
