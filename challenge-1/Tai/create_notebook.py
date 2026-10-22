import json
import os

notebook = {
    "cells": [],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.10.12"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

def add_md(text):
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": text.strip().splitlines(keepends=True)
    })

def add_code(text):
    notebook["cells"].append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.strip().splitlines(keepends=True)
    })

# --- CELL 1: Header & Plan ---
add_md("""# 🛡️ RMIT Hackathon 2026: Multilingual Prompt-Attack Classification
### End-to-End Pipeline: XLM-RoBERTa-base + Weighted Cross-Entropy + Macro-F1 Optimization

- **Author / Team:** Tai (@Tai)
- **Dataset:** `dangthtai/rmit-hackathon-2026-dataset` (`/kaggle/input/rmit-hackathon-2026-dataset`)
- **Backbone Model:** `/kaggle/input/models/aisuko/xlm-roberta-base/transformers/default/1`
  (Kaggle Model: `https://www.kaggle.com/models/aisuko/xlm-roberta-base/Transformers/default`)
- **Evaluation Metric:** **Macro-F1** (Kaggle Leaderboard)
- **Target Classes:** `BENIGN`, `JAILBREAK`, `PROMPT_INJECTION`

---

### 💡 Chiến lược & Điểm mấu chốt của Pipeline:
1. **Multilingual Representation:** XLM-RoBERTa-base được pretrain trên 100+ ngôn ngữ, bảo toàn sắc thái tự nhiên của tiếng Anh, Pháp, Ý, Bồ Đào Nha mà không cần dịch qua tiếng Anh (tránh làm mất cấu trúc payload / prompt injection).
2. **Xử lý mất cân bằng dữ liệu (Class Imbalance):**
   - Phân bố nhãn trong Train: `BENIGN` (~62%), `JAILBREAK` (~31%), `PROMPT_INJECTION` (~7%).
   - Sử dụng **Inverse Square-Root Class Weights** ($w_c \\propto \\frac{1}{\\sqrt{n_c}}$) trong Weighted Cross-Entropy Loss: tăng trọng số cho lớp hiếm mà không làm over-penalize lớp phổ biến.
3. **Stratified Split 80/20:** Phân tầng theo nhãn (và ngôn ngữ nếu có) để bảo toàn tỷ lệ giữa Train và Validation.
4. **Early Stopping & Best Checkpoint:** Theo dõi trực tiếp **Macro-F1** trên validation (`patience = 2`).
5. **Post-Processing (Logit Bias Tuning):** Tối ưu bias vector $\\hat{y} = \\arg\\max_c (z_c + b_c)$ trên validation logits để đẩy chỉ số Macro-F1 lên tối đa.
6. **Strict Submission Assertion:** Đảm bảo đủ 6.000 dòng test, format chuẩn `id,label`, không trùng lặp, không NaN.
""")

# --- CELL 2: Environment & Libraries ---
add_code('''# ==============================================================================
# 1. SETUP ENVIRONMENT & IMPORT LIBRARIES
# ==============================================================================
import os
import gc
import re
import sys
import glob
import time
import json
import random
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import (
    f1_score, 
    accuracy_score, 
    classification_report, 
    confusion_matrix
)
from scipy.optimize import minimize

import transformers
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback,
    set_seed
)
import datasets
from datasets import Dataset as HFDataset

warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Set plot style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["figure.figsize"] = (10, 5)
plt.rcParams["font.size"] = 11

print(f"PyTorch Version: {torch.__version__}")
print(f"Transformers Version: {transformers.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
''')

# --- CELL 3: Reproducibility & Config ---
add_code('''# ==============================================================================
# 2. GLOBAL CONFIGURATION & SEED EVERYTHING
# ==============================================================================
def seed_everything(seed: int = 42):
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    set_seed(seed)

class Config:
    # Random Seed
    SEED = 42
    
    # Dataset & Paths
    DATASET_SLUG = "dangthtai/rmit-hackathon-2026-dataset"
    KAGGLE_INPUT_DIR = "/kaggle/input/rmit-hackathon-2026-dataset"
    OUTPUT_DIR = "./output_xlm_roberta"
    SUBMISSION_PATH = "/kaggle/working/submission.csv"
    LOCAL_SUBMISSION_PATH = "./submission.csv"
    
    # Model Path from Kaggle: https://www.kaggle.com/models/aisuko/xlm-roberta-base/Transformers/default
    MODEL_PATH = "/kaggle/input/models/aisuko/xlm-roberta-base/transformers/default/1"
    
    # Label Definitions
    LABELS = ["BENIGN", "JAILBREAK", "PROMPT_INJECTION"]
    LABEL2ID = {"BENIGN": 0, "JAILBREAK": 1, "PROMPT_INJECTION": 2}
    ID2LABEL = {0: "BENIGN", 1: "JAILBREAK", 2: "PROMPT_INJECTION"}
    NUM_LABELS = len(LABELS)
    
    # Training Hyperparameters
    MAX_LENGTH = 256          # Covers >95% prompts, balances speed & GPU memory
    BATCH_SIZE = 16          # 16 on 16GB GPU (T4/P100); use 8 with grad_accum=2 if OOM
    EVAL_BATCH_SIZE = 32
    LEARNING_RATE = 2e-5
    WEIGHT_DECAY = 0.01
    WARMUP_RATIO = 0.1
    NUM_EPOCHS = 4
    PATIENCE = 2             # Early stopping on validation Macro-F1
    FP16 = torch.cuda.is_available()
    
    # Validation
    VAL_SIZE = 0.20          # 80% Train, 20% Validation

def verify_model_path():
    """
    Kiểm tra đường dẫn model Kaggle đã cấu hình:
    Ưu tiên tuyệt đối: /kaggle/input/models/aisuko/xlm-roberta-base/transformers/default/1
    """
    target = Config.MODEL_PATH
    if os.path.exists(target):
        print(f"✅ Đã tìm thấy mô hình tại: {target}")
        return target
    
    # Fallback dự phòng nếu mount hơi khác hoặc chạy test offline
    fallback_candidates = [
        "/kaggle/input/xlm-roberta-base/transformers/default/1",
        "/kaggle/input/xlm-roberta-base/transformers/default",
        "/kaggle/input/models/aisuko/xlm-roberta-base/transformers/default",
        "/kaggle/input/xlm-roberta-base",
        "FacebookAI/xlm-roberta-base"
    ]
    for p in fallback_candidates:
        if os.path.exists(p) or p.startswith("FacebookAI"):
            print(f"⚠️ Không thấy '{target}', tự động chuyển sang đường dẫn khả dụng: {p}")
            return p
    return target

Config.MODEL_PATH = verify_model_path()
seed_everything(Config.SEED)
print(f"Configuration loaded & Model path: {Config.MODEL_PATH}")
''')

# --- CELL 4: Smart Data Finder & Loader ---
add_code('''# ==============================================================================
# 3. ROBUST DATASET DISCOVERY & LOADING
# ==============================================================================
def locate_dataset_files():
    """
    Tự động tìm kiếm đường dẫn file train.csv và test.csv:
    1. Kiểm tra thư mục /kaggle/input/rmit-hackathon-2026-dataset
    2. Quét toàn bộ /kaggle/input để tìm kiếm nếu tên thư mục Kaggle thay đổi
    3. Kiểm tra các thư mục local (./data, .)
    """
    candidates = [
        Config.KAGGLE_INPUT_DIR,
        "/kaggle/input/rmit-hackathon-2026",
        "/kaggle/input/rmit-hackathon",
        "./data",
        "."
    ]
    
    train_path, test_path = None, None
    
    for candidate in candidates:
        if os.path.exists(candidate):
            train_candidates = glob.glob(os.path.join(candidate, "*train*.csv"))
            test_candidates = glob.glob(os.path.join(candidate, "*test*.csv"))
            if train_candidates and test_candidates:
                train_path = train_candidates[0]
                test_path = test_candidates[0]
                print(f"Found dataset in: {candidate}")
                break
                
    # Nếu chưa tìm thấy, quét toàn bộ /kaggle/input
    if (train_path is None or test_path is None) and os.path.exists("/kaggle/input"):
        for root, dirs, files in os.walk("/kaggle/input"):
            for f in files:
                if "train" in f.lower() and f.endswith(".csv"):
                    train_path = os.path.join(root, f)
                elif "test" in f.lower() and f.endswith(".csv"):
                    test_path = os.path.join(root, f)
                    
    if train_path is None or test_path is None:
        raise FileNotFoundError(
            f"Could not locate train.csv and test.csv! "
            f"Please ensure dataset 'dangthtai/rmit-hackathon-2026-dataset' is added via Kaggle Add Input."
        )
        
    return train_path, test_path

train_file, test_file = locate_dataset_files()
print(f"Loading Train data from: {train_file}")
print(f"Loading Test data from:  {test_file}")

train_df = pd.read_csv(train_file)
test_df = pd.read_csv(test_file)

print(f"\\nTrain shape: {train_df.shape}")
print(f"Test shape:  {test_df.shape}")

# Tự động nhận diện cột văn bản (prompt / text / content)
def detect_columns(df, is_train=True):
    cols = df.columns.tolist()
    
    # 1. Text column
    text_col = None
    for candidate in ["prompt", "text", "content", "input", "query"]:
        if candidate in cols:
            text_col = candidate
            break
    if text_col is None:
        for c in cols:
            if c not in ["id", "label", "language", "lang"] and df[c].dtype == "object":
                text_col = c
                break
                
    # 2. ID column
    id_col = "id" if "id" in cols else cols[0]
    
    # 3. Label column (for train)
    label_col = "label" if "label" in cols else None
    
    # 4. Language column (if exists)
    lang_col = None
    for candidate in ["language", "lang", "lang_code"]:
        if candidate in cols:
            lang_col = candidate
            break
            
    return {"text": text_col, "id": id_col, "label": label_col, "lang": lang_col}

col_info = detect_columns(train_df, is_train=True)
TEXT_COL = col_info["text"]
ID_COL = col_info["id"]
LABEL_COL = col_info["label"]
LANG_COL = col_info["lang"]

print(f"\\nDetected Columns:")
print(f" - ID Column:       {ID_COL}")
print(f" - Text Column:     {TEXT_COL}")
print(f" - Label Column:    {LABEL_COL}")
print(f" - Language Column: {LANG_COL if LANG_COL else 'Not provided (multilingual embedded in text)'}")
''')

# --- CELL 5: EDA Section Markdown ---
add_md("""---
## 📊 2. Exploratory Data Analysis (EDA)

Chúng ta sẽ phân tích:
1. **Phân bố nhãn (Class Distribution):** Đánh giá mức độ mất cân bằng dữ liệu giữa `BENIGN`, `JAILBREAK`, và `PROMPT_INJECTION`.
2. **Ngôn ngữ (Language Distribution):** Kiểm tra các ngôn ngữ có mặt trong dataset (nếu có cột metadata).
3. **Độ dài Prompt (Token Length Distribution):** Đo độ dài token thực tế qua XLM-RoBERTa Tokenizer để chọn `max_length` chuẩn xác nhất (tránh truncate cụm từ tấn công).
4. **Kiểm tra dữ liệu thiếu và trùng lặp (Missing / Duplicates).**
""")

# --- CELL 6: EDA - Class Distribution ---
add_code('''# ==============================================================================
# 4. EDA: CLASS DISTRIBUTION
# ==============================================================================
print("=== TRAIN DATA PREVIEW ===")
display(train_df.head(5))

print("\\n=== LABEL VALUE COUNTS ===")
label_counts = train_df[LABEL_COL].value_counts()
label_percentages = train_df[LABEL_COL].value_counts(normalize=True) * 100

summary_df = pd.DataFrame({
    "Count": label_counts,
    "Percentage (%)": label_percentages.round(2)
})
display(summary_df)

# Plot class distribution
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Bar chart
colors = ["#2b5c8f", "#d95f02", "#7570b3"]
sns.barplot(x=label_counts.index, y=label_counts.values, palette=colors, ax=axes[0])
axes[0].set_title("Distribution of Attack Classes (Counts)", fontsize=13, fontweight="bold")
axes[0].set_ylabel("Number of Samples")
axes[0].set_xlabel("Class")
for i, count in enumerate(label_counts.values):
    axes[0].text(i, count + 100, f"{count} ({count/len(train_df)*100:.1f}%)", ha="center", fontweight="bold")

# Pie chart
axes[1].pie(
    label_counts.values, 
    labels=label_counts.index, 
    autopct="%1.1f%%", 
    colors=colors, 
    startangle=140,
    explode=(0.02, 0.04, 0.08)
)
axes[1].set_title("Class Ratio in Training Set", fontsize=13, fontweight="bold")

plt.tight_layout()
plt.show()

print(f"Tỷ lệ lớp thiểu số PROMPT_INJECTION: {label_percentages.get('PROMPT_INJECTION', 0):.2f}%")
print("Nhận xét: Lớp PROMPT_INJECTION chiếm tỷ lệ rất thấp (~7%). Nếu không dùng class weights, Macro-F1 sẽ bị kéo giảm đáng kể!")
''')

# --- CELL 7: EDA - Token Length Distribution ---
add_code('''# ==============================================================================
# 5. EDA: TOKEN LENGTH ANALYSIS & MISSING / DUPLICATES
# ==============================================================================
# 1. Missing values
print("--- Missing Values ---")
print("Train NaNs:\\n", train_df.isnull().sum())
print("Test NaNs:\\n", test_df.isnull().sum())

# 2. Duplicates
train_dups = train_df.duplicated(subset=[TEXT_COL]).sum()
print(f"\\nTrùng lặp text trong tập Train: {train_dups} mẫu ({train_dups/len(train_df)*100:.2f}%)")

# 3. Phân tích độ dài token bằng Tokenizer của XLM-RoBERTa
print(f"\\nĐang tải XLM-RoBERTa Tokenizer từ: {Config.MODEL_PATH}...")
tokenizer = AutoTokenizer.from_pretrained(Config.MODEL_PATH)

sample_texts = train_df[TEXT_COL].dropna().tolist()
token_lens = [len(tokenizer.encode(str(t), truncation=False)) for t in sample_texts[:3000]] # lấy mẫu 3000

token_lens_series = pd.Series(token_lens)
print("\\n--- Phân bố độ dài Token (Sample 3,000) ---")
print(f"Min:        {token_lens_series.min()}")
print(f"Median:     {token_lens_series.median():.0f}")
print(f"Mean:       {token_lens_series.mean():.1f}")
print(f"75th pct:   {token_lens_series.quantile(0.75):.0f}")
print(f"90th pct:   {token_lens_series.quantile(0.90):.0f}")
print(f"95th pct:   {token_lens_series.quantile(0.95):.0f}")
print(f"99th pct:   {token_lens_series.quantile(0.99):.0f}")
print(f"Max:        {token_lens_series.max()}")

pct_covered = (token_lens_series <= Config.MAX_LENGTH).mean() * 100
print(f"\\nTỷ lệ prompt được giữ nguyên toàn bộ với MAX_LENGTH={Config.MAX_LENGTH}: {pct_covered:.2f}%")

# Plot token length distribution
plt.figure(figsize=(10, 4))
sns.histplot(token_lens, bins=60, kde=True, color="#1f77b4")
plt.axvline(Config.MAX_LENGTH, color="red", linestyle="--", linewidth=2, label=f"MAX_LENGTH = {Config.MAX_LENGTH}")
plt.title("Distribution of Prompt Token Lengths (XLM-RoBERTa Tokenizer)", fontsize=12, fontweight="bold")
plt.xlabel("Number of Tokens")
plt.ylabel("Frequency")
plt.legend()
plt.tight_layout()
plt.show()
''')

# --- CELL 8: EDA - Sample Inspection ---
add_code('''# ==============================================================================
# 6. SAMPLE INSPECTION: BENIGN vs JAILBREAK vs PROMPT_INJECTION
# ==============================================================================
print("=== MẪU VĂN BẢN THEO TỪNG LỚP ===")
for label in Config.LABELS:
    samples = train_df[train_df[LABEL_COL] == label][TEXT_COL].head(2).tolist()
    print(f"\\n{'='*20} [{label}] {'='*20}")
    for i, s in enumerate(samples, 1):
        print(f"[{i}] {s[:180]}...\\n")
''')

# --- CELL 9: Train / Val Split Markdown ---
add_md("""---
## ✂️ 3. Phân chia Train / Validation (Stratified 80% - 20%)

- Để đánh giá mô hình một cách khách quan, chúng ta chia tập `train.csv` (14.000 dòng) thành:
  - **Train set:** 80% (~11.200 dòng)
  - **Validation set:** 20% (~2.800 dòng)
- **Kỹ thuật Stratified Split:** Đảm bảo tỷ lệ nhãn (`BENIGN`, `JAILBREAK`, `PROMPT_INJECTION`) trong cả hai tập hoàn toàn đồng nhất. Nếu có cột ngôn ngữ, ta kết hợp phân tầng theo cả cặp `(label, language)`.
""")

# --- CELL 10: Train / Val Split Code ---
add_code('''# ==============================================================================
# 7. STRATIFIED TRAIN / VALIDATION SPLIT
# ==============================================================================
# Map labels to integers
train_df["label_id"] = train_df[LABEL_COL].map(Config.LABEL2ID)

# Create stratification key
if LANG_COL is not None and LANG_COL in train_df.columns:
    print(f"Stratifying by both Label and Language...")
    train_df["strat_key"] = train_df["label_id"].astype(str) + "_" + train_df[LANG_COL].astype(str)
else:
    print(f"Stratifying by Label...")
    train_df["strat_key"] = train_df["label_id"]

# Split 80% train, 20% validation
train_sub_df, val_sub_df = train_test_split(
    train_df,
    test_size=Config.VAL_SIZE,
    random_state=Config.SEED,
    stratify=train_df["strat_key"]
)

train_sub_df = train_sub_df.reset_index(drop=True)
val_sub_df = val_sub_df.reset_index(drop=True)

print(f"Total Train records:      {len(train_df)}")
print(f"Train subset records:     {len(train_sub_df)} ({len(train_sub_df)/len(train_df)*100:.1f}%)")
print(f"Validation subset records:{len(val_sub_df)} ({len(val_sub_df)/len(train_df)*100:.1f}%)")

# Verify label distribution equality
train_dist = train_sub_df["label_id"].map(Config.ID2LABEL).value_counts(normalize=True) * 100
val_dist = val_sub_df["label_id"].map(Config.ID2LABEL).value_counts(normalize=True) * 100

compare_dist = pd.DataFrame({"Train Subset (%)": train_dist, "Val Subset (%)": val_dist}).round(2)
print("\\nSo sánh phân bố nhãn sau khi phân tầng:")
display(compare_dist)
''')

# --- CELL 11: Class Weights Markdown ---
add_md("""---
## ⚖️ 4. Xử lý mất cân bằng: Inverse Square-Root Class Weights

### Công thức Weighted Cross-Entropy Loss:
$$L = - w_y \\log(P(y \\mid x))$$

Trong đó $w_y$ là trọng số tương ứng của lớp đúng.

Thay vì dùng trọng số nghịch đảo tần suất $w_c = \\frac{1}{n_c}$ (quá gắt, dễ gây false positive cho lớp thiểu số), chúng ta áp dụng **trọng số căn bậc hai nghịch đảo (Inverse Square-Root)**:
$$w_c \\propto \\frac{1}{\\sqrt{n_c}}$$

Chuẩn hóa để trọng số của lớp `BENIGN` xấp xỉ 1.00:
- `BENIGN`: $\\approx 1.00$
- `JAILBREAK`: $\\approx 1.41$
- `PROMPT_INJECTION`: $\\approx 2.98$

Cách này giúp mô hình chú ý gấp ~3 lần vào các cuộc tấn công prompt injection mà vẫn kiểm soát được độ ổn định dự đoán trên `BENIGN`.
""")

# --- CELL 12: Class Weights & Custom Trainer ---
add_code('''# ==============================================================================
# 8. CLASS WEIGHTS CALCULATION & CUSTOM WEIGHTED TRAINER
# ==============================================================================
train_class_counts = train_sub_df["label_id"].value_counts().sort_index().values
print("Số lượng mẫu từng lớp trong tập train_sub:", train_class_counts)

# Tính trọng số nghịch đảo căn bậc hai
inv_sqrt_weights = 1.0 / np.sqrt(train_class_counts)
# Chuẩn hóa sao cho trọng số lớp BENIGN (class 0) bằng 1.0
normalized_weights = inv_sqrt_weights / inv_sqrt_weights[0]

weights_tensor = torch.tensor(normalized_weights, dtype=torch.float)
print("\\nTrọng số lớp (Normalized Inverse Square-Root):")
for idx, name in Config.ID2LABEL.items():
    print(f" - {name:<18} (Class {idx}): {normalized_weights[idx]:.4f}")

# Custom HuggingFace Trainer kế thừa để tùy chỉnh Weighted Cross-Entropy Loss
class WeightedTrainer(Trainer):
    def __init__(self, class_weights=None, *args, **kwargs):
        # Tự động chuyển đổi tokenizer <-> processing_class tùy phiên bản Transformers (v4 vs v5)
        import inspect
        trainer_params = inspect.signature(Trainer.__init__).parameters
        if "tokenizer" in kwargs and "processing_class" in trainer_params and "tokenizer" not in trainer_params:
            kwargs["processing_class"] = kwargs.pop("tokenizer")
        elif "processing_class" in kwargs and "tokenizer" in trainer_params and "processing_class" not in trainer_params:
            kwargs["tokenizer"] = kwargs.pop("processing_class")
            
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None, **kwargs):
        labels = inputs.get("labels")
        outputs = model(**inputs)
        logits = outputs.get("logits")
        
        if self.class_weights is not None:
            weights = self.class_weights.to(logits.device)
            loss_fct = nn.CrossEntropyLoss(weight=weights)
        else:
            loss_fct = nn.CrossEntropyLoss()
            
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss

print("\\nWeightedTrainer đã được định nghĩa thành công!")
''')

# --- CELL 13: Dataset Preparation Markdown ---
add_md("""---
## 🔄 5. Chuẩn bị Dataset & Tokenization (XLM-RoBERTa)

Chuyển đổi DataFrame sang định dạng Hugging Face `Dataset` và tokenize với `max_length = 256`.
""")

# --- CELL 14: Dataset Preparation Code ---
add_code('''# ==============================================================================
# 9. TOKENIZATION & DATASET PREPARATION
# ==============================================================================
def prepare_hf_dataset(df, tokenizer, max_length=Config.MAX_LENGTH, is_test=False):
    """
    Tokenize các cột prompt và chuyển thành PyTorch format
    """
    texts = df[TEXT_COL].fillna("").astype(str).tolist()
    
    print(f"Tokenizing {len(texts)} samples (max_length={max_length})...")
    encodings = tokenizer(
        texts,
        truncation=True,
        padding="max_length",
        max_length=max_length,
        return_tensors=None
    )
    
    data_dict = {
        "input_ids": encodings["input_ids"],
        "attention_mask": encodings["attention_mask"]
    }
    
    if not is_test:
        data_dict["labels"] = df["label_id"].tolist()
        
    return HFDataset.from_dict(data_dict)

train_hf_dataset = prepare_hf_dataset(train_sub_df, tokenizer)
val_hf_dataset   = prepare_hf_dataset(val_sub_df, tokenizer)

print(f"\\nTrain HuggingFace Dataset: {len(train_hf_dataset)} items")
print(f"Validation HuggingFace Dataset: {len(val_hf_dataset)} items")
''')

# --- CELL 15: Training Setup Markdown ---
add_md("""---
## 🚀 6. Huấn luyện mô hình XLM-RoBERTa-base

- **Metric theo dõi:** `Macro-F1` (quyết định chọn checkpoint tốt nhất).
- **Early Stopping:** `patience = 2` (dừng sớm nếu Macro-F1 không tăng trong 2 epoch liên tiếp).
- **FP16:** Kích hoạt Mixed Precision để tối ưu tốc độ GPU và tiết kiệm VRAM.
""")

# --- CELL 16: Metrics Computation Code ---
add_code('''# ==============================================================================
# 10. COMPUTE METRICS FOR TRAINER
# ==============================================================================
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    
    macro_f1 = f1_score(labels, predictions, average="macro", zero_division=0)
    acc = accuracy_score(labels, predictions)
    per_class_f1 = f1_score(labels, predictions, average=None, zero_division=0)
    
    metrics = {
        "macro_f1": float(macro_f1),
        "accuracy": float(acc),
    }
    for i, name in Config.ID2LABEL.items():
        if i < len(per_class_f1):
            metrics[f"f1_{name.lower()}"] = float(per_class_f1[i])
            
    return metrics
''')

# --- CELL 17: Model & Training Arguments ---
add_code('''# ==============================================================================
# 11. INITIALIZE MODEL & TRAINING ARGUMENTS
# ==============================================================================
print(f"Loading sequence classification model from: {Config.MODEL_PATH}...")
model = AutoModelForSequenceClassification.from_pretrained(
    Config.MODEL_PATH,
    num_labels=Config.NUM_LABELS,
    id2label=Config.ID2LABEL,
    label2id=Config.LABEL2ID
)

# Training Arguments (Tương thích tự động 100% với cả Transformers v4.x và v5.x)
import inspect
sig = inspect.signature(TrainingArguments.__init__)
valid_params = sig.parameters

training_args_dict = {
    "output_dir": Config.OUTPUT_DIR,
    "learning_rate": Config.LEARNING_RATE,
    "per_device_train_batch_size": Config.BATCH_SIZE,
    "per_device_eval_batch_size": Config.EVAL_BATCH_SIZE,
    "num_train_epochs": Config.NUM_EPOCHS,
    "weight_decay": Config.WEIGHT_DECAY,
    "logging_steps": 50,
    "save_total_limit": 2,
    "seed": Config.SEED,
    "report_to": "none"
}

# 1. Evaluation Strategy
if "eval_strategy" in valid_params:
    training_args_dict["eval_strategy"] = "epoch"
elif "evaluation_strategy" in valid_params:
    training_args_dict["evaluation_strategy"] = "epoch"

# 2. Save Strategy
if "save_strategy" in valid_params:
    training_args_dict["save_strategy"] = "epoch"

# 3. Warmup (Transformers v5 bỏ warmup_ratio, thay bằng warmup_steps hỗ trợ float < 1.0)
if "warmup_ratio" in valid_params:
    training_args_dict["warmup_ratio"] = Config.WARMUP_RATIO
elif "warmup_steps" in valid_params:
    training_args_dict["warmup_steps"] = Config.WARMUP_RATIO

# 4. FP16 Mixed Precision
if "fp16" in valid_params:
    training_args_dict["fp16"] = Config.FP16

# 5. Best checkpoint selection
if "load_best_model_at_end" in valid_params:
    training_args_dict["load_best_model_at_end"] = True
if "metric_for_best_model" in valid_params:
    training_args_dict["metric_for_best_model"] = "macro_f1"
if "greater_is_better" in valid_params:
    training_args_dict["greater_is_better"] = True

# 6. Logging directory (chỉ truyền nếu phiên bản transformers hỗ trợ)
if "logging_dir" in valid_params:
    training_args_dict["logging_dir"] = f"{Config.OUTPUT_DIR}/logs"

training_args = TrainingArguments(**training_args_dict)

# Instantiate WeightedTrainer with early stopping
trainer_sig = inspect.signature(Trainer.__init__)
trainer_kwargs = {
    "model": model,
    "args": training_args,
    "train_dataset": train_hf_dataset,
    "eval_dataset": val_hf_dataset,
    "compute_metrics": compute_metrics,
    "class_weights": weights_tensor,
    "callbacks": [EarlyStoppingCallback(early_stopping_patience=Config.PATIENCE)]
}

# Tương thích với cả Transformers v5 (processing_class) lẫn Transformers v4 (tokenizer)
if "processing_class" in trainer_sig.parameters:
    trainer_kwargs["processing_class"] = tokenizer
elif "tokenizer" in trainer_sig.parameters:
    trainer_kwargs["tokenizer"] = tokenizer

trainer = WeightedTrainer(**trainer_kwargs)

print("Trainer initialized successfully and ready for training!")
''')

# --- CELL 18: Run Training ---
add_code('''# ==============================================================================
# 12. RUN FINE-TUNING
# ==============================================================================
print("Starting Fine-tuning XLM-RoBERTa-base...")
start_time = time.time()

train_result = trainer.train()

training_time = time.time() - start_time
print(f"\\nTraining completed in {training_time/60:.2f} minutes.")

# Save best model
best_model_path = "./best_xlm_roberta"
trainer.save_model(best_model_path)
tokenizer.save_pretrained(best_model_path)
print(f"Best checkpoint saved to: {best_model_path}")
''')

# --- CELL 19: Evaluation Section Markdown ---
add_md("""---
## 📈 7. Đánh giá chi tiết & Phân tích lỗi (Error Analysis)

Chúng ta sẽ phân tích toàn diện trên tập Validation:
- **Macro-F1 tổng thể** và **F1 từng lớp**.
- **Classification Report** (Precision, Recall, F1).
- **Confusion Matrix** (Ma trận nhầm lẫn): Tìm các cặp lớp dễ bị nhầm lẫn nhất (đặc biệt giữa `JAILBREAK` và `PROMPT_INJECTION`).
""")

# --- CELL 20: Detailed Validation & Confusion Matrix ---
add_code('''# ==============================================================================
# 13. DETAILED VALIDATION EVALUATION & CONFUSION MATRIX
# ==============================================================================
val_predictions_raw = trainer.predict(val_hf_dataset)
val_logits = val_predictions_raw.predictions
val_preds = np.argmax(val_logits, axis=-1)
val_labels = val_predictions_raw.label_ids

macro_f1_val = f1_score(val_labels, val_preds, average="macro")
acc_val = accuracy_score(val_labels, val_preds)

print(f"=== VALIDATION RESULTS (BASELINE ARGMAX) ===")
print(f"Macro-F1 Score: {macro_f1_val:.4f}")
print(f"Accuracy:       {acc_val:.4f}\\n")

# Classification Report
print("--- Detailed Classification Report ---")
target_names = [Config.ID2LABEL[i] for i in range(Config.NUM_LABELS)]
print(classification_report(val_labels, val_preds, target_names=target_names, digits=4))

# Confusion Matrix
cm = confusion_matrix(val_labels, val_preds)
cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Raw counts
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=target_names, yticklabels=target_names, ax=axes[0])
axes[0].set_title("Confusion Matrix (Counts)", fontsize=13, fontweight="bold")
axes[0].set_xlabel("Predicted Label")
axes[0].set_ylabel("True Label")

# Normalized
sns.heatmap(cm_norm, annot=True, fmt=".2%", cmap="Blues", xticklabels=target_names, yticklabels=target_names, ax=axes[1])
axes[1].set_title("Confusion Matrix (Normalized)", fontsize=13, fontweight="bold")
axes[1].set_xlabel("Predicted Label")
axes[1].set_ylabel("True Label")

plt.tight_layout()
plt.show()

# Đánh giá theo ngôn ngữ nếu có cột language
if LANG_COL is not None and LANG_COL in val_sub_df.columns:
    print("\\n--- Macro-F1 Breakdown by Language ---")
    val_sub_df["val_pred"] = val_preds
    for lang, group in val_sub_df.groupby(LANG_COL):
        lang_f1 = f1_score(group["label_id"], group["val_pred"], average="macro", zero_division=0)
        print(f" - {lang:<12}: Macro-F1 = {lang_f1:.4f} (N={len(group)})")
''')

# --- CELL 21: Logit Bias Tuning Markdown ---
add_md("""---
## 🎛️ 8. Tối ưu ngưỡng dự đoán (Logit Bias Tuning)

### Nguyên lý:
Mô hình chuẩn dự đoán theo quy tắc argmax:
$$\\hat{y} = \\arg\\max_c (z_c)$$

Tuy nhiên, vì Macro-F1 đánh trọng số ngang nhau cho cả 3 nhãn ($1/3$ cho mỗi nhãn), việc dự đoán thận trọng lớp `PROMPT_INJECTION` (chỉ 7% tập dữ liệu) có thể khiến Recall của lớp này thấp, làm kéo giảm Macro-F1 tổng thể.

Chúng ta tối ưu một bộ bias vector $\\mathbf{b} = [b_0, b_1, b_2]$:
$$\\hat{y} = \\arg\\max_c (z_c + b_c)$$

Sử dụng thuật toán tối ưu `Powell` trên tập Validation để tìm vector $\\mathbf{b}$ tối đa hóa Macro-F1.
> **Lưu ý quan trọng:** Quá trình tối ưu chỉ thực hiện trên Validation Logits, hoàn toàn không chạm vào Test Data!
""")

# --- CELL 22: Logit Bias Search Algorithm ---
add_code('''# ==============================================================================
# 14. POST-PROCESSING: THRESHOLD / LOGIT BIAS OPTIMIZATION
# ==============================================================================
def optimize_logit_biases(logits, labels):
    """
    Tìm kiếm bias vector b sao cho np.argmax(logits + b) tối đa hóa Macro-F1
    """
    initial_bias = np.zeros(Config.NUM_LABELS)
    
    def loss_function(bias):
        adjusted_logits = logits + bias
        preds = np.argmax(adjusted_logits, axis=-1)
        score = f1_score(labels, preds, average="macro", zero_division=0)
        return -score  # Minimize negative F1

    # Tối ưu bằng thuật toán Powell (rất phù hợp cho hàm mục tiêu không khả vi như F1)
    res = minimize(
        loss_function, 
        initial_bias, 
        method="Powell", 
        options={"maxiter": 200, "ftol": 1e-4}
    )
    
    best_bias = res.x
    # Đặt bias lớp 0 (BENIGN) về 0 làm chuẩn
    best_bias = best_bias - best_bias[0]
    
    # Đánh giá lại
    raw_preds = np.argmax(logits, axis=-1)
    raw_f1 = f1_score(labels, raw_preds, average="macro", zero_division=0)
    
    tuned_preds = np.argmax(logits + best_bias, axis=-1)
    tuned_f1 = f1_score(labels, tuned_preds, average="macro", zero_division=0)
    
    return best_bias, raw_f1, tuned_f1

print("Đang tìm kiếm Logit Bias tối ưu trên tập Validation...")
best_bias, raw_f1, tuned_f1 = optimize_logit_biases(val_logits, val_labels)

print(f"\\n--- KẾT QUẢ TỐI ƯU LOGIT BIAS ---")
print(f"Validation Macro-F1 Trước khi tối ưu: {raw_f1:.4f}")
print(f"Validation Macro-F1 Sau khi tối ưu:   {tuned_f1:.4f}")
print(f"Cải thiện:                            {tuned_f1 - raw_f1:+.4f}")
print("\\nVector Bias tối ưu:")
for idx, name in Config.ID2LABEL.items():
    print(f" - Bias {name:<18}: {best_bias[idx]:+.4f}")

# Chỉ áp dụng bias nếu cải thiện thực sự trên tập validation
if tuned_f1 > raw_f1:
    print("\\n✅ Áp dụng Logit Bias Tuning cho bước dự đoán tập Test!")
    final_bias = best_bias
else:
    print("\\n⚠️ Logit Bias không giúp tăng điểm, giữ nguyên argmax thông thường.")
    final_bias = np.zeros(Config.NUM_LABELS)
''')

# --- CELL 23: Test Prediction Markdown ---
add_md("""---
## 🔮 9. Dự đoán trên tập Test & Xuất file Submission

Quy trình:
1. Tokenize toàn bộ tập `test.csv` (6.000 dòng).
2. Dự đoán logits qua mô hình tốt nhất (`best_xlm_roberta`).
3. Cộng `final_bias` vào logits và lấy $\\arg\\max$.
4. Map label ID sang string (`BENIGN`, `JAILBREAK`, `PROMPT_INJECTION`).
5. **Kiểm tra chặt chẽ tính toàn vẹn (Assertion Checks):**
   - Đủ chính xác 6.000 dòng.
   - Các ID duy nhất và khớp thứ tự với `test.csv`.
   - Không chứa bất kỳ giá trị NaN / Null nào.
   - Nhãn nằm trong tập 3 nhãn hợp lệ.
6. Lưu file ra `/kaggle/working/submission.csv`.
""")

# --- CELL 24: Test Prediction Code ---
add_code('''# ==============================================================================
# 15. INFERENCE ON TEST SET
# ==============================================================================
print(f"Chuẩn bị dữ liệu Test ({len(test_df)} dòng)...")
test_hf_dataset = prepare_hf_dataset(test_df, tokenizer, is_test=True)

print("Đang chạy dự đoán Test trên GPU...")
test_predictions_raw = trainer.predict(test_hf_dataset)
test_logits = test_predictions_raw.predictions

# Áp dụng Logit Bias đã tối ưu
test_adjusted_logits = test_logits + final_bias
test_pred_ids = np.argmax(test_adjusted_logits, axis=-1)

# Ánh xạ ngược sang tên nhãn
test_pred_labels = [Config.ID2LABEL[idx] for idx in test_pred_ids]

print("Hoàn thành dự đoán trên toàn bộ tập Test!")
''')

# --- CELL 25: Verification & Export Code ---
add_code('''# ==============================================================================
# 16. SUBMISSION GENERATION & STRICT INTEGRITY CHECKS
# ==============================================================================
submission_df = pd.DataFrame({
    "id": test_df[ID_COL],
    "label": test_pred_labels
})

print("=== KIỂM TRA TÍNH TOÀN VẸN CỦA SUBMISSION ===")

# 1. Kiểm tra số lượng dòng
print(f"1. Số dòng: {len(submission_df)} (Kỳ vọng: 6000)")
assert len(submission_df) == 6000 or len(submission_df) == len(test_df), \\
    f"Lỗi: Số lượng dòng ({len(submission_df)}) không khớp với test set ({len(test_df)})!"

# 2. Kiểm tra tính duy nhất của ID
print("2. ID is unique:", submission_df["id"].is_unique)
assert submission_df["id"].is_unique, "Lỗi: ID bị trùng lặp!"

# 3. Kiểm tra thứ tự ID khớp 100% với test.csv
id_match = (submission_df["id"].values == test_df[ID_COL].values).all()
print("3. ID matches test.csv exactly:", id_match)
assert id_match, "Lỗi: Thứ tự ID không khớp với test.csv!"

# 4. Kiểm tra nhãn hợp lệ
valid_labels = set(Config.LABELS)
current_labels = set(submission_df["label"].unique())
print(f"4. Các nhãn trong submission: {current_labels}")
assert current_labels.issubset(valid_labels), f"Lỗi: Xuất hiện nhãn không hợp lệ: {current_labels - valid_labels}"

# 5. Kiểm tra NaN / Null
null_count = submission_df.isnull().sum().sum()
print(f"5. Số giá trị null/NaN: {null_count}")
assert null_count == 0, "Lỗi: Submission chứa giá trị Null/NaN!"

print("\\n✅ TẤT CẢ KIỂM TRA ĐỀU HỢP LỆ!")

# Thống kê phân bố nhãn dự đoán trên Test
print("\\n=== PHÂN BỐ NHÃN DỰ ĐOÁN TRÊN TEST SET ===")
test_label_counts = submission_df["label"].value_counts()
test_label_pct = submission_df["label"].value_counts(normalize=True) * 100

test_summary = pd.DataFrame({
    "Test Count": test_label_counts,
    "Test Percentage (%)": test_label_pct.round(2)
})
display(test_summary)

# Xuất file submission.csv
output_dir = os.path.dirname(Config.SUBMISSION_PATH)
if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)

submission_df.to_csv(Config.SUBMISSION_PATH, index=False)
print(f"\\n📁 Đã lưu file submission tại: {Config.SUBMISSION_PATH}")

# Lưu thêm 1 bản dự phòng tại thư mục làm việc hiện tại
submission_df.to_csv(Config.LOCAL_SUBMISSION_PATH, index=False)
print(f"📁 Bản sao lưu tại: {Config.LOCAL_SUBMISSION_PATH}")

print("\\n--- Preview 5 dòng đầu ---")
display(submission_df.head(5))

print("\\n--- Preview 5 dòng cuối ---")
display(submission_df.tail(5))
''')

# --- CELL 26: Strategy Roadmap Markdown ---
add_md("""---
## 🏆 10. Chiến lược tối ưu với ngân sách 6 lượt Submission

Để tối đa hóa thứ hạng trên Kaggle Leaderboard mà không bị lãng phí lượt nộp bài, hãy tuân thủ chiến lược 6 bước:

| Giai đoạn | Thử nghiệm | Mô tả chi tiết | Mục tiêu kỳ vọng |
| :---: | :--- | :--- | :--- |
| **Sub 1** | **XLM-RoBERTa Baseline** | Standard Cross-Entropy, max_length=256, 4 epochs | Tạo điểm benchmark ban đầu và xác thực submission hợp lệ. |
| **Sub 2** | **XLM-RoBERTa + Class Weights** | Weighted Cross-Entropy (Inverse Sqrt), phạt nặng hơn khi đoán sai `PROMPT_INJECTION` | Cải thiện F1 của lớp thiểu số, kéo tăng Macro-F1 tổng thể. |
| **Sub 3** | **Tối ưu Hyperparameters** | Thử `learning_rate = 1.5e-5` hoặc `3e-5`, tăng `max_length = 384` nếu GPU đủ VRAM | Bắt trọn vẹn các prompt tấn công dài. |
| **Sub 4** | **Logit Bias Post-Processing** | Điều chỉnh bias logits $z_c + b_c$ tối ưu trên tập Validation | Tăng thêm từ 0.005 - 0.015 Macro-F1 mà không cần retrain mô hình. |
| **Sub 5** | **Thử nghiệm Backbone thứ 2** | Huấn luyện `mmBERT-base` hoặc `DeBERTa-v3 Prompt Injection v2` với cùng pipeline | So sánh hiệu năng đa ngôn ngữ giữa các kiến trúc. |
| **Sub 6** | **Ensemble / Blend cuối cùng** | Weighted Probability Average giữa Checkpoint XLM-RoBERTa tốt nhất và mmBERT/DeBERTa | Giảm variance, tăng tính tổng quát hóa và chốt điểm cao nhất. |

### 💡 Lưu ý cốt lõi khi thi đấu:
1. **Luôn tin tưởng Validation F1:** Chỉ nộp submission mới lên Kaggle nếu điểm Validation cải thiện rõ rệt so với bản cũ.
2. **Cố định Validation Split:** Giữ nguyên random seed (`seed=42`) cho việc chia Train/Validation để mọi so sánh đều công bằng.
3. **Bảo toàn ký tự đặc biệt:** Không loại bỏ dấu câu, emoji hay ký tự lạ trong prompt, vì đây thường là dấu hiệu nhận diện đặc trưng của các payload prompt injection.
""")

output_path = r"d:\PARA Method\Project\RMIT-Hackathon-2026\Tai\multilingual_prompt_attack_classification.ipynb"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)

print(f"Notebook successfully created at: {output_path}")
print(f"Total cells: {len(notebook['cells'])}")
