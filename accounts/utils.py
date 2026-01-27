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
FACE_MATCH_THRESHOLD = 0.82
from django.conf import settings

API_KEY = settings.ELASTIC_EMAIL_API_KEY
FROM_EMAIL = settings.ELASTIC_EMAIL_FROM



def send_otp_email(email, otp):
    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json",
    }

    payload = {
        "sender": {
            "name": settings.BREVO_SENDER_NAME,
            "email": settings.BREVO_SENDER_EMAIL,
        },
        "to": [{"email": email}],
        "subject": "Your LinkX OTP",
        "htmlContent": f"""
            <h2>LinkX Verification</h2>
            <p>Your OTP is:</p>
            <h1>{otp}</h1>
            <p>This OTP expires in 10 minutes.</p>
        """,
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

FACE_MATCH_THRESHOLD = 0.82
import requests
from django.conf import settings

API_KEY = settings.ELASTIC_EMAIL_API_KEY
FROM_EMAIL = settings.ELASTIC_EMAIL_FROM


def send_otp_email(email, otp):
    url = "https://api.elasticemail.com/v4/emails"

    payload = {
        "Recipients": {
            "To": [email]
        },
        "Content": {
            "From": FROM_EMAIL,
            "Subject": "Your LinkX OTP",
            "Body": [
                {
                    "ContentType": "HTML",
                    "Content": f"""
                        <h2>LinkX Verification</h2>
                        <p>Your OTP is:</p>
                        <h1>{otp}</h1>
                        <p>This OTP expires in 10 minutes.</p>
                    """
                }
            ]
        }
    }

    headers = {
        "X-ElasticEmail-ApiKey": API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()


    