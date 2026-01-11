# feature_5_summarization.py

import re
import torch
import numpy as np
from transformers import DistilBertTokenizer, DistilBertModel
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize import sent_tokenize

# -------------------------------
# CONFIG (LOCKED)
# -------------------------------
MAX_SENTENCES = 2
MIN_TEXT_LENGTH = 15

MODEL_NAME = "distilbert-base-uncased"

# -------------------------------
# LOAD MODEL (ONCE)
# -------------------------------
tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)
model = DistilBertModel.from_pretrained(MODEL_NAME)
model.eval()

# -------------------------------
# VALIDATION
# -------------------------------
def is_meaningful_text(text):
    if not isinstance(text, str):
        return False
    text = text.strip()
    if len(text) < MIN_TEXT_LENGTH:
        return False
    if not re.search(r"[aeiouAEIOU]", text):
        return False
    if len(set(text)) < 5:
        return False
    if len(text.split()) < 3:
        return False
    return True

# -------------------------------
# FALLBACK SENTENCE SPLIT
# -------------------------------
def safe_sentence_split(text):
    try:
        return sent_tokenize(text)
    except:
        return [s.strip() for s in text.split(".") if len(s.strip()) > 5]

# -------------------------------
# EMBEDDING
# -------------------------------
def encode_sentence(sentence):
    inputs = tokenizer(
        sentence,
        return_tensors="pt",
        truncation=True,
        max_length=128,
        padding=True
    )
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state[:, 0, :].numpy()

# -------------------------------
# MAIN API
# -------------------------------
def generate_summary(message):
    if not is_meaningful_text(message):
        return None

    sentences = safe_sentence_split(message)

    if len(sentences) <= MAX_SENTENCES:
        return message.strip()

    embeddings = np.vstack([encode_sentence(s) for s in sentences])
    centroid = embeddings.mean(axis=0, keepdims=True)

    scores = cosine_similarity(embeddings, centroid).flatten()
    top_ids = np.argsort(scores)[::-1][:MAX_SENTENCES]

    return " ".join([sentences[i] for i in top_ids])
