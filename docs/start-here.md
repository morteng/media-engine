# Test Coverage Analysis - Start Here

## Current State
- **Overall Coverage**: 43% (9,109 / 15,901 lines)
- **Tests**: 554 passing, 10 skipped, 0 failed
- **Target**: 80% coverage
- **Gap**: 37 percentage points (need ~3,000 more lines tested)

## Three Key Documents

1. **COVERAGE_SUMMARY.txt** - Quick reference with priority rankings
2. **COVERAGE_ANALYSIS.md** - Detailed analysis with implementation plan
3. **TESTING_ROADMAP.md** - Function-level test templates and guidance

## Quick Start: The 5 Most Important Modules

### Top 5 Modules to Test First

**1. video/captions.py** (419 LOC, 0%)
   - What: WebVTT caption generation
   - Why: Completely untested, clear functionality
   - Effort: 45 minutes
   - Expected gain: +2% overall
   - Status: High priority (foundational for video)

**2. cms/document.py** (320 LOC, 41%)
   - What: Core document class and methods
   - Why: Only 41% tested, used everywhere
   - Effort: 2 hours
   - Expected gain: +8% overall
   - Status: CRITICAL (core module)

**3. cms/schema.py** (219 LOC, 27%)
   - What: Document schema validation
   - Why: Only 27% tested, affects all documents
   - Effort: 90 minutes
   - Expected gain: +5% overall
   - Status: CRITICAL (foundational)

**4. freshness/scanner.py** (128 LOC, 9%)
   - What: Document staleness detection
   - Why: Only 9% tested, new feature
   - Effort: 60 minutes
   - Expected gain: +2% overall
   - Status: Important (growing module)

**5. publish/packager.py** (259 LOC, 13%)
   - What: Deliverable packaging
   - Why: Only 13% tested, high user impact
   - Effort: 90 minutes
   - Expected gain: +5% overall
   - Status: High priority (release feature)

## The Path to 80%

### Week 1: Foundation (11-15 hours)

**Day 1: Quick Wins (3-4 hours)**
- [ ] Test video/captions.py (45 min)
- [ ] Expand cms/document.py tests (2 hours)
- [ ] Quick MCP tools tests (30 min)
- [ ] Result: 43% → 50% (+7%)

**Day 2: Core Module Strategy (4-5 hours)**
- [ ] Test cms/schema.py (90 min)
- [ ] Test cms/index.py (90 min)
- [ ] Test cms/references.py (90 min)
- [ ] Result: 50% → 60% (+10%)

**Day 3: Video & Freshness (4-5 hours)**
- [ ] Expand video/timeline.py tests (90 min)
- [ ] Test freshness/scanner.py (60 min)
- [ ] Test freshness/registry.py (120 min)
- [ ] Result: 60% → 68% (+8%)

**Day 4: Final Push (3-4 hours)**
- [ ] Test publish/packager.py (90 min)
- [ ] Test integrity module (90 min)
- [ ] Complete remaining gaps (60 min)
- [ ] Result: 68% → 80% (+12%)

## How to Use These Documents

### If you want: QUICK OVERVIEW
→ Read **COVERAGE_SUMMARY.txt** (5 min)

### If you want: DETAILED PLAN
→ Read **COVERAGE_ANALYSIS.md** (20 min) + **TESTING_ROADMAP.md** (20 min)

### If you want: TO START CODING
→ Open **TESTING_ROADMAP.md** and pick module from "Testing Priority Chart"

## Command Reference

```bash
# Run all tests with coverage
uv run pytest --cov=media_engine --cov-report=term-missing

# Test specific module
uv run pytest python/tests/test_cms.py -v

# Test with detailed output
uv run pytest -vv

# Create HTML coverage report
uv run pytest --cov=media_engine --cov-report=html
# Then open htmlcov/index.html
```

## Key Statistics

**Untested Modules (0%)**:
- video/captions.py (419 LOC)
- video/capture.py (705 LOC)
- publish/packager.py (259 LOC) - technically 13% but only 34 lines tested
- demos/__init__.py (795 LOC)
- integrity/__init__.py (427 LOC)

**Severely Undercovered (<20%)**:
- freshness/scanner.py (9%)
- status/views.py (8%)
- web/routes/search.py (10%)
- video/voiceover.py (18%)
- cms/references.py (18%)

**Partially Tested (20-70%)**:
- cms/index.py (22%)
- cms/quality.py (22%)
- cms/schema.py (27%)
- cms/graph.py (26%)
- video/timeline.py (45%)
- video/builder.py (41%)

**Well-Tested (>70%)**:
- core/config.py (100%)
- readability/__init__.py (100%)
- core/theme.py (98%)
- security/__init__.py (96%)
- cms/translation.py (90%)

## Success Criteria

**Phase 1 Complete** (3-4 hours)
- [ ] video/captions.py: 0% → 95%
- [ ] cms/document.py: 41% → 80%
- [ ] cms/schema.py: 27% → 80%
- [ ] Overall: 43% → 50%

**Phase 2 Complete** (4-5 hours)
- [ ] cms/index.py: 22% → 80%
- [ ] cms/references.py: 18% → 80%
- [ ] freshness/scanner.py: 9% → 80%
- [ ] Overall: 50% → 60%

**Phase 3 Complete** (4-5 hours)
- [ ] video/timeline.py: 45% → 80%
- [ ] freshness/registry.py: 14% → 80%
- [ ] publish/packager.py: 13% → 80%
- [ ] Overall: 60% → 70%

**Final Target** (2-3 hours)
- [ ] Remaining edge cases and error paths
- [ ] Overall: 70% → 80%+

## Test Infrastructure Ready?

✓ pytest configured and working (554 tests passing)
✓ Fixtures available (temp_dir, sample_config, sample_theme, sample_markdown)
✓ Coverage tools installed (pytest-cov)
✓ Good test examples to follow (test_security.py, test_links.py)
✓ AAA pattern established

You're ready to code! Start with **video/captions.py** for a quick win.

## Next Steps

1. Read COVERAGE_SUMMARY.txt (2 min)
2. Read COVERAGE_ANALYSIS.md Phase 1 section (5 min)
3. Pick a module from TESTING_ROADMAP.md
4. Create test file with provided templates
5. Run: `uv run pytest --cov=media_engine --cov-report=term-missing`
6. Iterate until coverage improves

Good luck! You've got this.
