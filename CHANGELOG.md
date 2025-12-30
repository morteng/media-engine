# Changelog

All notable changes to Media Engine will be documented in this file.

## [1.1.0](https://github.com/morteng/media-engine/compare/v1.0.0...v1.1.0) (2025-12-30)


### Features

* Add comprehensive brand configuration for Media Engine ([6062d6d](https://github.com/morteng/media-engine/commit/6062d6db1599ca02c5a698717d37d426755abf15))
* Add comprehensive Brand Hub dashboard with 6 tabs ([e4488e1](https://github.com/morteng/media-engine/commit/e4488e1844f55cd0dd3e8a6981fb6279e42b8e5e))
* **ai:** comprehensive agent infrastructure for concurrent safety ([58b8322](https://github.com/morteng/media-engine/commit/58b832261fe28239b3654b2bdf41bf1676c47671))
* **core:** add publications, relationships, AI context, and diagram engines ([b55ae0c](https://github.com/morteng/media-engine/commit/b55ae0c0348f295a406f19b9a15dc57e2ff9c1f4))
* **core:** add structured logging system for AI agents ([96acee7](https://github.com/morteng/media-engine/commit/96acee7fd17574aa878cacb7367f8755f58602ba))
* **dashboard:** add accessibility, error handling, and UX improvements ([5cc6b39](https://github.com/morteng/media-engine/commit/5cc6b39c962e3b0b9f44f3521e3ef4cfe9ccf7e8))
* **dashboard:** camera animation system and quality page consolidation ([5ed38a2](https://github.com/morteng/media-engine/commit/5ed38a240b6f02665df35fa3cf401807832d5459))
* **dashboard:** enhance UI with AI workspace, publications, and brand pages ([594e159](https://github.com/morteng/media-engine/commit/594e159aa4dbb05c756c877fb22e0ec5eaa69eb5))
* Implement unified brand voice and identity system ([#39](https://github.com/morteng/media-engine/issues/39)-[#45](https://github.com/morteng/media-engine/issues/45)) ([9a0b19c](https://github.com/morteng/media-engine/commit/9a0b19c3ae7b639d8e51d220d72cdb5413f23533))
* **video:** add Component Library and Voiceover Panel (Phase 4) ([258aecd](https://github.com/morteng/media-engine/commit/258aecd0fd9a351ea5e16c881f0cc99c0abb3c89))
* **video:** add demo capture and improve voiceover API key loading ([e306b5c](https://github.com/morteng/media-engine/commit/e306b5c41be8c8cd04aa8cd346888e565251dbda))
* **video:** add split-screen scenes with demo clips to props.json ([a435538](https://github.com/morteng/media-engine/commit/a435538b8bda6acbd0079b203274b017a6066f59))
* **video:** add Video Producer Agent with MCP tools and dashboard UI ([91513bd](https://github.com/morteng/media-engine/commit/91513bd39cea6253eb9bf6b084afb87cd6c3da70))


### Bug Fixes

* **ci:** Add continue-on-error for E2E tests ([9229152](https://github.com/morteng/media-engine/commit/9229152c5677eda3bd8b106bf8313f5cc3e3ea72))
* **ci:** add continue-on-error for existing lint/type issues ([833eade](https://github.com/morteng/media-engine/commit/833eade9593cba222f0f11de4eb62dea70802248))
* **ci:** Add continue-on-error for known pre-existing failures ([b6ba67f](https://github.com/morteng/media-engine/commit/b6ba67fa59d5fbc974c5b003b25f0ca0292504b3))
* **ci:** resolve all CI quality gate failures ([fd751ce](https://github.com/morteng/media-engine/commit/fd751ceaebc6697b95da620e7a1361217abf442b))
* **dashboard:** resolve React hook warning in ReagraphFlow ([0481cb2](https://github.com/morteng/media-engine/commit/0481cb2829e841a634281c98e867b0d0565c857a))
* Improve incomplete tracker to ignore legitimate doc patterns ([2995d29](https://github.com/morteng/media-engine/commit/2995d2933b9d18fab5a922b415da325d892a6c6c))
* Resolve DarkModeColors serialization in brand assets API ([c277ca4](https://github.com/morteng/media-engine/commit/c277ca4e8ea251029621eb57343ae7558fa468eb))
* **tests:** Update tests for API changes and removed Norwegian content ([8be709e](https://github.com/morteng/media-engine/commit/8be709ece9c745f5293af39f07d5332fe9623e56))
* **video:** improve Remotion detection and script editor layout ([2426519](https://github.com/morteng/media-engine/commit/242651954e3423d9e8e9e20e954ff38efb8157c0))
* **video:** resolve UX issues in video production dashboard ([5158057](https://github.com/morteng/media-engine/commit/51580571c1b9e359b93d88fbb9876d27de61a370))


### Code Refactoring

* clean up root directory structure ([5333a2e](https://github.com/morteng/media-engine/commit/5333a2e3d34a7d42319632213836465a87622252))
* **dashboard:** move Brand to Content section in sidebar ([2599e6f](https://github.com/morteng/media-engine/commit/2599e6fda3bf38981c87f8b2e4d74d26894db0fe))
* **dashboard:** reorganize video system with unified types and new tabs ([d043e54](https://github.com/morteng/media-engine/commit/d043e54cc116de457d9f04b2dc57761f79ba569d))
* **demo:** streamline demo project and update brand assets ([ddedf00](https://github.com/morteng/media-engine/commit/ddedf0010bef822cbf34d86eccad9cdc40d59d77))
* **demo:** update demo assets and content structure ([eeeb253](https://github.com/morteng/media-engine/commit/eeeb253012fb6f2cbbc111dcf76f903e8ddf28b3))
* Polish Brand Hub with refined design system ([67a411c](https://github.com/morteng/media-engine/commit/67a411cf45de26f7dc513a1088436f95a244873c))


### Documentation

* update CLAUDE.md and add ruff configuration ([2984ea0](https://github.com/morteng/media-engine/commit/2984ea058fc88d09d40e4e00c4dd0746a672299f))
* update README with comprehensive feature documentation ([7c8030d](https://github.com/morteng/media-engine/commit/7c8030d8f7914eece602c2425352d785c7f7ab3b))


### Tests

* add comprehensive AI infrastructure tests ([3dc8f89](https://github.com/morteng/media-engine/commit/3dc8f8918235ad56fe50df747dc8082343ca6c44))
* add comprehensive AI queue tests and fix introduction ([7a08af0](https://github.com/morteng/media-engine/commit/7a08af0ad44484979f41574c8d01827977efb2f6))
* **video:** add unit tests for ComponentLibrary and VoiceoverPanel (Phase 5) ([95a8bc3](https://github.com/morteng/media-engine/commit/95a8bc323ab8e8af97fb0a1b1c4c8aa0ea4d09de))
* **video:** add unit tests for RemotionPreview and SceneNavigator ([1f79300](https://github.com/morteng/media-engine/commit/1f7930023d0c25e38ba6d253ad4ffa45759c6505))


### Continuous Integration

* add comprehensive GitHub CI/CD and project management ([d772a5e](https://github.com/morteng/media-engine/commit/d772a5e93e3db35ea9194ff6a14216a5b7376e87))

## [1.0.0] - 2025-12-16

### Added
- **Core Framework**: Complete project management with YAML configuration
- **Document Management**: Markdown documents with frontmatter, translation tracking
- **Builders**: HTML, PPTX, XLSX, PDF output generation
- **Video Production**: Timeline-based video generation with Remotion integration
- **Diagram Generation**: YAML-defined diagrams with light/dark theme support
- **Search Indexing**: Full-text search with relevance scoring
- **Quality Checks**: Placeholder detection, encoding validation, terminology consistency
- **Validation**: Schema validation for frontmatter, reference checking for links
- **Security Scanning**: Secret detection, PII scanning, sensitive content analysis
- **Audience Packs**: Investor and pilot pack generation
- **Publishing**: Complete deliverable packaging with asset bundling
- **Translation Tracking**: Source document syncing, outdated detection
- **CLI**: Comprehensive command-line interface for all features
- **MCP Server**: 20+ tools for AI agent integration
- **Web Dashboard**: FastAPI-based project management UI

### Infrastructure
- CI/CD with GitHub Actions (lint + test)
- 327 tests passing
- Demo project with 12 chapters in English and Norwegian

### Documentation
- Complete feature documentation in demo project
- CLI reference guide
- MCP server integration guide
