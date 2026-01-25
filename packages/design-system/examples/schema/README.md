# JHG Databricks Schema Template

Standard schema template for JHG Flask applications using Databricks Unity Catalog.

## Quick Start

1. Open Databricks SQL workspace
2. Edit `create_schema.sql` and replace:
   - `{catalog}` with your Unity Catalog name (e.g., `jhg_prod`)
   - `{schema}` with your application schema name (e.g., `my_app`)
3. Execute the SQL script

## Tables

| Table | Purpose |
|-------|---------|
| `audit_log` | Tracks all user actions and system events |
| `cache_metadata` | Metadata for distributed caching (optional) |
| `user_preferences` | User-specific settings and preferences |
| `app_config` | Runtime application configuration |
| `feature_flags` | Feature flag management |
| `sessions` | Custom session storage (optional) |

## Views

| View | Purpose |
|------|---------|
| `v_recent_audit` | Last 7 days of audit events |
| `v_active_sessions` | Currently active sessions |
| `v_enabled_features` | All enabled feature flags |

## Integration with JHG Design System

### Audit Logging

```python
from jhg_patterns.ds.databricks import AuditLogger, get_connector

# Initialize
audit = AuditLogger(app_name="my-app", table="audit_log")

# Log actions
audit.log("user_login", user_id="123", ip_address="192.168.1.1")
audit.log("data_export", user_id="123", metadata={"rows": 1000})

# Log from Flask request
@app.route("/api/action")
def action():
    audit.log_request("api_call")
    return jsonify({"status": "ok"})
```

### Feature Flags

```python
def is_feature_enabled(flag_name: str) -> bool:
    """Check if a feature flag is enabled."""
    connector = get_connector()
    result = connector.query_one(
        "SELECT is_enabled, rollout_percentage FROM feature_flags WHERE flag_name = :flag",
        {"flag": flag_name}
    )
    if not result or not result["is_enabled"]:
        return False

    # Handle gradual rollout
    if result["rollout_percentage"] < 100:
        # Use user_id hash to determine if user is in rollout
        import hashlib
        user_hash = int(hashlib.md5(current_user_id.encode()).hexdigest(), 16)
        return (user_hash % 100) < result["rollout_percentage"]

    return True
```

### Configuration

```python
def get_config(key: str, default=None):
    """Get configuration value from database."""
    connector = get_connector()
    result = connector.query_one(
        "SELECT config_value FROM app_config WHERE config_key = :key",
        {"key": key}
    )
    return result["config_value"] if result else default
```

## Best Practices

1. **Audit Everything**: Log all significant user actions
2. **Use Feature Flags**: Roll out new features gradually
3. **Cache Aggressively**: Use TTL cache for frequently accessed data
4. **Monitor**: Set up alerts on audit log for security events
5. **Optimize**: Run `OPTIMIZE` on tables periodically

## Maintenance

```sql
-- Optimize audit log (run weekly)
OPTIMIZE audit_log;

-- Vacuum old files (run monthly)
VACUUM audit_log;

-- Clean expired sessions (run daily)
DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP();

-- Clean old audit logs (run monthly, keep 90 days)
DELETE FROM audit_log WHERE timestamp < DATEADD(DAY, -90, CURRENT_TIMESTAMP());
```
