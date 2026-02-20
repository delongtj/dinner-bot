import firebase_admin
from firebase_admin import auth as firebase_auth

# Initialize Firebase Admin SDK (uses GOOGLE_APPLICATION_CREDENTIALS or
# Application Default Credentials when running on GCP).
if not firebase_admin._apps:
    firebase_admin.initialize_app()


def verify_token(request):
    """Extract and verify a Firebase ID token from the Authorization header.

    Returns a dict with at least 'uid' and 'email' on success.
    Raises ValueError on missing/invalid token.
    """
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise ValueError("Missing or malformed Authorization header")

    token = header[len("Bearer "):]
    decoded = firebase_auth.verify_id_token(token)

    if not decoded.get("email"):
        raise ValueError("Token missing email claim")

    return decoded
