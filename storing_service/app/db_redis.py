# StoringService - Redis Connection and Operations
# Manages Redis connection and caching operations
#
# Redis Keys:
# - "latest_cv" : stores cv_id (hash) of most recently uploaded CV
#
# Operations:
# - set_latest_cv(cv_id) -> sets latest_cv key
# - get_latest_cv() -> returns cv_id or None
#
# Purpose:
# - Fast retrieval of latest CV without MongoDB query
# - Simple single-key caching strategy
#
# Responsibilities:
# - Redis client initialization
# - Get/Set operations for latest_cv key
# - Handle connection failures gracefully

