from fastapi import APIRouter

from app.api.routes import allowlists, audit_logs, auth, config_management, dashboard, emails, incidents, issue_logs, mail_accounts, rules

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(emails.router, prefix="/emails", tags=["emails"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])
api_router.include_router(mail_accounts.router, prefix="/mail-accounts", tags=["mail-accounts"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])
api_router.include_router(allowlists.router, prefix="/allowlists", tags=["allowlists"])
api_router.include_router(config_management.router, prefix="/config-management", tags=["config-management"])
api_router.include_router(issue_logs.router, prefix="/issue-logs", tags=["issue-logs"])
