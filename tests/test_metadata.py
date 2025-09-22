"""Unit tests for add-metadata.py functions."""
import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Add the parent directory to sys.path to import add-metadata
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import functions from add-metadata.py
import importlib.util
spec = importlib.util.spec_from_file_location("add_metadata", Path(__file__).parent.parent / "add-metadata.py")
add_metadata = importlib.util.module_from_spec(spec)
spec.loader.exec_module(add_metadata)

# Import the functions we need
load_configuration = add_metadata.load_configuration
process_metadata_extraction = add_metadata.process_metadata_extraction
load_pivot_mapping = add_metadata.load_pivot_mapping
parse_metadata_from_content = add_metadata.parse_metadata_from_content
merge_external_data = add_metadata.merge_external_data


class TestConfiguration:
    """Test configuration loading functionality."""
    
    def test_load_configuration_defaults(self, monkeypatch):
        """Test loading configuration with default values."""
        # Set minimal required environment
        monkeypatch.setenv("METADATA_FILE", "test.csv")
        monkeypatch.setenv("METADATA_OUTPUT_FILE", "output.csv")
        monkeypatch.setenv("METADATA_FIELDS", "title,author")
        monkeypatch.setenv("DEBUG", "False")
        
        config = load_configuration()
        
        assert config['input_path'] == "test.csv"
        assert config['output_path'] == "output.csv"
        assert config['metadata_fields'] == ["title", "author"]
        assert config['has_pivot_field'] == False
        assert config['debug'] == False
        
    def test_load_configuration_with_pivots(self, monkeypatch):
        """Test configuration when zone_pivot_groups is included."""
        monkeypatch.setenv("INPUT_PATH", "test.csv")
        monkeypatch.setenv("OUTPUT_PATH", "output.csv")
        monkeypatch.setenv("METADATA_FIELDS", "title,zone_pivot_groups,author")
        
        config = load_configuration()
        
        assert config['has_pivot_field'] == True
        assert "zone_pivot_groups" in config['metadata_fields']
        
    def test_load_configuration_missing_required(self, monkeypatch):
        """Test that missing required environment variables raise SystemExit."""
        monkeypatch.delenv("INPUT_PATH", raising=False)
        monkeypatch.delenv("OUTPUT_PATH", raising=False)
        monkeypatch.delenv("METADATA_FILE", raising=False)
        monkeypatch.delenv("METADATA_OUTPUT_FILE", raising=False)
        
        with pytest.raises(SystemExit):
            load_configuration()


class TestPivotMapping:
    """Test pivot mapping functionality."""
    
    def test_load_pivot_mapping_success(self):
        """Test loading valid pivot mapping file."""
        fixture_path = Path(__file__).parent.parent / "test" / "fixtures" / "pivot-mapping.yml"
        
        pivot_mapping = load_pivot_mapping(str(fixture_path))
        
        assert pivot_mapping is not None
        assert "test-group" in pivot_mapping
        assert pivot_mapping["test-group"] == ["option-a", "option-b", "option-c"]
        
    def test_load_pivot_mapping_missing_file(self):
        """Test handling of missing pivot mapping file."""
        pivot_mapping = load_pivot_mapping("nonexistent-file.yml")
        
        assert pivot_mapping is None


class TestMetadataExtraction:
    """Test metadata extraction from markdown files."""
    
    def test_parse_metadata_from_content_valid(self):
        """Test parsing valid YAML frontmatter."""
        content = """---
title: Test Title
author: Test Author
description: Test description
---

# Content here
"""
        metadata = parse_metadata_from_content(content)
        
        assert metadata["title"] == "Test Title"
        assert metadata["author"] == "Test Author"
        assert metadata["description"] == "Test description"
        
    def test_parse_metadata_from_content_no_frontmatter(self):
        """Test handling content without frontmatter."""
        content = """# Just a heading

Some content without frontmatter.
"""
        metadata = parse_metadata_from_content(content)
        
        assert metadata == {}
        
    def test_parse_metadata_from_content_invalid_yaml(self):
        """Test handling invalid YAML frontmatter."""
        content = """---
title: Test Title
invalid: yaml: content: here
---

Content
"""
        metadata = parse_metadata_from_content(content)
        
        # Should return empty dict for invalid YAML
        assert metadata == {}


class TestProcessMetadataExtraction:
    """Test the main metadata processing function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.fixtures_dir = Path(__file__).parent.parent / "test" / "fixtures"
        
    def test_process_metadata_extraction_basic(self):
        """Test basic metadata extraction workflow."""
        # Create test dataframe
        test_data = {
            'filename': ['fixtures/sample-article.md'],
            'relative_path': ['sample-article.md'],
            'title': [''],
            'author': [''],
            'description': [''],
            'file_found': [False]
        }
        df = pd.DataFrame(test_data)
        
        # Mock config
        config = {
            'DEBUG': False,
            'base_path': str(self.fixtures_dir.parent),
            'metadata_fields': ['title', 'author', 'description'],
            'has_pivot_field': False,
            'metadata_flags': {},
            'debug': False
        }
        
        processed_files, found_files = process_metadata_extraction(df, config, {})
        
        # Check results
        assert processed_files == 1
        assert found_files == 1
        assert df.loc[0, 'title'] == 'Test Article'
        assert df.loc[0, 'author'] == 'testuser' 
        assert df.loc[0, 'file_found'] == True
        
    def test_process_metadata_extraction_missing_file(self):
        """Test handling of missing files."""
        test_data = {
            'Href': ['nonexistent-file.md'],
            'relative_path': ['nonexistent-file.md'],
            'title': [''],
            'file_found': [False]
        }
        df = pd.DataFrame(test_data)
        
        config = {
            'DEBUG': False,
            'base_path': str(self.fixtures_dir.parent),
            'metadata_fields': ['title'],
            'has_pivot_field': False,
            'metadata_flags': {},
            'debug': False
        }
        
        processed_files, found_files = process_metadata_extraction(df, config, {})
        
        assert processed_files == 0  # File not found, so not processed
        assert found_files == 0
        assert df.loc[0, 'file_found'] == False
        assert df.loc[0, 'title'] == ''  # Should remain empty
        
    def test_process_metadata_extraction_with_pivots(self):
        """Test metadata extraction with pivot groups."""
        test_data = {
            'filename': ['fixtures/sample-article.md'],
            'relative_path': ['sample-article.md'],
            'title': [''],
            'zone_pivot_groups': [''],
            'pivot_id': [''],
            'has_pivots': [False],
            'pivot_groups': [''],
            'file_found': [False]
        }
        df = pd.DataFrame(test_data)
        
        config = {
            'DEBUG': False,
            'base_path': str(self.fixtures_dir.parent),
            'metadata_fields': ['title', 'zone_pivot_groups'],
            'has_pivot_field': True,
            'metadata_flags': {},
            'debug': False
        }
        
        # Load pivot mapping
        pivot_mapping_path = self.fixtures_dir / 'pivot-mapping.yml'
        pivot_mapping = load_pivot_mapping(str(pivot_mapping_path))
        
        processed_files, found_files = process_metadata_extraction(df, config, pivot_mapping)
        
        # Check pivot processing
        assert df.loc[0, 'zone_pivot_groups'] == 'test-group'
        assert df.loc[0, 'has_pivots'] == True
        assert df.loc[0, 'pivot_groups'] == 'option-a,option-b,option-c'


class TestExternalDataMerging:
    """Test external data merging functionality."""
    
    def test_merge_external_data_no_file(self):
        """Test merge when no external file is specified."""
        config = {'DEBUG': False}
        
        result_df = merge_external_data(pd.DataFrame(), config)
        
        assert result_df.empty
        
    def test_merge_external_data_missing_file(self):
        """Test merge when external file doesn't exist.""" 
        config = {'foundry_file': 'nonexistent.csv', 'DEBUG': False}
        
        result_df = merge_external_data(pd.DataFrame(), config)
        
        assert result_df.empty


# Integration test fixture
@pytest.fixture
def sample_csv_data():
    """Create sample CSV data for integration testing."""
    fixtures_dir = Path(__file__).parent.parent / "test" / "fixtures"
    return str(fixtures_dir / "test-sample.csv")


class TestIntegration:
    """Integration tests for the full workflow."""
    
    def test_end_to_end_processing(self, sample_csv_data, monkeypatch):
        """Test the complete metadata processing workflow."""
        # Set up environment
        monkeypatch.setenv("METADATA_FILE", sample_csv_data)
        monkeypatch.setenv("METADATA_OUTPUT_FILE", "test-output.csv") 
        monkeypatch.setenv("METADATA_FIELDS", "title,author,description")
        monkeypatch.setenv("DEBUG", "True")
        
        # Load configuration
        config = load_configuration()
        
        # Read input CSV
        df = pd.read_csv(config['input_path'])
        
        # Rename file_path to filename for consistency with pipeline
        if 'file_path' in df.columns:
            df = df.rename(columns={'file_path': 'filename'})
        
        # Add metadata columns
        for field in config['metadata_fields']:
            df[field] = ""
        df['file_found'] = False
        
        # Process metadata
        processed_files, found_files = process_metadata_extraction(df, config, {})
        
        # Verify results
        assert processed_files == 2  # 2 files actually exist and were processed
        assert found_files == 2      # 2 files actually exist
        
        # Check specific results
        sample_row = df[df['relative_path'] == 'sample-article.md'].iloc[0]
        assert sample_row['title'] == 'Test Article'
        assert sample_row['author'] == 'testuser'
        assert sample_row['file_found'] == True
        
        no_meta_row = df[df['relative_path'] == 'no-metadata-article.md'].iloc[0]
        assert no_meta_row['title'] == 'No Metadata Article'
        assert no_meta_row['file_found'] == True
        
        missing_row = df[df['relative_path'] == 'missing-file.md'].iloc[0]
        assert missing_row['file_found'] == False


if __name__ == "__main__":
    pytest.main([__file__])