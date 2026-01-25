"""Tests for jhg-patterns-databricks Unity Catalog utilities."""

import os
import pytest
from jhg_patterns.databricks import get_catalog_schema, get_table_path
from jhg_patterns.databricks.unity import parse_table_path


class TestGetCatalogSchema:
    """Tests for get_catalog_schema function."""

    def test_returns_defaults_when_no_env(self, monkeypatch):
        """Should return defaults when env vars not set."""
        monkeypatch.delenv('DATABRICKS_CATALOG', raising=False)
        monkeypatch.delenv('DATABRICKS_SCHEMA', raising=False)

        catalog, schema = get_catalog_schema()

        assert catalog == 'main'
        assert schema == 'default'

    def test_uses_env_vars(self, monkeypatch):
        """Should use environment variables when set."""
        monkeypatch.setenv('DATABRICKS_CATALOG', 'ai_a')
        monkeypatch.setenv('DATABRICKS_SCHEMA', 'rei')

        catalog, schema = get_catalog_schema()

        assert catalog == 'ai_a'
        assert schema == 'rei'

    def test_custom_defaults(self, monkeypatch):
        """Should use custom defaults."""
        monkeypatch.delenv('DATABRICKS_CATALOG', raising=False)
        monkeypatch.delenv('DATABRICKS_SCHEMA', raising=False)

        catalog, schema = get_catalog_schema(
            default_catalog='my_catalog',
            default_schema='my_schema'
        )

        assert catalog == 'my_catalog'
        assert schema == 'my_schema'


class TestGetTablePath:
    """Tests for get_table_path function."""

    def test_builds_path_from_defaults(self, monkeypatch):
        """Should build path from default catalog/schema."""
        monkeypatch.delenv('DATABRICKS_CATALOG', raising=False)
        monkeypatch.delenv('DATABRICKS_SCHEMA', raising=False)

        path = get_table_path('users')

        assert path == 'main.default.users'

    def test_builds_path_from_env(self, monkeypatch):
        """Should build path from env vars."""
        monkeypatch.setenv('DATABRICKS_CATALOG', 'ai_a')
        monkeypatch.setenv('DATABRICKS_SCHEMA', 'rei')

        path = get_table_path('pi_projects')

        assert path == 'ai_a.rei.pi_projects'

    def test_explicit_overrides(self, monkeypatch):
        """Should use explicit catalog/schema when provided."""
        monkeypatch.setenv('DATABRICKS_CATALOG', 'ignored')
        monkeypatch.setenv('DATABRICKS_SCHEMA', 'ignored')

        path = get_table_path('users', catalog='explicit', schema='test')

        assert path == 'explicit.test.users'


class TestParseTablePath:
    """Tests for parse_table_path function."""

    def test_parses_valid_path(self):
        """Should parse valid three-part path."""
        catalog, schema, table = parse_table_path('ai_a.rei.pi_projects')

        assert catalog == 'ai_a'
        assert schema == 'rei'
        assert table == 'pi_projects'

    def test_raises_on_invalid_path(self):
        """Should raise ValueError on invalid paths."""
        with pytest.raises(ValueError):
            parse_table_path('just_table')

        with pytest.raises(ValueError):
            parse_table_path('schema.table')

        with pytest.raises(ValueError):
            parse_table_path('too.many.parts.here')
