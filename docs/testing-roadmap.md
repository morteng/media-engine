# Test Development Roadmap

## High-Priority Modules Needing Tests

### 1. video/captions.py (419 LOC, 0% → 95%)

**Module Purpose**: WebVTT caption generation from video scripts

**Functions to test**:
```python
format_timestamp(seconds: float) -> str:
    # Test inputs: 0, 1.5, 61, 3661, 3661.123
    # Test format: HH:MM:SS.mmm
```

**Classes to test**:
```python
class CaptionEntry:
    start_time: float
    end_time: float
    text: str
    style: str = "default"
    # Test creation, validation, serialization
```

**Public API functions** (read full file to find all):
- Functions that appear after line 50

---

### 2. video/capture.py (705 LOC, 0% → 95%)

**Module Purpose**: Video scene capture and rendering

**Key areas to test**:
- Scene initialization and configuration
- Frame capture logic
- Video file output handling
- Error handling for missing dependencies
- Performance with large videos

---

### 3. cms/document.py (320 LOC, 41% → 80%)

**Missing lines (need tests)**:
- Lines 36, 67, 71-79: Constructor, initializers
- Lines 83-91, 95, 99-101: Metadata accessors
- Lines 105-127: Status/state methods
- Lines 154-183: Translation handling
- Lines 188-202: Advanced accessors

**Test template**:
```python
def test_document_from_markdown_with_frontmatter():
    content = "---\ntitle: Hello\nlanguage: en\n---\nBody"
    doc = Document.from_markdown(content)
    assert doc.title == "Hello"
    assert doc.body == "Body"
    assert doc.language == "en"

def test_document_missing_required_fields():
    content = "---\n---\nBody"  # no title
    with pytest.raises(ValueError):
        Document.from_markdown(content)

def test_document_translation_status():
    doc = Document(..., language="no", source_document="en/intro.md")
    assert doc.is_translation
    assert doc.source_document == "en/intro.md"
```

---

### 4. cms/schema.py (219 LOC, 27% → 80%)

**Missing lines**:
- Lines 57-70, 74-104: Schema loading
- Lines 110-161: Field validation
- Lines 165-194: Type validation
- Lines 207-230: Nested structure validation

**Test template**:
```python
def test_schema_load_from_yaml():
    schema = Schema.load(Path("schema.yaml"))
    assert schema is not None
    assert "title" in schema.fields

def test_schema_requires_title():
    schema = Schema.load(...)
    errors = schema.validate({})  # no title
    assert len(errors) > 0
    assert any("title" in e for e in errors)

def test_schema_validates_field_types():
    schema = Schema.load(...)
    data = {"title": 123}  # should be string
    errors = schema.validate(data)
    assert any("type" in e for e in errors)

def test_schema_validates_nested_objects():
    schema = Schema.load(...)  # with nested fields
    data = {"metadata": {"author": "John"}}
    assert schema.validate(data) == []  # valid

def test_schema_required_vs_optional():
    schema = Schema.load(...)
    required_fields = schema.get_required_fields()
    assert "title" in required_fields
    assert "tags" not in required_fields  # optional
```

---

### 5. cms/index.py (208 LOC, 22% → 80%)

**Missing lines**:
- Lines 133-142, 150-157: Indexing operations
- Lines 161-205: Search functionality
- Lines 209-235: Index updates
- Lines 240-293: Complex queries

**Test template**:
```python
def test_index_add_document():
    index = DocumentIndex()
    doc = Document(title="Test", body="Content here")
    index.add_document(doc)
    assert doc.id in index

def test_index_search_by_title():
    index = DocumentIndex()
    index.add_document(Document(title="Hello World", body="..."))
    results = index.search("Hello")
    assert len(results) > 0
    assert results[0].title == "Hello World"

def test_index_search_by_content():
    index = DocumentIndex()
    index.add_document(Document(title="Test", body="specific keyword here"))
    results = index.search("keyword")
    assert len(results) > 0

def test_index_update_document():
    index = DocumentIndex()
    doc = Document(title="Old Title", id="doc1")
    index.add_document(doc)
    doc.title = "New Title"
    index.update_document(doc)
    results = index.search("New")
    assert len(results) > 0

def test_index_remove_document():
    index = DocumentIndex()
    doc = Document(id="doc1", title="Test")
    index.add_document(doc)
    index.remove_document("doc1")
    assert "doc1" not in index
```

---

### 6. cms/references.py (194 LOC, 18% → 80%)

**Missing lines**:
- Lines 45-48, 52-58: Reference parsing
- Lines 62-117, 121-193: Reference resolution
- Lines 198-265: Cross-document linking

**Test template**:
```python
def test_extract_references_from_document():
    doc = Document(body="See [other document](./other.md)")
    refs = extract_references(doc)
    assert len(refs) > 0
    assert refs[0].target == "./other.md"

def test_resolve_reference():
    doc1 = Document(id="doc1", title="Intro")
    doc2 = Document(id="doc2", body="See [intro](./doc1.md)")
    ref = Reference(source=doc2, target="./doc1.md")
    resolved = ref.resolve([doc1, doc2])
    assert resolved == doc1

def test_broken_reference_detection():
    doc = Document(body="See [missing](./missing.md)")
    refs = extract_references(doc)
    assert refs[0].is_broken  # target doesn't exist

def test_circular_reference_detection():
    # doc1 references doc2
    # doc2 references doc1
    # Should detect cycle
    pass
```

---

### 7. cms/graph.py (156 LOC, 26% → 80%)

**Missing lines**:
- Lines 56-93: Graph building
- Lines 97-131: Relationship mapping
- Lines 143-163: Impact analysis

**Test template**:
```python
def test_build_dependency_graph():
    doc1 = Document(id="doc1", title="Intro")
    doc2 = Document(id="doc2", body="See intro")
    graph = DependencyGraph([doc1, doc2])
    assert graph.get_dependencies(doc2) == [doc1]

def test_detect_cycles_in_graph():
    # Create circular dependency
    doc1 = Document(id="doc1", body="See doc2")
    doc2 = Document(id="doc2", body="See doc1")
    graph = DependencyGraph([doc1, doc2])
    cycles = graph.find_cycles()
    assert len(cycles) > 0

def test_impact_analysis():
    # If doc1 changes, what else is affected?
    doc1 = Document(id="doc1")
    doc2 = Document(id="doc2", body="See doc1")
    doc3 = Document(id="doc3", body="See doc2")
    graph = DependencyGraph([doc1, doc2, doc3])
    impacted = graph.get_impact(doc1)
    assert doc2 in impacted
    assert doc3 in impacted  # transitive

def test_topological_sort():
    # Ensure documents are processed in dependency order
    graph = DependencyGraph([...])
    sorted_docs = graph.topological_sort()
    # Dependencies should come before dependents
    pass
```

---

### 8. freshness/scanner.py (128 LOC, 9% → 80%)

**Missing lines**:
- Lines 25-42: Scanner initialization
- Lines 47-72: Document staleness detection
- Lines 77-148: Complex scanning logic
- Lines 153-189, 194-242: Batch operations

**Test template**:
```python
def test_scanner_identifies_recent_documents():
    # Document updated today
    doc = Document(last_updated=datetime.now())
    scanner = FreshnessScanner()
    assert not scanner.is_stale(doc, days=30)

def test_scanner_identifies_stale_documents():
    # Document not updated in 60 days
    old_date = datetime.now() - timedelta(days=60)
    doc = Document(last_updated=old_date)
    scanner = FreshnessScanner()
    assert scanner.is_stale(doc, days=30)

def test_scanner_respects_staleness_threshold():
    doc = Document(last_updated=datetime.now() - timedelta(days=29))
    scanner = FreshnessScanner()
    assert not scanner.is_stale(doc, days=30)
    assert scanner.is_stale(doc, days=28)

def test_scan_multiple_documents():
    docs = [
        Document(id="doc1", last_updated=datetime.now()),
        Document(id="doc2", last_updated=datetime.now() - timedelta(days=60)),
    ]
    scanner = FreshnessScanner()
    results = scanner.scan(docs, days=30)
    assert results["recent"] == 1
    assert results["stale"] == 1

def test_scanner_handles_missing_timestamps():
    # Document with no last_updated
    doc = Document(last_updated=None)
    scanner = FreshnessScanner()
    # Should handle gracefully
    result = scanner.is_stale(doc)
    assert result is False or result is True  # should not crash
```

---

### 9. publish/packager.py (259 LOC, 13% → 80%)

**Missing lines**:
- Lines 86-390: Package building
- Lines 409-482: File bundling
- Lines 501-590: Distribution logic

**Test template**:
```python
def test_packager_creates_archive():
    packager = Packager(project)
    package = packager.create_package()
    assert package.exists()
    assert package.suffix in [".zip", ".tar.gz"]

def test_packager_includes_all_documents():
    packager = Packager(project_with_5_docs)
    package = packager.create_package()
    # Extract and verify
    assert_archive_contains_files(package, count=5)

def test_packager_excludes_drafts():
    docs = [
        Document(id="published", status="published"),
        Document(id="draft", status="draft"),
    ]
    packager = Packager(project_with_docs(docs))
    package = packager.create_package()
    assert_archive_contains("published", package)
    assert_not_contains("draft", package)

def test_packager_handles_large_projects():
    # Test with 100+ documents
    packager = Packager(large_project)
    package = packager.create_package()
    assert package.stat().st_size > 0  # Not empty

def test_packager_compression():
    packager = Packager(project, compression="gzip")
    package = packager.create_package()
    assert package.suffix == ".tar.gz"
    assert is_valid_gzip(package)
```

---

### 10. freshness/registry.py (269 LOC, 14% → 80%)

**Missing lines**:
- Lines 63-77, 81-94: Registry initialization
- Lines 98-133, 137-169: Update tracking
- Lines 181-212, 216-316: Persistence

**Test template**:
```python
def test_registry_records_update():
    registry = FreshnessRegistry(project)
    doc = Document(id="doc1", title="Test")
    registry.record_update(doc)
    assert registry.get_last_updated("doc1") is not None

def test_registry_tracks_timestamps():
    registry = FreshnessRegistry(project)
    before = datetime.now()
    registry.record_update(Document(id="doc1"))
    after = datetime.now()
    timestamp = registry.get_last_updated("doc1")
    assert before <= timestamp <= after

def test_registry_persists_to_file():
    registry = FreshnessRegistry(project)
    registry.record_update(Document(id="doc1"))
    registry.save()
    
    registry2 = FreshnessRegistry(project)
    registry2.load()
    assert registry2.get_last_updated("doc1") is not None

def test_registry_bulk_update():
    registry = FreshnessRegistry(project)
    docs = [Document(id=f"doc{i}") for i in range(10)]
    registry.record_updates(docs)
    assert len(registry.get_all_updates()) == 10

def test_registry_concurrent_updates():
    # Multiple processes updating same registry
    registry = FreshnessRegistry(project)
    # Should handle concurrent writes
    pass
```

---

## Testing Priority Chart

```
EFFORT vs IMPACT
═══════════════════════════════════════════════════════════════

Quick Wins (Do First):
  mcp/tools/audit.py         ⚡ 15 min → +1% coverage
  mcp/tools/cache.py         ⚡ 15 min → +1% coverage
  video/captions.py          ⚡ 45 min → +2% coverage
  freshness/scanner.py       ⚡ 60 min → +2% coverage

Medium Effort (Do Second):
  cms/schema.py              ⏱ 90 min → +5% coverage
  cms/index.py               ⏱ 90 min → +4% coverage
  cms/document.py            ⏱ 120 min → +6% coverage
  video/voiceover.py         ⏱ 120 min → +5% coverage

Larger Projects (Do Third):
  freshness/registry.py      📦 150 min → +7% coverage
  publish/packager.py        📦 150 min → +8% coverage
  video/timeline.py          📦 120 min → +5% coverage
  video/capture.py           📦 180 min → +8% coverage

Final Push (Do Last):
  integrity/__init__.py      🎯 120 min → +3% coverage
  demos/__init__.py          🎯 120 min → +4% coverage
  cms/graph.py               🎯 90 min → +4% coverage
  cms/references.py          🎯 90 min → +5% coverage
```

---

## Running Tests During Development

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest python/tests/test_cms.py -v

# Run with coverage for one module
uv run pytest python/tests/ --cov=media_engine.cms --cov-report=term-missing

# Run with output on failures
uv run pytest -vv

# Stop on first failure
uv run pytest -x

# Run specific test
uv run pytest python/tests/test_cms.py::test_document_parsing -v

# Generate HTML coverage report
uv run pytest --cov=media_engine --cov-report=html
# Then open htmlcov/index.html
```

---

## Test File Templates

### Minimal Test File Template

```python
import pytest
from pathlib import Path
from media_engine.cms import Document
from media_engine.cms.schema import Schema

class TestDocumentParsing:
    """Tests for Document parsing and initialization."""
    
    def test_document_from_markdown_basic(self):
        """Test basic markdown parsing with frontmatter."""
        content = "---\ntitle: Test\nlanguage: en\n---\nBody"
        doc = Document.from_markdown(content)
        assert doc.title == "Test"
        assert doc.body == "Body"
    
    def test_document_missing_title_raises_error(self):
        """Test that documents without title raise ValueError."""
        content = "---\n---\nBody"
        with pytest.raises(ValueError):
            Document.from_markdown(content)
    
    def test_document_with_tags(self):
        """Test document with tags in frontmatter."""
        content = "---\ntitle: Test\ntags: [a, b, c]\n---\nBody"
        doc = Document.from_markdown(content)
        assert doc.title == "Test"
        assert "a" in doc.tags

class TestSchemaValidation:
    """Tests for schema validation."""
    
    def test_schema_loads_from_file(self, temp_dir):
        """Test loading schema from YAML file."""
        schema_file = temp_dir / "schema.yaml"
        schema_file.write_text("""
fields:
  title:
    type: string
    required: true
""")
        schema = Schema.load(schema_file)
        assert "title" in schema.fields
    
    def test_schema_validates_required_fields(self):
        """Test that schema enforces required fields."""
        schema = Schema.load(...)
        doc = {}  # missing required title
        errors = schema.validate(doc)
        assert len(errors) > 0
```

---

## Coverage Maintenance Strategy

1. **Before committing code**: Run `pytest --cov=media_engine` and check coverage
2. **Set minimum**: Configure `--cov-fail-under=80` in pyproject.toml
3. **Regular review**: Run coverage report weekly during development
4. **Quick checks**: Use `--cov-report=term-missing` to see which lines need tests

---

## Expected Timeline

| Phase | Hours | Target Coverage | Focus |
|-------|-------|-----------------|-------|
| Phase 1 | 2-3 | 43% → 50% | Quick wins, CMS basics |
| Phase 2 | 3-4 | 50% → 60% | Video, publish, demos |
| Phase 3 | 3-4 | 60% → 70% | Freshness, status, integrity |
| Phase 4 | 2-3 | 70% → 80%+ | Final gaps, edge cases |
| **Total** | **11-15** | **43% → 80%+** | Complete |

---
