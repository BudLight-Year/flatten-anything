"""
Tests for v1.1 flatten functionality with records parameter and List[Dict] guarantees.
"""

import pytest
from flatten_anything import flatten, ingest
from pathlib import Path
import json
import tempfile


class TestFlattenRecordsParameter:
    """Test the new records parameter functionality."""
    
    def test_records_true_with_list_of_dicts(self):
        """Test records=True flattens each dict separately."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        result = flatten(data, records=True)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == {"name": "Alice", "age": 30}
        assert result[1] == {"name": "Bob", "age": 25}
    
    def test_records_false_with_list_of_dicts(self):
        """Test records=False flattens entire structure."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        result = flatten(data, records=False)
        
        assert isinstance(result, dict)
        assert result["0.name"] == "Alice"
        assert result["0.age"] == 30
        assert result["1.name"] == "Bob"
        assert result["1.age"] == 25
    
    def test_records_default_is_true(self):
        """Test that records=True is the default behavior."""
        data = [{"a": 1}, {"b": 2}]
        result_default = flatten(data)
        result_explicit = flatten(data, records=True)
        
        assert result_default == result_explicit
        assert isinstance(result_default, list)
    
    def test_nested_records_flattening(self):
        """Test that nested structures within records are flattened."""
        data = [
            {"user": {"name": "Alice", "details": {"age": 30}}},
            {"user": {"name": "Bob", "details": {"age": 25}}}
        ]
        result = flatten(data)
        
        assert len(result) == 2
        assert result[0]["user.name"] == "Alice"
        assert result[0]["user.details.age"] == 30
        assert result[1]["user.name"] == "Bob"
        assert result[1]["user.details.age"] == 25
    
    def test_single_dict_not_affected_by_records(self):
        """Test that single dict works the same regardless of records parameter."""
        data = {"user": {"name": "Alice", "age": 30}}
        
        result_true = flatten(data, records=True)
        result_false = flatten(data, records=False)
        
        expected = {"user.name": "Alice", "user.age": 30}
        assert result_true == expected
        assert result_false == expected
    
    def test_empty_list_with_records(self):
        """Test empty list handling with records parameter."""
        assert flatten([], records=True) == []
        assert flatten([], records=False) == {}
    
    def test_list_with_mixed_empty_dicts(self):
        """Test list containing empty and non-empty dicts."""
        data = [
            {"name": "Alice"},
            {},
            {"name": "Bob"}
        ]
        result = flatten(data)
        
        assert len(result) == 3
        assert result[0] == {"name": "Alice"}
        assert result[1] == {}
        assert result[2] == {"name": "Bob"}


class TestIngestAlwaysReturnsList:
    """Test that all ingest functions return List[Dict[str, Any]]."""
    
    def test_json_primitive_wrapping(self, tmp_path):
        """Test JSON with primitive values gets wrapped."""
        # Primitive value
        json_file = tmp_path / "primitive.json"
        json_file.write_text('"hello world"')
        
        data = ingest(json_file)
        assert data == [{"value": "hello world"}]
        
        # List of primitives
        json_file2 = tmp_path / "list.json"
        json_file2.write_text('[1, 2, 3, 4, 5]')
        
        data2 = ingest(json_file2)
        assert data2 == [
            {"value": 1},
            {"value": 2},
            {"value": 3},
            {"value": 4},
            {"value": 5}
        ]
    
    def test_yaml_primitive_wrapping(self, tmp_path):
        """Test YAML with primitive values gets wrapped."""
        # List of primitives
        yaml_file = tmp_path / "list.yaml"
        yaml_file.write_text("- apple\n- banana\n- cherry")
        
        data = ingest(yaml_file)
        assert data == [
            {"value": "apple"},
            {"value": "banana"},
            {"value": "cherry"}
        ]
        
        # Single primitive
        yaml_file2 = tmp_path / "string.yaml"
        yaml_file2.write_text("just a string")
        
        data2 = ingest(yaml_file2)
        assert data2 == [{"value": "just a string"}]
    
    def test_jsonl_primitive_wrapping(self, tmp_path):
        """Test JSONL with primitive values per line gets wrapped."""
        jsonl_file = tmp_path / "primitives.jsonl"
        jsonl_file.write_text('1\n"hello"\ntrue\nnull')
        
        data = ingest(jsonl_file)
        assert data == [
            {"value": 1},
            {"value": "hello"},
            {"value": True},
            {"value": None}
        ]
    
    def test_json_dict_wrapped_in_list(self, tmp_path):
        """Test single JSON object gets wrapped in list."""
        json_file = tmp_path / "object.json"
        json_file.write_text('{"name": "Alice", "age": 30}')
        
        data = ingest(json_file)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data == [{"name": "Alice", "age": 30}]
    
    def test_all_formats_return_list(self, tmp_path):
        """Test that all formats consistently return lists."""
        # CSV
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("name,age\nAlice,30")
        csv_data = ingest(csv_file)
        assert isinstance(csv_data, list)
        
        # JSON object
        json_file = tmp_path / "data.json"
        json_file.write_text('{"test": true}')
        json_data = ingest(json_file)
        assert isinstance(json_data, list)
        
        # YAML
        yaml_file = tmp_path / "data.yaml"
        yaml_file.write_text("test: true")
        yaml_data = ingest(yaml_file)
        assert isinstance(yaml_data, list)
        
        # XML
        xml_file = tmp_path / "data.xml"
        xml_file.write_text('<?xml version="1.0"?><root><test>true</test></root>')
        xml_data = ingest(xml_file)
        assert isinstance(xml_data, list)


class TestIntegrationIngestAndFlatten:
    """Test ingest and flatten working together with new behavior."""
    
    def test_csv_ingestion_and_flattening(self, tmp_path):
        """Test CSV -> ingest -> flatten pipeline."""
        csv_file = tmp_path / "users.csv"
        csv_file.write_text("name,age,city\nAlice,30,NYC\nBob,25,LA")
        
        data = ingest(csv_file)
        flat = flatten(data)
        
        assert isinstance(flat, list)
        assert len(flat) == 2
        assert flat[0] == {"name": "Alice", "age": 30, "city": "NYC"}
        assert flat[1] == {"name": "Bob", "age": 25, "city": "LA"}
    
    def test_nested_json_array_flattening(self, tmp_path):
        """Test JSON array of nested objects."""
        json_file = tmp_path / "nested.json"
        json_data = [
            {"user": {"name": "Alice", "contact": {"email": "alice@example.com"}}},
            {"user": {"name": "Bob", "contact": {"email": "bob@example.com"}}}
        ]
        json_file.write_text(json.dumps(json_data))
        
        data = ingest(json_file)
        flat = flatten(data)
        
        assert len(flat) == 2
        assert flat[0]["user.name"] == "Alice"
        assert flat[0]["user.contact.email"] == "alice@example.com"
        assert flat[1]["user.name"] == "Bob"
        assert flat[1]["user.contact.email"] == "bob@example.com"
    
    def test_single_nested_structure(self, tmp_path):
        """Test single nested structure gets flattened correctly."""
        json_file = tmp_path / "single.json"
        json_data = {
            "company": {
                "name": "TechCorp",
                "address": {
                    "street": "123 Main St",
                    "city": "SF"
                }
            }
        }
        json_file.write_text(json.dumps(json_data))
        
        data = ingest(json_file)  # Returns [json_data]
        flat = flatten(data)  # Should detect single dict in list
        
        assert len(flat) == 1
        assert flat[0]["company.name"] == "TechCorp"
        assert flat[0]["company.address.street"] == "123 Main St"
        assert flat[0]["company.address.city"] == "SF"
    
    def test_primitive_list_handling(self, tmp_path):
        """Test that primitive lists get wrapped and handled correctly."""
        json_file = tmp_path / "numbers.json"
        json_file.write_text("[1, 2, 3, 4, 5]")
        
        data = ingest(json_file)
        flat = flatten(data)
        
        assert len(flat) == 5
        assert flat[0] == {"value": 1}
        assert flat[1] == {"value": 2}
        assert flat[4] == {"value": 5}
    
    def test_mixed_structure_preservation(self, tmp_path):
        """Test that mixed structures are handled correctly."""
        yaml_file = tmp_path / "mixed.yaml"
        yaml_content = """
- name: Alice
  scores: [95, 87, 92]
- name: Bob
  scores: [88, 91]
"""
        yaml_file.write_text(yaml_content)
        
        data = ingest(yaml_file)
        flat = flatten(data)
        
        assert len(flat) == 2
        assert flat[0]["name"] == "Alice"
        assert flat[0]["scores.0"] == 95
        assert flat[0]["scores.1"] == 87
        assert flat[0]["scores.2"] == 92
        assert flat[1]["name"] == "Bob"
        assert flat[1]["scores.0"] == 88
        assert flat[1]["scores.1"] == 91


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_deeply_nested_with_records(self):
        """Test deeply nested structure with records=True."""
        data = [
            {
                "level1": {
                    "level2": {
                        "level3": {
                            "value": "deep"
                        }
                    }
                }
            }
        ]
        result = flatten(data)
        
        assert len(result) == 1
        assert result[0]["level1.level2.level3.value"] == "deep"
    
    def test_none_values_preserved(self):
        """Test that None values are preserved correctly."""
        data = [
            {"name": "Alice", "age": None},
            {"name": None, "age": 25}
        ]
        result = flatten(data)
        
        assert result[0]["name"] == "Alice"
        assert result[0]["age"] is None
        assert result[1]["name"] is None
        assert result[1]["age"] == 25
    
    def test_empty_string_keys(self):
        """Test handling of empty string as keys."""
        data = [
            {"": "empty key", "normal": "value"},
            {"nested": {"": "nested empty"}}
        ]
        result = flatten(data)
        
        assert result[0][""] == "empty key"
        assert result[0]["normal"] == "value"
        assert result[1]["nested"] == "nested empty"
    
    def test_preserve_empty_lists_with_records(self):
        """Test preserve_empty_lists works with records parameter."""
        data = [
            {"items": [], "count": 0},
            {"items": [1, 2], "count": 2}
        ]
        
        result_preserve = flatten(data, preserve_empty_lists=True)
        assert result_preserve[0]["items"] == []
        assert result_preserve[0]["count"] == 0
        
        result_remove = flatten(data, preserve_empty_lists=False)
        assert "items" not in result_remove[0]
        assert result_remove[0]["count"] == 0
