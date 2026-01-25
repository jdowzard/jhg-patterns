# jhg-patterns-flask

Flask utilities for JHG projects, including TTL caching for external data sources.

## Installation

```bash
pip install jhg-patterns-flask

# With Databricks SQL support
pip install jhg-patterns-flask[databricks]
```

## TTL Cache

Thread-safe in-memory cache with configurable time-to-live per key. Designed for Flask apps that read from external data sources (databases, APIs) with infrequent updates.

### Basic Usage

```python
from jhg_patterns.flask import TTLCache

# Create cache
cache = TTLCache()

# Get data (fetches from source if cache expired)
def get_users():
    return cache.get('users', fetch_fn=lambda: db.query("SELECT * FROM users"))

# Invalidate on write
def update_user(user_id, data):
    db.update(user_id, data)
    cache.invalidate('users')
```

### Custom TTLs

```python
cache = TTLCache(default_ttls={
    'users': 3600,      # 1 hour - rarely changes
    'projects': 1800,   # 30 min
    'logs': 60,         # 1 min - frequently updated
})
```

### Environment Configuration

Override TTLs without code changes:

```bash
CACHE_ENABLED=true          # Enable/disable caching (default: true)
CACHE_TTL_DEFAULT=600       # Default TTL in seconds
CACHE_TTL_USERS=3600        # Override for 'users' key
CACHE_TTL_PROJECTS=1800     # Override for 'projects' key
```

### Monitoring

```python
stats = cache.stats()
# {
#     'enabled': True,
#     'entry_count': 5,
#     'total_hits': 1234,
#     'total_fetches': 45,
#     'hit_rate': 0.96,
#     'entries': {...}
# }
```

### Flask API Endpoints

```python
from flask import Blueprint, jsonify
from jhg_patterns.flask import TTLCache

cache = TTLCache()
api = Blueprint('api', __name__)

@api.route('/cache/stats')
def cache_stats():
    return jsonify(cache.stats())

@api.route('/cache/invalidate', methods=['POST'])
def cache_invalidate():
    data = request.json or {}
    if data.get('all'):
        count = cache.invalidate_all()
        return jsonify({'cleared': count})
    if data.get('key'):
        cache.invalidate(data['key'])
        return jsonify({'cleared': data['key']})
    return jsonify({'error': 'Provide key or all'}), 400
```

### Features

- **Thread-safe**: Uses `threading.RLock()` for concurrent access
- **Stale-on-error**: Returns cached data if fetch fails
- **Force refresh**: Bypass cache when needed
- **Per-key TTLs**: Different expiry times for different data
- **Environment config**: Override at runtime without code changes
- **Monitoring**: Built-in statistics for observability
