# Media Engine Test Coverage Analysis

**Report Date**: 2025-12-19
**Overall Coverage**: 43% (9,109 / 15,901 lines)
**Test Results**: 554 passed, 10 skipped
**Target Coverage**: 80%

---

## Executive Summary

The media-engine project has moderate test coverage at **43%** overall, but with significant variance across modules. The good news: **core modules are well-tested** (config: 100%, theme: 98%, translation: 90%, links: 92%). The challenge: **several critical modules have near-zero coverage**, particularly in the video and freshness tracking pipelines.

To reach **80% overall coverage**, we need to focus on:

1. **Untested modules** (0% coverage) - 11 modules
2. **Critically low modules** (<20% coverage) - 23 modules
3. **High-impact modules** (large, <80% coverage) - Priority targets

---

## Tier 1: Critical Gaps (0% Coverage)

These modules have NO tests and are preventing overall coverage growth.

### High-Impact Untested Modules

| Module | LOC | Priority | Why It Matters |
|--------|-----|----------|-----------------|
| `video/captions.py` | 419 | CRITICAL | 0% - WebVTT caption generation for videos |
| `video/capture.py` | 705 | CRITICAL | 0% - Video scene capture pipeline |
| `publish/packager.py` | 727 | CRITICAL | 0% - Deliverable packaging/distribution |
| `demos/__init__.py` | 795 | HIGH | 0% - Interactive demo generation |
| `integrity/__init__.py` | 427 | HIGH | 0% - Asset integrity verification |
| `gui/__init__.py` | 128 | MEDIUM | 0% - GUI launcher |
| `cli/commands/*.py` | 20+ files | LOW | All 0% - CLI commands (lower priority) |
| `mcp/helpers.py` | 38 | MEDIUM | 0% - MCP helper utilities |
| `mcp/resources.py` | 30 | MEDIUM | 0% - MCP resource definitions |
| `web/routes.py` | 5 | TRIVIAL | 0% - Web routing entry point |

### Action Items for Tier 1

1. **Start with video/captions.py** (419 LOC):
   - Test `format_timestamp()` with various input times
   - Test WebVTT format generation
   - Test caption entry creation and validation
   - Expected gain: 2-3% coverage

2. **Then video/capture.py** (705 LOC, largest):
   - Test scene capture initialization
   - Test capture state management
   - Test video output handling
   - Expected gain: 3-4% coverage

3. **Then publish/packager.py** (727 LOC, highly used):
   - Test package generation
   - Test deliverable creation workflows
   - Test file bundling and distribution
   - Expected gain: 3-4% coverage

---

## Tier 2: Severely Undercovered (<20% Coverage)

These modules are tested but need substantial expansion.

### Modules with Lowest Coverage (% vs LOC)

| Module | Coverage | LOC | Gap | Priority |
|--------|----------|-----|-----|----------|
| `freshness/scanner.py` | 9% | 128 | 116 lines | CRITICAL |
| `status/views.py` | 8% | 169 | 155 lines | CRITICAL |
| `web/routes/search.py` | 10% | 70 | 63 lines | HIGH |
| `publish/packager.py` | 13% | 259 | 225 lines | HIGH |
| `freshness/registry.py` | 14% | 269 | 230 lines | HIGH |
| `web/routes/dependencies.py` | 16% | 63 | 53 lines | HIGH |
| `web/routes/insights.py` | 17% | 173 | 144 lines | HIGH |
| `mcp/tools/session.py` | 16% | 64 | 54 lines | MEDIUM |
| `mcp/tools/audit.py` | 18% | 17 | 14 lines | MEDIUM |
| `video/voiceover.py` | 18% | 173 | 142 lines | MEDIUM |
| `cms/references.py` | 18% | 194 | 160 lines | HIGH |

### Quick Wins (Small, High Impact)

These are small modules where adding tests yields quick coverage gains:

1. **mcp/tools/audit.py** (17 LOC, 18% coverage):
   - Test 3-4 simple functions
   - Expected coverage gain: 10-15%

2. **mcp/tools/cache.py** (17 LOC, 12% coverage):
   - Test cache operations
   - Expected coverage gain: 10-15%

3. **mcp/tools/quality.py** (17 LOC, 12% coverage):
   - Test quality check wrappers
   - Expected coverage gain: 10-15%

---

## Tier 3: Moderate Gaps (20-70% Coverage)

These modules are partially tested. Target the largest ones first.

### High-Impact, Partially-Tested Modules

| Module | Coverage | LOC | Untested Lines | Priority |
|--------|----------|-----|-----------------|----------|
| `cms/index.py` | 22% | 208 | 162 lines | HIGH |
| `cms/graph.py` | 26% | 156 | 116 lines | HIGH |
| `cms/quality.py` | 22% | 193 | 150 lines | HIGH |
| `cms/schema.py` | 27% | 219 | 160 lines | HIGH |
| `cms/provenance.py` | 30% | 159 | 112 lines | HIGH |
| `video/timeline.py` | 45% | 216 | 119 lines | MEDIUM |
| `video/builder.py` | 41% | 239 | 141 lines | MEDIUM |
| `video/voiceover.py` | 18% | 173 | 142 lines | HIGH |
| `video/scene_capture.py` | 23% | 126 | 97 lines | MEDIUM |
| `cms/document.py` | 41% | 320 | 189 lines | MEDIUM |

### CMS Module Strategy (Very Important)

The CMS module has 4 core files totaling 736 LOC with only 26% coverage. These are foundational to the system:

1. **cms/schema.py** (219 LOC, 27% coverage):
   - Test schema validation logic
   - Test required/optional field handling
   - Test nested schema definitions
   - Test error messages

2. **cms/index.py** (208 LOC, 22% coverage):
   - Test document indexing
   - Test search functionality
   - Test index updates

3. **cms/references.py** (194 LOC, 18% coverage):
   - Test cross-document reference resolution
   - Test broken reference detection
   - Test reference updating

4. **cms/graph.py** (156 LOC, 26% coverage):
   - Test dependency graph building
   - Test cycle detection
   - Test impact analysis

---

## Tier 4: Well-Tested Modules (>70% Coverage)

These don't need as much attention but have room for improvement:

| Module | Coverage | Notes |
|--------|----------|-------|
| `core/config.py` | 100% | Complete |
| `core/theme.py` | 98% | Almost complete (1 line missing) |
| `cms/translation.py` | 90% | Strong coverage |
| `links/__init__.py` | 92% | Strong coverage |
| `readability/__init__.py` | 100% | Complete |
| `security/__init__.py` | 96% | Almost complete |
| `gaps/__init__.py` | 98% | Almost complete |
| `diagrams/generator.py` | 97% | Almost complete |

---

## Prioritized Implementation Plan

### Phase 1: Quick Wins (2-3 hours)

Focus on untested small modules and existing tests that need minimal expansion:

1. **Create test_video_captions.py** (new)
   - Cover all functions in `video/captions.py` (419 LOC, 0%)
   - Expected: +2-3% overall coverage
   - Effort: 30-45 min

2. **Create test_freshness.py** (new)
   - Test freshness tracking and scanning
   - Cover `freshness/scanner.py` (128 LOC, 9%) and `freshness/registry.py` (269 LOC, 14%)
   - Expected: +1-2% overall coverage
   - Effort: 45-60 min

3. **Expand test_cms.py** (existing)
   - Currently minimal (8 tests)
   - Add coverage for schema, references, graph, provenance
   - Target: Get cms/* from 26% avg to 60%
   - Expected: +3-5% overall coverage
   - Effort: 1.5-2 hours

4. **Create test_publish.py** (new)
   - Cover `publish/packager.py` (727 LOC, 13%)
   - Focus on main export/packaging workflows
   - Expected: +1-2% overall coverage
   - Effort: 45-60 min

### Phase 2: Medium Effort (3-4 hours)

1. **Expand test_video.py** (existing)
   - Currently 82% done (coverage: 81%)
   - Add tests for `video/builder.py` (41%), `video/timeline.py` (45%), `video/voiceover.py` (18%)
   - Expected: +3-4% overall coverage
   - Effort: 1.5-2 hours

2. **Create test_demos.py** (new)
   - Cover `demos/__init__.py` (795 LOC, 0%)
   - Focus on demo generation and configuration
   - Expected: +2-3% overall coverage
   - Effort: 1-1.5 hours

3. **Expand MCP tools tests** (existing test_mcp_tools.py)
   - Currently 49% coverage
   - Add tests for low-coverage tools: audit, cache, quality, session, translation, documents, project
   - Expected: +1-2% overall coverage
   - Effort: 1-1.5 hours

### Phase 3: Larger Effort (4-5 hours)

1. **Expand test_web_routes.py** (existing)
   - Several web route modules have <50% coverage
   - Focus on: insights (17%), dependencies (16%), search (10%), freshness (15%)
   - Expected: +2-3% overall coverage
   - Effort: 1.5-2 hours

2. **Create test_integrity.py** (new)
   - Cover `integrity/__init__.py` (427 LOC, 0%)
   - Test asset verification and terminology tracking
   - Expected: +1-2% overall coverage
   - Effort: 1-1.5 hours

3. **Create test_status.py** (new)
   - Cover `status/dashboard.py` (205 LOC, 36%) and `status/views.py` (169 LOC, 8%)
   - Test dashboard rendering and status views
   - Expected: +1-2% overall coverage
   - Effort: 1-1.5 hours

---

## Implementation Priority Sequence

To maximize impact with minimal effort, follow this order:

### Day 1: Quick Coverage Gains

```bash
# 1. Test video captions (419 LOC, 0% → should be ~95%)
# 2. Expand CMS tests (736 LOC, 26% → should be ~60%)
# 3. Quick MCP fixes (small, high impact)
```

Expected result: **43% → 50%** (+7 percentage points)

### Day 2: CMS and Video Expansion

```bash
# 1. Expand video module tests (complete coverage for timeline, builder, voiceover)
# 2. Finish CMS module tests (schema, references, graph, provenance)
# 3. Test publish/packager
```

Expected result: **50% → 60%** (+10 percentage points)

### Day 3: Freshness and Status

```bash
# 1. Test freshness tracking (scanner + registry)
# 2. Test status module (dashboard + views)
# 3. Test demos module
```

Expected result: **60% → 68%** (+8 percentage points)

### Day 4: Web Routes and Integrity

```bash
# 1. Expand web routes tests (insights, dependencies, search, freshness)
# 2. Test integrity module (asset verification, terminology)
# 3. Test remaining gaps
```

Expected result: **68% → 75-80%**

---

## Specific Test Recommendations

### cms/document.py (320 LOC, 41% coverage)

**Missing test coverage for:**
- Lines 36, 67, 71-79: Constructor and property initializers
- Lines 83-91, 95, 99-101: Metadata accessors
- Lines 105-127: Status and state methods
- Lines 154-183: Translation handling
- Lines 188-202, 206-207, 211-212, 216-230: Various accessors and mutators
- Lines 234-262: Complex methods like `get_related_documents()`, `resolve_references()`

**Test template:**
```python
def test_document_load_from_markdown():
    content = "---\ntitle: Test\nlanguage: en\n---\nBody text"
    doc = Document.from_markdown(content)
    assert doc.title == "Test"
    assert doc.body == "Body text"

def test_document_frontmatter_parsing():
    # Test YAML frontmatter extraction
    pass

def test_document_translation_detection():
    # Test source_document and source_version tracking
    pass
```

### video/voiceover.py (173 LOC, 18% coverage)

**Missing test coverage for:**
- Lines 50-59, 71-81, 86-87: Voiceover synthesis
- Lines 101-124, 129-135, 140-146: Audio processing
- Lines 173-209, 226-243: Audio file handling
- Lines 272-335, 356-392, 414-479: Complex audio/timing operations

**Test template:**
```python
def test_voiceover_synthesis():
    # Test text-to-speech synthesis
    pass

def test_voiceover_timing_calculation():
    # Test duration and timing calculation
    pass

def test_voiceover_audio_normalization():
    # Test audio level normalization
    pass
```

### cms/schema.py (219 LOC, 27% coverage)

**Missing test coverage for:**
- Lines 57-70, 74-104, 110-161: Schema validation logic
- Lines 165-194: Field type validation
- Lines 207-230, 235-261, 265-293: Complex validation rules

**Test template:**
```python
def test_schema_validates_required_fields():
    schema = load_schema()
    doc = {"title": "Test"}  # missing required field
    errors = schema.validate(doc)
    assert len(errors) > 0

def test_schema_validates_field_types():
    # Test type coercion and validation
    pass

def test_schema_validates_nested_objects():
    # Test nested structure validation
    pass
```

### freshness/scanner.py (128 LOC, 9% coverage)

**Missing test coverage for:**
- Lines 25-42: Scanner initialization
- Lines 47-72: Document staleness detection
- Lines 77-148, 153-189, 194-242: Complex scanning logic
- Lines 247-267: Stale document identification

**Test template:**
```python
def test_scanner_detects_recent_documents():
    # Documents updated today should not be stale
    pass

def test_scanner_detects_stale_documents():
    # Documents not updated in 30+ days should be stale
    pass

def test_scanner_respects_update_threshold():
    # Test configurable staleness threshold
    pass
```

---

## Coverage Goals by Module

### Core Modules (Target: 100%)
- ✓ `core/config.py` - 100%
- ✓ `core/theme.py` - 98% (add 1 line)
- ⚠ `core/project.py` - 71% (need +29%)

### CMS Module (Target: 80%)
- ✗ `cms/document.py` - 41% (need +39%)
- ✗ `cms/document_manager.py` - 35% (need +45%)
- ✗ `cms/graph.py` - 26% (need +54%)
- ✗ `cms/index.py` - 22% (need +58%)
- ✗ `cms/provenance.py` - 30% (need +50%)
- ✗ `cms/quality.py` - 22% (need +58%)
- ✗ `cms/references.py` - 18% (need +62%)
- ✓ `cms/schema.py` - 27% (need +53%)
- ✓ `cms/translation.py` - 90% (need +10%)

### Video Module (Target: 80%)
- ✗ `video/builder.py` - 41% (need +39%)
- ✗ `video/captions.py` - 0% (need +80%)
- ✗ `video/capture.py` - 0% (need +80%)
- ✗ `video/demo_registry.py` - 35% (need +45%)
- ✗ `video/scene_capture.py` - 23% (need +57%)
- ✗ `video/timeline.py` - 45% (need +35%)
- ✗ `video/voiceover.py` - 18% (need +62%)
- ✓ `video/quality.py` - 83%

### Other Critical Modules (Target: 80%)
- ⚠ `cms/references.py` - 18% (need +62%)
- ⚠ `publish/packager.py` - 13% (need +67%)
- ⚠ `freshness/registry.py` - 14% (need +66%)
- ⚠ `freshness/scanner.py` - 9% (need +71%)
- ⚠ `integrity/__init__.py` - 0% (need +80%)
- ⚠ `demos/__init__.py` - 0% (need +80%)

---

## Testing Infrastructure Notes

### Existing Test Files (19 total)
- **Well-structured**: test_core.py, test_cms.py, test_builders.py
- **Comprehensive**: test_security.py, test_links.py, test_readability.py
- **Need expansion**: test_video.py, test_web_routes.py, test_mcp_tools.py
- **Need creation**: test_video_captions.py, test_freshness.py, test_publish.py, test_demos.py, test_integrity.py, test_status.py

### Pytest Configuration
- **Fixtures available** in conftest.py: `temp_dir`, `sample_markdown`, `sample_config`, `sample_theme`
- **Test runner**: `uv run pytest`
- **Coverage command**: `uv run pytest --cov=media_engine --cov-report=term-missing`

### Best Practices (Follow Existing Tests)
1. Use AAA pattern (Arrange, Act, Assert)
2. Use fixtures for common setup
3. Use descriptive test names: `test_{function}_{scenario}()`
4. Group related tests in test classes when appropriate
5. Provide clear assertion messages

---

## Summary: Path to 80% Coverage

| Phase | Focus | Effort | Expected Gain |
|-------|-------|--------|-----------------|
| 1 | Quick wins (captions, CMS, MCP) | 2-3h | 43% → 50% |
| 2 | Video & CMS expansion | 3-4h | 50% → 60% |
| 3 | Freshness, Status, Demos | 3-4h | 60% → 68% |
| 4 | Web routes & Integrity | 3-4h | 68% → 78-80% |
| **Total** | **End-to-end testing** | **11-15h** | **43% → 80%** |

The most impactful targets are:
1. CMS module (4 large files, all <30%)
2. Video module (7 large files, all <50%)
3. Freshness tracking (2 files, 9-14%)
4. Publish/integrity/demos (3 files, 0%)

Estimated realistic timeline to reach 80%: **2-3 days of focused testing work**.
