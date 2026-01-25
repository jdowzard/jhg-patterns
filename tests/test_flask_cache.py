"""Tests for jhg-patterns-flask TTLCache."""

import time
import pytest
from jhg_patterns.flask import TTLCache


class TestTTLCache:
    """Tests for TTLCache class."""

    def test_cache_stores_and_retrieves(self):
        """Cache should store and return data."""
        cache = TTLCache()
        data = [{'id': 1, 'name': 'Test'}]

        result = cache.get('test', fetch_fn=lambda: data)

        assert result == data

    def test_cache_hit_returns_cached_data(self):
        """Second call should return cached data without calling fetch_fn."""
        cache = TTLCache()
        call_count = 0

        def fetch():
            nonlocal call_count
            call_count += 1
            return [{'id': call_count}]

        result1 = cache.get('test', fetch_fn=fetch)
        result2 = cache.get('test', fetch_fn=fetch)

        assert call_count == 1
        assert result1 == result2

    def test_cache_expires_after_ttl(self):
        """Cache should expire and refetch after TTL."""
        cache = TTLCache()
        call_count = 0

        def fetch():
            nonlocal call_count
            call_count += 1
            return [{'id': call_count}]

        cache.get('test', fetch_fn=fetch, ttl=1)
        assert call_count == 1

        time.sleep(1.1)

        cache.get('test', fetch_fn=fetch, ttl=1)
        assert call_count == 2

    def test_invalidate_clears_entry(self):
        """Invalidate should remove cache entry."""
        cache = TTLCache()
        cache.get('test', fetch_fn=lambda: [1, 2, 3])

        result = cache.invalidate('test')

        assert result is True
        assert cache.get_entry_info('test') is None

    def test_invalidate_nonexistent_returns_false(self):
        """Invalidate on missing key should return False."""
        cache = TTLCache()

        result = cache.invalidate('nonexistent')

        assert result is False

    def test_invalidate_all_clears_cache(self):
        """Invalidate all should clear all entries."""
        cache = TTLCache()
        cache.get('a', fetch_fn=lambda: [1])
        cache.get('b', fetch_fn=lambda: [2])
        cache.get('c', fetch_fn=lambda: [3])

        count = cache.invalidate_all()

        assert count == 3
        assert cache.stats()['entry_count'] == 0

    def test_force_refresh_bypasses_cache(self):
        """Force refresh should bypass cache and fetch fresh."""
        cache = TTLCache()
        call_count = 0

        def fetch():
            nonlocal call_count
            call_count += 1
            return [{'id': call_count}]

        cache.get('test', fetch_fn=fetch)
        cache.get('test', fetch_fn=fetch, force_refresh=True)

        assert call_count == 2

    def test_stats_returns_correct_info(self):
        """Stats should return cache statistics."""
        cache = TTLCache()
        cache.get('test', fetch_fn=lambda: [1, 2, 3])
        cache.get('test', fetch_fn=lambda: [])  # Cache hit

        stats = cache.stats()

        assert stats['enabled'] is True
        assert stats['entry_count'] == 1
        assert stats['total_fetches'] == 1
        assert stats['total_hits'] == 1
        assert 'test' in stats['entries']

    def test_get_entry_info(self):
        """get_entry_info should return entry details."""
        cache = TTLCache()
        cache.get('test', fetch_fn=lambda: [1], ttl=300)

        info = cache.get_entry_info('test')

        assert info is not None
        assert info['ttl'] == 300
        assert info['ttl_remaining'] > 0
        assert info['is_expired'] is False

    def test_disabled_cache_always_fetches(self):
        """When disabled, cache should always call fetch_fn."""
        cache = TTLCache()
        cache._enabled = False
        call_count = 0

        def fetch():
            nonlocal call_count
            call_count += 1
            return [call_count]

        cache.get('test', fetch_fn=fetch)
        cache.get('test', fetch_fn=fetch)

        assert call_count == 2

    def test_returns_stale_on_fetch_error(self):
        """On fetch error, should return stale data if available."""
        cache = TTLCache()
        call_count = 0

        def fetch():
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise Exception("Fetch failed")
            return [1, 2, 3]

        result1 = cache.get('test', fetch_fn=fetch, ttl=0)
        result2 = cache.get('test', fetch_fn=fetch, ttl=0)

        assert result1 == result2 == [1, 2, 3]

    def test_custom_default_ttls(self):
        """Custom default TTLs should be used."""
        cache = TTLCache(default_ttls={'custom': 999})
        cache.get('custom', fetch_fn=lambda: [1])

        info = cache.get_entry_info('custom')
        assert info['ttl'] == 999
