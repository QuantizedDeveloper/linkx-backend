import random
from django.utils import timezone
from datetime import timedelta
import numpy as np


def generate_otp():
    return str(random.randint(1000, 9999))

def otp_expiry():
    return timezone.now() + timedelta(minutes=5)

def reset_token_expiry():
    return timezone.now() + timedelta(minutes=10)


# utils.py
import numpy as np

EMBEDDING_SIZE = 128
CONSISTENCY_THRESHOLD = 0.60


def validate_embedding(vec):
    if not isinstance(vec, list):
        return False
    if len(vec) != EMBEDDING_SIZE:
        return False
    if not all(isinstance(x, (int, float)) for x in vec):
        return False

    arr = np.array(vec, dtype=np.float32)

    if np.isnan(arr).any():
        return False
    if np.linalg.norm(arr) < 0.5:
        return False

    return True


def cosine_distance(a, b):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    return 1 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def check_same_person(embeddings):
    base = embeddings[0]
    distances = [cosine_distance(base, e) for e in embeddings[1:]]
    return max(distances) < CONSISTENCY_THRESHOLD


def canonical_embedding(embeddings):
    return np.mean(embeddings, axis=0)
    






# utils.py (ADD BELOW existing functions)



def cosine_similarity(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


FACE_MATCH_THRESHOLD = 0.82
