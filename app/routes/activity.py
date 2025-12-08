from quart import Blueprint, jsonify, request
from sqlalchemy import func, desc, case
from app.database import SessionLocal
from app.models import ActivityLog, Client, Lead, Project, Account
from app.utils.auth_utils import requires_auth


activity_bp = Blueprint("activity", __name__, url_prefix="/api/activity")


@activity_bp.route("/recent", methods=["GET"])
@requires_auth()
async def recent_activity():
    user = request.user
    session = SessionLocal()
    try:
        limit = int(request.args.get("limit", 10))
        limit = min(limit, 50)

        # Get most recent log per entity_type + entity_id for this user
        subquery = (
            session.query(
                ActivityLog.entity_type,
                ActivityLog.entity_id,
                func.max(ActivityLog.timestamp).label("last_touched")
            )
            .filter(
                ActivityLog.user_id == user.id,
                ActivityLog.tenant_id == user.tenant_id
            )
            .group_by(ActivityLog.entity_type, ActivityLog.entity_id)
            .subquery()
        )

        results = session.query(
            subquery.c.entity_type,
            subquery.c.entity_id,
            subquery.c.last_touched
        ).order_by(desc(subquery.c.last_touched)).limit(limit).all()

        # Collect entity IDs by type for bulk loading
        client_ids = []
        lead_ids = []
        project_ids = []
        account_ids = []
        
        for row in results:
            if row.entity_type == "client":
                client_ids.append(row.entity_id)
            elif row.entity_type == "lead":
                lead_ids.append(row.entity_id)
            elif row.entity_type == "project":
                project_ids.append(row.entity_id)
            elif row.entity_type == "account":
                account_ids.append(row.entity_id)
        
        # Bulk load all entities (prevents N+1)
        clients_map = {}
        if client_ids:
            clients = session.query(Client).filter(
                Client.id.in_(client_ids),
                Client.tenant_id == user.tenant_id,
                Client.deleted_at == None
            ).all()
            clients_map = {c.id: c for c in clients}
        
        leads_map = {}
        if lead_ids:
            leads = session.query(Lead).filter(
                Lead.id.in_(lead_ids),
                Lead.tenant_id == user.tenant_id,
                Lead.deleted_at == None
            ).all()
            leads_map = {l.id: l for l in leads}
        
        projects_map = {}
        if project_ids:
            projects = session.query(Project).filter(
                Project.id.in_(project_ids),
                Project.tenant_id == user.tenant_id
            ).all()
            projects_map = {p.id: p for p in projects}
        
        accounts_map = {}
        if account_ids:
            accounts = session.query(Account).filter(
                Account.id.in_(account_ids),
                Account.tenant_id == user.tenant_id
            ).all()
            accounts_map = {a.id: a for a in accounts}

        # Build output using cached entities
        output = []
        for row in results:
            entity_type = row.entity_type
            entity_id = row.entity_id
            last_touched = row.last_touched
            name = None
            profile_link = None

            if entity_type == "client":
                client = clients_map.get(entity_id)
                if client:
                    name = client.name
                    profile_link = f"/clients/{client.id}"

            elif entity_type == "lead":
                lead = leads_map.get(entity_id)
                if lead:
                    name = lead.name
                    profile_link = f"/leads/{lead.id}"

            elif entity_type == "project":
                project = projects_map.get(entity_id)
                if project:
                    name = project.project_name
                    profile_link = f"/projects/{project.id}"

            elif entity_type == "account":
                account = accounts_map.get(entity_id)
                if account and account.client and account.client.tenant_id == user.tenant_id and account.client.deleted_at is None:
                    name = account.account_name or account.account_number
                    profile_link = f"/clients/{account.client.id}"

            if name and profile_link:
                output.append({
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "name": name,
                    "last_touched": last_touched.isoformat() + "Z",
                    "profile_link": profile_link
                })

        response = jsonify(output)
        response.headers["Cache-Control"] = "no-store"
        return response

    finally:
        session.close()