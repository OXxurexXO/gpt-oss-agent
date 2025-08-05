#!/usr/bin/env python3
"""
Tests for File Agent functionality
"""

import pytest
import tempfile
import os
from pathlib import Path
from file_agent import (
    list_files, read_file, write_file, create_directory,
    delete_file, move_file, search_file_content
)

class TestFileOperations:
    """Test basic file operations"""
    
    def setup_method(self):
        """Setup for each test"""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
    def teardown_method(self):
        """Cleanup after each test"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_create_directory(self):
        """Test directory creation"""
        new_dir = self.test_path / "new_directory"
        result = create_directory(str(new_dir))
        
        assert "created successfully" in result
        assert new_dir.exists()
        assert new_dir.is_dir()
    
    def test_write_and_read_file(self):
        """Test file writing and reading"""
        test_file = self.test_path / "test.txt"
        test_content = "Hello, World!"
        
        # Write file
        write_result = write_file(str(test_file), test_content)
        assert "written successfully" in write_result
        assert test_file.exists()
        
        # Read file
        read_result = read_file(str(test_file))
        assert read_result == test_content
    
    def test_list_files(self):
        """Test file listing"""
        # Create some test files
        (self.test_path / "file1.txt").write_text("content1")
        (self.test_path / "file2.txt").write_text("content2")
        
        result = list_files(str(self.test_path))
        assert isinstance(result, list)
        assert "file1.txt" in result
        assert "file2.txt" in result
    
    def test_search_file_content(self):
        """Test content searching"""
        test_file = self.test_path / "search_test.txt"
        content = "Line 1\nThis is a test line\nLine 3\nAnother test\nLine 5"
        test_file.write_text(content)
        
        result = search_file_content(str(test_file), "test")
        assert "This is a test line" in result
        assert "Another test" in result
        assert "Line 1" not in result
    
    def test_move_file(self):
        """Test file moving"""
        source = self.test_path / "source.txt"
        dest = self.test_path / "destination.txt"
        
        source.write_text("test content")
        
        result = move_file(str(source), str(dest))
        assert "successfully" in result
        assert not source.exists()
        assert dest.exists()
        assert dest.read_text() == "test content"
    
    def test_delete_file(self):
        """Test file deletion"""
        test_file = self.test_path / "delete_me.txt"
        test_file.write_text("content")
        
        assert test_file.exists()
        
        result = delete_file(str(test_file))
        assert "deleted successfully" in result
        assert not test_file.exists()

class TestErrorHandling:
    """Test error handling in file operations"""
    
    def test_read_nonexistent_file(self):
        """Test reading non-existent file"""
        result = read_file("/nonexistent/file.txt")
        assert "Error:" in result
    
    def test_write_to_invalid_path(self):
        """Test writing to invalid path"""
        result = write_file("/invalid/path/file.txt", "content")
        assert "Error:" in result
    
    def test_list_nonexistent_directory(self):
        """Test listing non-existent directory"""
        result = list_files("/nonexistent/directory")
        assert "Error:" in result

if __name__ == "__main__":
    pytest.main([__file__])
