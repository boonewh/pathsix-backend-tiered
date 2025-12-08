from quart import Blueprint, request
from app.utils.auth_utils import requires_auth
from app.utils.logging_utils import log_error as log_error_util
import logging

utils_bp = Blueprint("utils", __name__, url_prefix="/api")

@utils_bp.route("/log-error", methods=["POST"])
@requires_auth()  # ✅ Now requires authentication
async def log_error():
    """
    Legacy endpoint for frontend error logging.
    
    NOTE: This is deprecated in favor of Sentry. 
    Kept for backward compatibility with older frontend versions.
    """
    user = request.user
    data = await request.get_json()
    message = data.get("message", "No message provided")
    context = data.get("context", {})
    
    # Add user/tenant context for filtering
    context["tenant_id"] = user.tenant_id
    context["user_id"] = user.id
    context["user_email"] = user.email

    logging.error(f"[Frontend Error] {message} | Context: {context}")
    return {"status": "logged"}
