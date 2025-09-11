"""
Basic test suite for Flatten Anything package.
"""

import pytest
import json
import tempfile
import requests
from pathlib import Path
from flatten_anything import flatten, ingest


class TestFlatten:
    """Test the flatten function."""

    def test_flatten_simple_dict(self):
        """Test flattening a simple dictionary."""
        data = {"a": 1, "b": 2}
        result = flatten(data)
        assert result == {"a": 1, "b": 2}

    def test_flatten_nested_dict(self):
        """Test flattening nested dictionaries."""
        data = {"user": {"name": "Alice", "age": 30}}
        result = flatten(data)
        assert result == {"user.name": "Alice", "user.age": 30}

    def test_flatten_list(self):
        """Test flattening lists."""
        data = {"items": [1, 2, 3]}
        result = flatten(data)
        assert result == {"items.0": 1, "items.1": 2, "items.2": 3}

    def test_flatten_mixed_nesting(self):
        """Test complex nested structures."""
        data = {
            "users": [
                {"name": "Alice", "scores": [100, 95]},
                {"name": "Bob", "scores": [88]},
            ]
        }
        result = flatten(data)
        assert result == {
            "users.0.name": "Alice",
            "users.0.scores.0": 100,
            "users.0.scores.1": 95,
            "users.1.name": "Bob",
            "users.1.scores.0": 88,
        }

    def test_flatten_empty_structures(self):
        """Test handling of empty structures."""
        assert flatten({}) == {}
        assert flatten([]) == {}
        assert flatten({"empty": []}) == {"empty": []}
        assert flatten({"empty": {}}) == {}
        assert flatten({"has_empty": {"list": [], "dict": {}}}) == {
            "has_empty.list": []
        }

    def test_flatten_primitive_at_root_raises_error(self):
        """Test that primitives at root level raise TypeError."""
        with pytest.raises(TypeError, match="Cannot flatten"):
            flatten(42)

        with pytest.raises(TypeError, match="Cannot flatten"):
            flatten("hello")

        with pytest.raises(TypeError, match="Cannot flatten"):
            flatten(None)

        with pytest.raises(TypeError, match="Cannot flatten"):
            flatten(True)

        assert flatten({"value": 42}) == {"value": 42}
        assert flatten({"text": "hello"}) == {"text": "hello"}

    def test_flatten_special_characters_in_keys(self):
        """Test keys with special characters."""
        data = {"user.name": "Alice", "user@email": "alice@example.com"}
        result = flatten(data)
        # Keys are preserved as-is
        assert "user.name" in result
        assert "user@email" in result


class TestIngest:
    """Test the ingest function."""

    def test_ingest_json(self, tmp_path):
        """Test JSON file ingestion."""
        # Create test JSON file
        test_file = tmp_path / "test.json"
        test_data = {"name": "Alice", "age": 30}
        test_file.write_text(json.dumps(test_data))

        # Test ingestion
        result = ingest(test_file)
        assert result == [test_data]

    def test_ingest_jsonl(self, tmp_path):
        """Test JSONL file ingestion."""
        # Create test JSONL file
        test_file = tmp_path / "test.jsonl"
        lines = [
            json.dumps({"id": 1, "name": "Alice"}),
            json.dumps({"id": 2, "name": "Bob"}),
        ]
        test_file.write_text("\n".join(lines))

        # Test ingestion
        result = ingest(test_file)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"

    def test_ingest_csv(self, tmp_path):
        """Test CSV file ingestion."""
        # Create test CSV file
        test_file = tmp_path / "test.csv"
        test_file.write_text("name,age\nAlice,30\nBob,25")

        # Test ingestion
        result = ingest(test_file)
        assert len(result) == 2
        assert result[0] == {"name": "Alice", "age": 30}
        assert result[1] == {"name": "Bob", "age": 25}

    def test_ingest_yaml(self, tmp_path):
        """Test YAML file ingestion."""
        # Create test YAML file
        test_file = tmp_path / "test.yaml"
        test_file.write_text("name: Alice\nage: 30\nscores:\n  - 100\n  - 95")

        # Test ingestion
        result = ingest(test_file)
        assert result == [{"name": "Alice", "age": 30, "scores": [100, 95]}]

    def test_ingest_xml(self, tmp_path):
        """Test XML file ingestion."""
        # Create test XML file
        test_file = tmp_path / "test.xml"
        test_file.write_text(
            '<?xml version="1.0"?><root><name>Alice</name><age>30</age></root>'
        )

        # Test ingestion
        result = ingest(test_file)
        assert len(result) == 1
        assert "root" in result[0]

    def test_ingest_empty_file(self, tmp_path):
        """Test handling of empty files."""
        test_file = tmp_path / "empty.json"
        test_file.write_text("")

        result = ingest(test_file)
        assert result == []

    def test_ingest_nonexistent_file(self):
        """Test error handling for nonexistent files."""
        with pytest.raises(FileNotFoundError):
            ingest("nonexistent.json")

    def test_ingest_invalid_json(self, tmp_path):
        """Test error handling for invalid JSON."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{invalid json}")

        with pytest.raises(ValueError, match="Invalid JSON"):
            ingest(test_file)

    def test_auto_format_detection(self, tmp_path):
        """Test automatic format detection."""
        # JSON
        json_file = tmp_path / "data.json"
        json_file.write_text('{"test": true}')
        assert ingest(json_file) == [{"test": True}]

        # CSV
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("col1,col2\n1,2")
        result = ingest(csv_file)
        assert len(result) == 1

    def test_format_override(self, tmp_path):
        """Test manual format specification."""
        # File with wrong extension
        test_file = tmp_path / "data.txt"
        test_file.write_text('{"name": "Alice"}')

        # Should work with format override
        result = ingest(test_file, format="json")
        assert result == [{"name": "Alice"}]

    # Missing File Format Tests
    def test_ingest_parquet_not_installed(self, tmp_path, monkeypatch):
        """Test parquet without pyarrow installed."""

        def mock_check(package, feature):
            raise ImportError(f"{feature} support requires {package}")

        monkeypatch.setattr(
            "flatten_anything.utils.check_optional_dependency", mock_check
        )

        test_file = tmp_path / "test.parquet"
        test_file.write_text("dummy")

        with pytest.raises(ImportError, match="parquet"):
            ingest(test_file)

    def test_ingest_api_failure(self, monkeypatch):
        """Test API request failure."""

        def mock_get(*args, **kwargs):
            raise requests.RequestException("Network error")

        monkeypatch.setattr("requests.get", mock_get)

        with pytest.raises(ValueError, match="API request failed"):
            ingest("http://example.com/api")


class TestIntegration:
    """Test flatten and ingest working together."""

    def test_ingest_and_flatten(self, tmp_path):
        """Test the full pipeline."""
        # Create nested JSON
        test_file = tmp_path / "nested.json"
        nested_data = {
            "user": {
                "name": "Alice",
                "contacts": {"email": "alice@example.com", "phone": "555-1234"},
            }
        }
        test_file.write_text(json.dumps(nested_data))

        # Ingest and flatten
        data = ingest(test_file)
        flattened = flatten(data[0])

        assert flattened == {
            "user.name": "Alice",
            "user.contacts.email": "alice@example.com",
            "user.contacts.phone": "555-1234",
        }

    def test_multiple_records(self, tmp_path):
        """Test handling multiple records."""
        test_file = tmp_path / "users.jsonl"
        lines = [
            json.dumps({"user": {"name": "Alice", "age": 30}}),
            json.dumps({"user": {"name": "Bob", "age": 25}}),
        ]
        test_file.write_text("\n".join(lines))

        data = ingest(test_file)
        flattened_records = [flatten(record) for record in data]

        assert len(flattened_records) == 2
        assert flattened_records[0]["user.name"] == "Alice"
        assert flattened_records[1]["user.name"] == "Bob"
