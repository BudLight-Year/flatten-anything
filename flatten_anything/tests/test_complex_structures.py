"""
Complex test cases for Flatten Anything package.
These test edge cases and complex nested structures.

AI Generated tests
"""

import pytest
import json
import tempfile
from pathlib import Path
from flatten_anything import flatten, ingest


class TestComplexFlatten:
    """Test complex and edge case scenarios for flatten."""

    def test_deeply_nested_structure(self):
        """Test very deep nesting (10+ levels)."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "level5": {
                                "level6": {
                                    "level7": {
                                        "level8": {"level9": {"level10": "deep_value"}}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        result = flatten(data)
        assert (
            result[
                "level1.level2.level3.level4.level5.level6.level7.level8.level9.level10"
            ]
            == "deep_value"
        )

    def test_mixed_empty_and_full_structures(self):
        """Test mix of empty and populated structures."""
        data = {
            "users": [
                {"name": "Alice", "tags": []},
                {"name": "Bob", "tags": ["admin", "user"]},
                {},  # Empty dict in list
                {"name": "Charlie", "tags": [], "meta": {}},
            ],
            "settings": {},
            "features": [],
        }
        result = flatten(data)

        assert result["users.0.name"] == "Alice"
        assert result["users.0.tags"] == []
        assert result["users.1.name"] == "Bob"
        assert result["users.1.tags.0"] == "admin"
        assert result["users.1.tags.1"] == "user"
        # users.2 is empty dict, should not appear
        assert "users.2" not in result
        assert result["users.3.name"] == "Charlie"
        assert result["users.3.tags"] == []
        # users.3.meta is empty dict, should not appear
        assert "users.3.meta" not in result
        assert result["features"] == []

    def test_special_characters_in_keys(self):
        """Test keys with dots, spaces, and special characters."""
        data = {
            "user.name": "John",  # Dot in key
            "user name": "Jane",  # Space in key
            "user@email": "john@example.com",  # @ in key
            "user/id": 123,  # Slash in key
            "user\\path": "C:\\Users",  # Backslash in key
            "user:role": "admin",  # Colon in key
            "user?query": "test",  # Question mark in key
            "user#hash": "abc123",  # Hash in key
        }
        result = flatten(data)

        # All special characters should be preserved
        assert result["user.name"] == "John"
        assert result["user name"] == "Jane"
        assert result["user@email"] == "john@example.com"
        assert result["user/id"] == 123
        assert result["user\\path"] == "C:\\Users"
        assert result["user:role"] == "admin"
        assert result["user?query"] == "test"
        assert result["user#hash"] == "abc123"

    def test_non_string_dict_keys(self):
        """Test dictionaries with non-string keys."""
        data = {
            2: "two",
            2.5: "two point five",
            True: "boolean true",
            None: "none value",
            "normal": "string key",
        }
        result = flatten(data)

        # Non-string keys should be converted to strings
        assert result["2"] == "two"
        assert result["2.5"] == "two point five"
        assert result["True"] == "boolean true"
        assert result["None"] == "none value"
        assert result["normal"] == "string key"

    def test_unicode_and_emoji_keys(self):
        """Test Unicode characters and emojis in keys and values."""
        data = {
            "用户": {"名字": "张三"},  # Chinese characters
            "użytkownik": {"imię": "Józef"},  # Polish characters
            "🔑": {"🏠": "🎉"},  # Emojis
            "café": {"naïve": "résumé"},  # Accented characters
        }
        result = flatten(data)

        assert result["用户.名字"] == "张三"
        assert result["użytkownik.imię"] == "Józef"
        assert result["🔑.🏠"] == "🎉"
        assert result["café.naïve"] == "résumé"

    def test_circular_reference_like_structure(self):
        """Test structure that looks like it could be circular (but isn't)."""
        data = {
            "node": {
                "value": 1,
                "child": {
                    "value": 2,
                    "parent_id": "node",  # Reference-like but just a string
                    "child": {"value": 3, "parent_id": "node.child"},
                },
            }
        }
        result = flatten(data)

        assert result["node.value"] == 1
        assert result["node.child.value"] == 2
        assert result["node.child.parent_id"] == "node"
        assert result["node.child.child.value"] == 3
        assert result["node.child.child.parent_id"] == "node.child"

    def test_large_list_structure(self):
        """Test handling of large lists (1000+ items)."""
        data = {"items": list(range(1000))}
        result = flatten(data)

        assert len(result) == 1000
        assert result["items.0"] == 0
        assert result["items.500"] == 500
        assert result["items.999"] == 999

    def test_mixed_type_values(self):
        """Test various Python types as values."""
        data = {
            "types": {
                "integer": 42,
                "float": 3.14159,
                "string": "hello",
                "boolean_true": True,
                "boolean_false": False,
                "none": None,
                "list": [1, 2, 3],
                "empty_list": [],
                "nested": {"inner": "value"},
            }
        }
        result = flatten(data)

        assert result["types.integer"] == 42
        assert result["types.float"] == 3.14159
        assert result["types.string"] == "hello"
        assert result["types.boolean_true"] is True
        assert result["types.boolean_false"] is False
        assert result["types.none"] is None
        assert result["types.list.0"] == 1
        assert result["types.list.1"] == 2
        assert result["types.list.2"] == 3
        assert result["types.empty_list"] == []
        assert result["types.nested.inner"] == "value"

    def test_alternating_list_dict_nesting(self):
        """Test alternating between lists and dicts in deep nesting."""
        data = [
            {
                "items": [
                    {"subitems": [{"value": 1}, {"value": 2}]},
                    {"subitems": [{"value": 3}]},
                ]
            },
            {"items": []},
        ]
        result = flatten(data)

        assert result["0.items.0.subitems.0.value"] == 1
        assert result["0.items.0.subitems.1.value"] == 2
        assert result["0.items.1.subitems.0.value"] == 3
        assert result["1.items"] == []

    def test_whitespace_in_keys(self):
        """Test various types of whitespace in keys."""
        data = {
            "  leading": "spaces",
            "trailing  ": "spaces",
            "  both  ": "spaces",
            "tab\there": "tab",
            "new\nline": "newline",
            "multiple   spaces": "between",
        }
        result = flatten(data)

        # Whitespace should be preserved as-is
        assert result["  leading"] == "spaces"
        assert result["trailing  "] == "spaces"
        assert result["  both  "] == "spaces"
        assert result["tab\there"] == "tab"
        assert result["new\nline"] == "newline"
        assert result["multiple   spaces"] == "between"

    def test_empty_string_keys(self):
        """Test handling of empty string as keys."""
        data = {"": "empty key", "normal": {"": "nested empty key"}}
        result = flatten(data)

        assert result[""] == "empty key"
        assert result["normal"] == "nested empty key"

    def test_very_long_keys(self):
        """Test handling of extremely long key names."""
        long_key = "a" * 1000  # 1000 character key
        data = {long_key: {"nested": "value"}}
        result = flatten(data)

        expected_key = f"{long_key}.nested"
        assert result[expected_key] == "value"
        assert len(expected_key) == 1007  # 1000 + '.nested'


class TestComplexIntegration:
    """Test complex scenarios with ingest and flatten together."""

    def test_malformed_json_recovery(self, tmp_path):
        """Test handling of slightly malformed but recoverable JSON."""
        # JSONL with empty lines and comments (common in real files)
        test_file = tmp_path / "messy.jsonl"
        test_file.write_text(
            """
{"id": 1, "name": "Alice"}

{"id": 2, "name": "Bob"}
        
{"id": 3, "name": "Charlie"}
"""
        )

        data = ingest(test_file)
        assert len(data) == 3

        flattened = [flatten(record) for record in data]
        assert flattened[0]["id"] == 1
        assert flattened[2]["name"] == "Charlie"

    def test_csv_with_nested_json_column(self, tmp_path):
        """Test CSV where one column contains JSON strings."""
        test_file = tmp_path / "mixed.csv"
        test_file.write_text(
            '''id,name,metadata
1,Alice,"{""tags"": [""admin"", ""user""], ""active"": true}"
2,Bob,"{""tags"": [], ""active"": false}"'''
        )

        data = ingest(test_file)
        # Note: The JSON is still a string after CSV ingestion
        assert len(data) == 2

        # In real usage, you'd need to parse the JSON column separately
        flattened = [flatten(record) for record in data]
        assert flattened[0]["id"] == 1
        assert flattened[0]["name"] == "Alice"
        # metadata is still a JSON string, not parsed
        assert isinstance(flattened[0]["metadata"], str)

    def test_yaml_with_anchors_and_references(self, tmp_path):
        """Test YAML with anchors and references (YAML-specific feature)."""
        test_file = tmp_path / "anchors.yaml"
        test_file.write_text(
            """
defaults: &defaults
  timeout: 30
  retries: 3

development:
  <<: *defaults
  host: localhost
  
production:
  <<: *defaults
  host: prod.example.com
  timeout: 60
"""
        )

        data = ingest(test_file)
        flattened = flatten(data[0])

        # YAML references should be resolved
        assert flattened["development.timeout"] == 30
        assert flattened["development.retries"] == 3
        assert flattened["development.host"] == "localhost"
        assert flattened["production.timeout"] == 60  # Overridden
        assert flattened["production.retries"] == 3

    def test_xml_with_attributes(self, tmp_path):
        """Test XML with attributes (which xmltodict handles specially)."""
        test_file = tmp_path / "attributes.xml"
        test_file.write_text(
            """<?xml version="1.0"?>
<root>
    <user id="1" active="true">
        <name>Alice</name>
        <email>alice@example.com</email>
    </user>
    <user id="2" active="false">
        <name>Bob</name>
    </user>
</root>"""
        )

        data = ingest(test_file)
        flattened = flatten(data[0])

        # xmltodict puts attributes in @key
        assert "@id" in str(flattened)  # Attributes are preserved
        # The exact structure depends on xmltodict's behavior
