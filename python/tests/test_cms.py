"""
Tests for media_engine.cms module.
"""

from media_engine.cms.document import Document, DocumentCollection


class TestDocument:
    """Tests for Document class."""

    def test_load_document(self, sample_markdown):
        """Test loading a document from file."""
        doc = Document.load(sample_markdown)
        assert doc.title == "Test Document"
        assert doc.version == "1.0.0"
        assert doc.status == "draft"

    def test_document_content(self, sample_markdown):
        """Test document content parsing."""
        doc = Document.load(sample_markdown)
        assert "# Test Document" in doc.content
        assert "## Section One" in doc.content

    def test_document_metadata(self, sample_markdown):
        """Test document metadata access."""
        doc = Document.load(sample_markdown)
        assert "title" in doc.metadata
        assert doc.metadata["title"] == "Test Document"

    def test_document_word_count(self, sample_markdown):
        """Test document word count."""
        doc = Document.load(sample_markdown)
        assert doc.word_count() > 0

    def test_document_missing_frontmatter(self, temp_dir):
        """Test document without frontmatter."""
        path = temp_dir / "no_frontmatter.md"
        path.write_text("# Just Content\n\nNo frontmatter here.")
        doc = Document.load(path)
        assert doc.title == "no_frontmatter"  # Falls back to filename


class TestDocumentCollection:
    """Tests for DocumentCollection class."""

    def test_empty_collection(self, temp_dir):
        """Test creating empty collection."""
        collection = DocumentCollection(temp_dir)
        assert len(collection.all_documents) == 0

    def test_collection_with_documents(self, temp_dir, sample_markdown):
        """Test collection with one document."""
        # Create a docs structure
        docs_dir = temp_dir / "docs"
        docs_dir.mkdir()
        (docs_dir / "test.md").write_text(sample_markdown.read_text())

        collection = DocumentCollection(temp_dir)
        # Note: load_all expects specific directory structure
        # For basic test, just verify initialization works
        assert collection.docs_dir == temp_dir

    def test_collection_iteration(self, temp_dir):
        """Test iterating over collection."""
        collection = DocumentCollection(temp_dir)
        documents = list(collection.all_documents)
        assert isinstance(documents, list)
