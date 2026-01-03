from quart import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError
from app.models import User, Tenant, TenantUsage, TenantStatus, EmailVerification, EmailVerificationStatus, Role
from app.database import SessionLocal
from app.utils.auth_utils import (
    verify_password,
    create_token,
    hash_password,
    generate_reset_token,
    verify_reset_token
)
from app.utils.auth_utils import requires_auth
from app.utils.email_utils import send_email
from app.utils.rate_limiter import rate_limit
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import secrets


auth_bp = Blueprint("auth", __name__, url_prefix="/api")

@auth_bp.route("/login", methods=["POST"])
@rate_limit(max_attempts=5, window_seconds=60)  # 5 login attempts per minute per IP
async def login():
    data = await request.get_json()

    email = data.get("email", "").lower().strip()
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing credentials"}), 400

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(email=email).first()
        if not user or not verify_password(password, user.password_hash):
            return jsonify({"error": "Invalid credentials"}), 401

        # Require email verification before login
        if not user.email_verified:
            return jsonify({
                "error": "Email not verified. Please check your email for the verification link.",
                "email_verified": False,
                "user_id": user.id
            }), 403

        token = create_token(user)

        response = jsonify({
            "user": {
                "id": user.id,
                "email": user.email,
                "roles": [role.name for role in user.roles]
            },
            "token": token
        })
        response.headers["Cache-Control"] = "no-store"
        return response
    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": "Server error"}), 500
    finally:
        session.close()

@auth_bp.route("/forgot-password", methods=["POST"])
@rate_limit(max_attempts=3, window_seconds=300)  # 3 password reset attempts per 5 minutes per IP
async def forgot_password():
    data = await request.get_json()
    email = data.get("email", "").lower().strip()
    if not email:
        return jsonify({"error": "Missing email"}), 400

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(email=email).first()
        if not user:
            return jsonify({"message": "If that account exists, an email was sent."})  # Don't reveal info

        token = generate_reset_token(email)
        reset_link = f"{current_app.config['FRONTEND_URL']}/reset-password/{token}"

        await send_email(
            subject="Password Reset Request",
            recipient=email,
            body=f"Click to reset your password: {reset_link}"
        )
        print("Reset link:", reset_link)

        return jsonify({"message": "If that account exists, a reset email was sent."})
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Server error"}), 500
    finally:
        session.close()

@auth_bp.route("/reset-password", methods=["POST"])
async def reset_password():
    data = await request.get_json()
    token = data.get("token")
    new_password = data.get("password")

    if not token or not new_password:
        return jsonify({"error": "Missing token or password"}), 400

    email = verify_reset_token(token)
    if not email:
        return jsonify({"error": "Invalid or expired token"}), 400

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.password_hash = hash_password(new_password)
        session.commit()

        return jsonify({"message": "Password updated successfully"})
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Server error"}), 500
    finally:
        session.close()

@auth_bp.route("/change-password", methods=["POST"])
@requires_auth()
async def change_password():
    data = await request.get_json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    user = request.user

    if not current_password or not new_password:
        return jsonify({"error": "Missing required fields"}), 400

    if not verify_password(current_password, user.password_hash):
        return jsonify({"error": "Incorrect current password"}), 403

    session = SessionLocal()
    try:
        user = session.get(User, user.id)
        user.password_hash = hash_password(new_password)
        session.commit()
        return jsonify({"message": "Password changed successfully"})
    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Server error"}), 500
    finally:
        session.close()


@auth_bp.route("/me", methods=["GET"])
@requires_auth()
async def get_me():
    user = request.user
    return jsonify({
        "id": user.id,
        "email": user.email,
        "roles": [r.name for r in user.roles]
    })


@auth_bp.route("/signup", methods=["POST"])
@rate_limit(max_attempts=3, window_seconds=300)
async def signup():
    """
    Create new user account with tenant and email verification.
    All signups default to free tier. Upgrades handled via /api/billing/create-checkout-session.

    Request body:
        {
            "email": "user@example.com",
            "password": "securepassword",
            "company_name": "Optional Company Name"
        }

    Returns 201 with user_id and tenant_id, sends verification email.
    """
    data = await request.get_json()

    email = data.get("email", "").lower().strip()
    password = data.get("password")
    company_name = data.get("company_name", "").strip()

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    session = SessionLocal()
    try:
        # Check if email already exists
        existing_user = session.query(User).filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "Email already registered"}), 409

        # Create Tenant (always starts on free tier)
        tenant = Tenant(
            plan_tier='free',
            status=TenantStatus.active,
            billing_email=email,
            company_name=company_name or None,
            created_at=datetime.utcnow()
        )
        session.add(tenant)
        session.flush()

        # Create TenantUsage with zeroed counters
        usage = TenantUsage(
            tenant_id=tenant.id,
            storage_bytes=0,
            db_record_count=0,
            api_calls_today=0,
            emails_this_month=0,
            api_calls_reset_at=datetime.utcnow() + timedelta(days=1),
            emails_reset_at=datetime.utcnow() + relativedelta(months=1)
        )
        session.add(usage)

        # Create User (email_verified=False initially)
        user = User(
            tenant_id=tenant.id,
            email=email,
            password_hash=hash_password(password),
            email_verified=False,
            created_at=datetime.utcnow()
        )
        session.add(user)
        session.flush()

        # Assign admin role to first user
        admin_role = session.query(Role).filter_by(name='admin').first()
        if admin_role:
            user.roles.append(admin_role)

        # Create email verification token (24-hour expiry)
        verification_token = secrets.token_urlsafe(32)
        verification = EmailVerification(
            email=email,
            user_id=user.id,
            tenant_id=tenant.id,
            token=verification_token,
            status=EmailVerificationStatus.pending,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            created_at=datetime.utcnow()
        )
        session.add(verification)
        session.commit()

        # Send verification email (handle gracefully if email not configured)
        verification_link = f"{current_app.config['FRONTEND_URL']}/verify-email/{verification_token}"
        try:
            await send_email(
                subject="Verify Your Email - PathSix CRM",
                recipient=email,
                body=f"Welcome to PathSix CRM!\n\nClick to verify your email: {verification_link}\n\nThis link expires in 24 hours."
            )
        except Exception as e:
            print(f"Email send failed (development): {str(e)}")

        print(f"Verification link: {verification_link}")

        return jsonify({
            "message": "Account created. Please check your email to verify your account.",
            "user_id": user.id,
            "tenant_id": tenant.id
        }), 201

    except SQLAlchemyError as e:
        session.rollback()
        return jsonify({"error": "Server error"}), 500
    finally:
        session.close()


@auth_bp.route("/verify-email/<token>", methods=["POST"])
async def verify_email(token):
    """
    Verify user email with token and auto-login.

    Returns JWT token for immediate login after verification.
    """
    session = SessionLocal()
    try:
        # Find verification record
        verification = session.query(EmailVerification).filter_by(
            token=token,
            status=EmailVerificationStatus.pending
        ).first()

        if not verification:
            return jsonify({"error": "Invalid or already used verification token"}), 400

        # Check expiration
        if verification.expires_at < datetime.utcnow():
            verification.status = EmailVerificationStatus.expired
            session.commit()
            return jsonify({"error": "Verification token expired. Please request a new one."}), 400

        # Mark user as verified
        user = session.query(User).filter_by(id=verification.user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.email_verified = True
        verification.status = EmailVerificationStatus.verified
        session.commit()

        # Generate JWT token for auto-login
        jwt_token = create_token(user)

        return jsonify({
            "message": "Email verified successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "tenant_id": user.tenant_id,
                "roles": [role.name for role in user.roles]
            },
            "token": jwt_token
        }), 200

    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Server error"}), 500
    finally:
        session.close()


@auth_bp.route("/resend-verification", methods=["POST"])
@rate_limit(max_attempts=3, window_seconds=600)
async def resend_verification():
    """
    Resend verification email for unverified accounts.

    Request body:
        {
            "email": "user@example.com"
        }
    """
    data = await request.get_json()
    email = data.get("email", "").lower().strip()

    if not email:
        return jsonify({"error": "Missing email"}), 400

    session = SessionLocal()
    try:
        # Find user
        user = session.query(User).filter_by(email=email).first()
        if not user:
            # Don't reveal if user exists
            return jsonify({"message": "If that account exists and is unverified, a new verification email was sent."}), 200

        # Check if already verified
        if user.email_verified:
            return jsonify({"error": "Email already verified"}), 400

        # Expire old pending verifications
        old_verifications = session.query(EmailVerification).filter_by(
            user_id=user.id,
            status=EmailVerificationStatus.pending
        ).all()
        for old_ver in old_verifications:
            old_ver.status = EmailVerificationStatus.expired

        # Create new verification token
        verification_token = secrets.token_urlsafe(32)
        verification = EmailVerification(
            email=email,
            user_id=user.id,
            tenant_id=user.tenant_id,
            token=verification_token,
            status=EmailVerificationStatus.pending,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            created_at=datetime.utcnow()
        )
        session.add(verification)
        session.commit()

        # Send new verification email (handle gracefully if email not configured)
        verification_link = f"{current_app.config['FRONTEND_URL']}/verify-email/{verification_token}"
        try:
            await send_email(
                subject="Verify Your Email - PathSix CRM",
                recipient=email,
                body=f"Here's your new verification link:\n\n{verification_link}\n\nThis link expires in 24 hours."
            )
        except Exception as e:
            print(f"Email send failed (development): {str(e)}")

        print(f"New verification link: {verification_link}")

        return jsonify({"message": "If that account exists and is unverified, a new verification email was sent."}), 200

    except SQLAlchemyError:
        session.rollback()
        return jsonify({"error": "Server error"}), 500
    finally:
        session.close()
