"""
Tests for v1.1 streaming functionality.
"""

import pytest
from flatten_anything import flatten, ingest
from pathlib import Path
import json
import csv
import tempfile
from typing import Generator


class TestStreamingBasics:
    """Test basic streaming functionality."""
    
    def test_csv_streaming_returns_generator(self, tmp_path):
        """Test that CSV streaming returns a generator."""
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("name,age\nAlice,30\nBob,25\nCharlie,35")
        
        result = ingest(csv_file, stream=True)
        
        assert isinstance(result, Generator)
        
        # Consume the generator
        chunks = list(result)
        assert len(chunks) > 0
        assert isinstance(chunks[0], list)
        assert isinstance(chunks[0][0], dict)
    
    def test_jsonl_streaming_returns_generator(self, tmp_path):
        """Test that JSONL streaming returns a generator."""
        jsonl_file = tmp_path / "data.jsonl"
        lines = [
            '{"name": "Alice", "age": 30}',
            '{"name": "Bob", "age": 25}',
            '{"name": "Charlie", "age": 35}'
        ]
        jsonl_file.write_text('\n'.join(lines))
        
        result = ingest(jsonl_file, stream=True)
        
        assert isinstance(result, Generator)
        chunks = list(result)
        assert len(chunks) > 0
    
    def test_regular_json_streaming_not_supported(self, tmp_path):
        """Test that regular JSON files raise error when streaming requested."""
        json_file = tmp_path / "data.json"
        json_file.write_text('{"name": "Alice", "age": 30}')
        
        with pytest.raises(NotImplementedError, match="Streaming is only supported for JSONL"):
            ingest(json_file, stream=True)
    
    def test_xml_streaming_not_supported(self, tmp_path):
        """Test that XML files raise error when streaming requested."""
        xml_file = tmp_path / "data.xml"
        xml_file.write_text('<?xml version="1.0"?><root><name>Alice</name></root>')
        
        with pytest.raises(NotImplementedError, match="Streaming is not supported for XML"):
            ingest(xml_file, stream=True)
    
    def test_yaml_streaming_not_supported(self, tmp_path):
        """Test that YAML files raise error when streaming requested."""
        yaml_file = tmp_path / "data.yaml"
        yaml_file.write_text("name: Alice\nage: 30")
        
        with pytest.raises(NotImplementedError, match="Streaming is not supported for YAML"):
            ingest(yaml_file, stream=True)
    
    def test_excel_streaming_not_supported(self, tmp_path):
        """Test that Excel files raise error when streaming requested."""
        # Create a simple CSV and rename to .xlsx for testing
        excel_file = tmp_path / "data.xlsx"
        excel_file.write_bytes(b"dummy excel content")
        
        with pytest.raises(NotImplementedError, match="Streaming is not supported for Excel"):
            ingest(excel_file, stream=True)


class TestStreamingChunkSize:
    """Test chunk size parameter behavior."""
    
    def test_csv_respects_chunk_size(self, tmp_path):
        """Test that CSV streaming respects chunk_size parameter."""
        csv_file = tmp_path / "large.csv"
        
        # Create CSV with 100 rows
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name'])
            for i in range(100):
                writer.writerow([i, f'Person{i}'])
        
        # Stream with chunk_size=10
        chunks = list(ingest(csv_file, stream=True, chunk_size=10))
        
        assert len(chunks) == 10  # 100 rows / 10 per chunk
        for chunk in chunks[:-1]:  # All but last chunk
            assert len(chunk) == 10
        # Last chunk might be smaller
        assert len(chunks[-1]) <= 10
    
    def test_jsonl_respects_chunk_size(self, tmp_path):
        """Test that JSONL streaming respects chunk_size parameter."""
        jsonl_file = tmp_path / "large.jsonl"
        
        # Create JSONL with 50 records
        lines = []
        for i in range(50):
            lines.append(json.dumps({"id": i, "name": f"Person{i}"}))
        jsonl_file.write_text('\n'.join(lines))
        
        # Stream with chunk_size=7
        chunks = list(ingest(jsonl_file, stream=True, chunk_size=7))
        
        assert len(chunks) == 8  # 50/7 = 7 full chunks + 1 partial
        for chunk in chunks[:-1]:
            assert len(chunk) == 7
        assert len(chunks[-1]) == 1  # 50 % 7 = 1
    
    def test_chunk_size_ignored_when_not_streaming(self, tmp_path):
        """Test that chunk_size is ignored in non-streaming mode."""
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("id,name\n1,Alice\n2,Bob\n3,Charlie\n4,David\n5,Eve")
        
        # Non-streaming with chunk_size should return all data
        result = ingest(csv_file, stream=False, chunk_size=2)
        
        assert isinstance(result, list)
        assert len(result) == 5  # All 5 records returned


class TestStreamingWithFlatten:
    """Test streaming integration with flatten function."""
    
    def test_flatten_streamed_csv_chunks(self, tmp_path):
        """Test flattening streamed CSV chunks."""
        csv_file = tmp_path / "nested.csv"
        csv_file.write_text("id,name,data\n1,Alice,'{\"city\": \"NYC\"}'\n2,Bob,'{\"city\": \"LA\"}'")
        
        all_flattened = []
        for chunk in ingest(csv_file, stream=True, chunk_size=1):
            flattened_chunk = flatten(chunk)
            all_flattened.extend(flattened_chunk)
        
        assert len(all_flattened) == 2
        assert all_flattened[0]['id'] == 1
        assert all_flattened[0]['name'] == 'Alice'
    
    def test_flatten_streamed_jsonl_with_nested_data(self, tmp_path):
        """Test flattening streamed JSONL with nested structures."""
        jsonl_file = tmp_path / "nested.jsonl"
        lines = [
            json.dumps({"user": {"name": "Alice", "contact": {"email": "alice@ex.com"}}}),
            json.dumps({"user": {"name": "Bob", "contact": {"email": "bob@ex.com"}}}),
        ]
        jsonl_file.write_text('\n'.join(lines))
        
        all_flattened = []
        for chunk in ingest(jsonl_file, stream=True, chunk_size=1):
            flattened_chunk = flatten(chunk)
            all_flattened.extend(flattened_chunk)
        
        assert len(all_flattened) == 2
        assert all_flattened[0]["user.name"] == "Alice"
        assert all_flattened[0]["user.contact.email"] == "alice@ex.com"
        assert all_flattened[1]["user.name"] == "Bob"


class TestStreamingMemoryBehavior:
    """Test that streaming actually provides memory benefits."""
    
    def test_generator_is_lazy(self, tmp_path):
        """Test that generator doesn't load all data immediately."""
        csv_file = tmp_path / "data.csv"
        
        # Create CSV with multiple rows
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'value'])
            for i in range(20):
                writer.writerow([i, f'value{i}'])
        
        gen = ingest(csv_file, stream=True, chunk_size=5)
        
        # Generator shouldn't execute until we iterate
        first_chunk = next(gen)
        assert len(first_chunk) == 5
        assert first_chunk[0]['id'] == 0
        
        # We can stop iteration at any time
        second_chunk = next(gen)
        assert len(second_chunk) == 5
        assert second_chunk[0]['id'] == 5
        
        # Rest of data hasn't been loaded
        # (we're not consuming the rest of the generator)
    
    def test_streaming_handles_empty_file(self, tmp_path):
        """Test streaming behavior with empty files."""
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("")
        
        result = ingest(empty_csv, stream=True)
        chunks = list(result)
        
        assert chunks == [[]]  # Single empty chunk
    
    def test_streaming_handles_single_record(self, tmp_path):
        """Test streaming with file containing single record."""
        csv_file = tmp_path / "single.csv"
        csv_file.write_text("name\nAlice")
        
        chunks = list(ingest(csv_file, stream=True, chunk_size=10))
        
        assert len(chunks) == 1
        assert len(chunks[0]) == 1
        assert chunks[0][0]['name'] == 'Alice'


class TestStreamingEdgeCases:
    """Test edge cases in streaming functionality."""
    
    def test_jsonl_with_empty_lines(self, tmp_path):
        """Test JSONL streaming handles empty lines correctly."""
        jsonl_file = tmp_path / "with_empty.jsonl"
        content = '{"id": 1}\n\n{"id": 2}\n\n\n{"id": 3}'
        jsonl_file.write_text(content)
        
        chunks = list(ingest(jsonl_file, stream=True, chunk_size=2))
        all_records = []
        for chunk in chunks:
            all_records.extend(chunk)
        
        assert len(all_records) == 3
        assert all_records[0]['id'] == 1
        assert all_records[1]['id'] == 2
        assert all_records[2]['id'] == 3
    
    def test_jsonl_with_primitive_values(self, tmp_path):
        """Test JSONL streaming wraps primitive values."""
        jsonl_file = tmp_path / "primitives.jsonl"
        jsonl_file.write_text('1\n"string"\ntrue\nnull')
        
        chunks = list(ingest(jsonl_file, stream=True, chunk_size=2))
        all_records = []
        for chunk in chunks:
            all_records.extend(chunk)
        
        assert len(all_records) == 4
        assert all_records[0] == {"value": 1}
        assert all_records[1] == {"value": "string"}
        assert all_records[2] == {"value": True}
        assert all_records[3] == {"value": None}
    
    def test_csv_with_chunk_size_larger_than_file(self, tmp_path):
        """Test CSV streaming when chunk_size exceeds file size."""
        csv_file = tmp_path / "small.csv"
        csv_file.write_text("id\n1\n2\n3")
        
        chunks = list(ingest(csv_file, stream=True, chunk_size=100))
        
        assert len(chunks) == 1
        assert len(chunks[0]) == 3
    
    def test_invalid_chunk_size(self, tmp_path):
        """Test behavior with invalid chunk_size values."""
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("id\n1\n2")
        
        # Zero or negative chunk_size should raise error or use default
        # This depends on implementation - adjust based on actual behavior
        with pytest.raises(ValueError):
            list(ingest(csv_file, stream=True, chunk_size=0))
    
    def test_parquet_streaming(self, tmp_path):
        """Test Parquet streaming if pyarrow is available."""
        pytest.importorskip("pyarrow")

        import pandas as pd
        
        # Create a parquet file
        parquet_file = tmp_path / "data.parquet"
        df = pd.DataFrame({
            'id': range(100),
            'name': [f'Person{i}' for i in range(100)]
        })
        df.to_parquet(parquet_file)
        
        chunks = list(ingest(parquet_file, stream=True, chunk_size=25))
        
        assert len(chunks) == 4
        for chunk in chunks:
            assert len(chunk) == 25


class TestStreamingPipeline:
    """Test complete streaming pipeline scenarios."""
    
    def test_large_file_processing_pipeline(self, tmp_path):
        """Test processing large file in streaming fashion."""
        csv_file = tmp_path / "large.csv"
        
        # Create larger CSV
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'score'])
            for i in range(1000):
                writer.writerow([i, f'Person{i}', i % 100])
        
        # Process in chunks, collecting statistics
        total_records = 0
        total_score = 0
        
        for chunk in ingest(csv_file, stream=True, chunk_size=100):
            flattened = flatten(chunk)
            total_records += len(flattened)
            total_score += sum(r['score'] for r in flattened)
        
        assert total_records == 1000
        assert total_score == sum(i % 100 for i in range(1000))
    
    def test_streaming_with_mixed_chunk_sizes(self, tmp_path):
        """Test that last chunk can be smaller than chunk_size."""
        csv_file = tmp_path / "data.csv"
        
        # Create CSV with 23 rows (not divisible by chunk_size)
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id'])
            for i in range(23):
                writer.writerow([i])
        
        chunks = list(ingest(csv_file, stream=True, chunk_size=5))
        
        assert len(chunks) == 5  # 4 full chunks + 1 partial
        assert len(chunks[0]) == 5
        assert len(chunks[1]) == 5
        assert len(chunks[2]) == 5
        assert len(chunks[3]) == 5
        assert len(chunks[4]) == 3  # Last chunk has remainder
