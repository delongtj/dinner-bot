import secrets
from datetime import datetime, timedelta

from db.connection import query


def register_user(email, name):
    """Create a new family and user for a first-time sign-in.

    Returns dict with user and family info.
    """
    family_name = f"{name}'s Family" if name else "My Family"
    family = query(
        "INSERT INTO families (name) VALUES (%s) RETURNING *",
        (family_name,),
        fetch_one=True,
    )

    user = query(
        "INSERT INTO users (family_id, email, name) VALUES (%s, %s, %s) RETURNING *",
        (str(family["id"]), email, name),
        fetch_one=True,
    )

    return {"user": user, "family": family}


def join_family_with_invite(email, name, invite_code):
    """Join an existing family using an invite code.

    Returns dict with user and family info.
    Raises ValueError if the code is invalid, used, or expired.
    """
    invite = query(
        "SELECT * FROM family_invites WHERE code = %s",
        (invite_code,),
        fetch_one=True,
    )

    if not invite:
        raise ValueError("Invalid invite code")

    if invite["used_by"] is not None:
        raise ValueError("Invite code has already been used")

    if invite["expires_at"] < datetime.utcnow():
        raise ValueError("Invite code has expired")

    family_id = str(invite["family_id"])

    user = query(
        "INSERT INTO users (family_id, email, name) VALUES (%s, %s, %s) RETURNING *",
        (family_id, email, name),
        fetch_one=True,
    )

    # Mark invite as used
    query(
        "UPDATE family_invites SET used_by = %s WHERE id = %s RETURNING id",
        (str(user["id"]), str(invite["id"])),
        fetch_one=True,
    )

    family = query(
        "SELECT * FROM families WHERE id = %s",
        (family_id,),
        fetch_one=True,
    )

    return {"user": user, "family": family}


def create_invite(family_id, user_id):
    """Generate a short random invite code with 7-day expiry.

    Returns dict with code and expires_at.
    """
    code = secrets.token_urlsafe(6).upper()[:8]
    expires_at = datetime.utcnow() + timedelta(days=7)

    invite = query(
        """INSERT INTO family_invites (family_id, code, created_by, expires_at)
           VALUES (%s, %s, %s, %s) RETURNING code, expires_at""",
        (family_id, code, user_id, expires_at),
        fetch_one=True,
    )

    return invite


def get_family_members(family_id):
    """List all users in a family."""
    return query(
        "SELECT id, email, name, created_at FROM users WHERE family_id = %s ORDER BY created_at",
        (family_id,),
    )
