# Tasks: Source Management & Podcast Summarization

**Input**: Design documents from `/specs/001-daily-news-aggregation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-interface.md, contracts/config-schema.md, quickstart.md

**Tests**: All test tasks MUST be written and verified to FAIL before implementation tasks per constitution TDD principle (NON-NEGOTIABLE).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Note**: This task breakdown extends the existing Daily News Aggregation implementation. The project structure, models, services, config loader, and CLI already exist. These tasks cover two NEW capabilities: source management and podcast summarization.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

Single project structure at repository root:
- `src/` for source code
- `tests/` for test code
- `~/.ai-digest/` for runtime cache and config

---

## Phase 1: Setup

**Purpose**: Project configuration updates for new features

- [ ] T001 Update pyproject.toml with optional `[project.optional-dependencies]` podcast extras (`yt-dlp>=2024.1,<2026`, `faster-whisper>=1.0,<2`) in pyproject.toml
- [ ] T002 [P] Update requirements.txt to document optional podcast dependencies with install instructions in requirements.txt

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure changes that MUST be complete before either user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Implement config save support in src/config/loader.py (read current config → modify in-memory → backup to `.bak` → write to `~/.ai-digest/config.json` via stdlib `json` per config-schema.md Config Write Contract)
- [ ] T004 [P] Implement config merge logic in src/config/loader.py (on load: TOML base settings + JSON overrides for `sources.enabled` and `sources.custom` per config-schema.md merge strategy)
- [ ] T005 Refactor src/cli/commands.py to use argparse subparsers (add `sources` and `podcast` subcommand groups alongside existing default digest behavior per cli-interface.md)
- [ ] T006 Update src/cli/__main__.py to dispatch subcommands (`sources` → source handlers, `podcast` → podcast handler, default → existing digest flow)

**Checkpoint**: Foundation ready — subcommand routing works, config can be read and written, user story implementation can begin

---

## Phase 3: User Story 1 — Source Management (Priority: P1) 🎯 MVP

**Goal**: Users can manage their news source list (list, add, remove, enable, disable) via CLI without manually editing config files

**Independent Test**: Run `ai-digest sources add --name "Test Blog" --url https://test.com/feed.xml`, then `ai-digest sources list` and verify the new source appears. Run `ai-digest sources disable hackernews` and verify it shows as disabled. Run `ai-digest sources remove test-blog` and verify it is gone.

### Tests for User Story 1 (TDD — Write and verify FAIL first) ⚠️

- [ ] T007 [P] [US1] Unit test for generate_source_id() slug generation (name → lowercase-hyphens, strip non-alphanumeric, uniqueness check) in tests/unit/test_source_manager.py
- [ ] T008 [P] [US1] Unit test for list_sources() merging built-in + custom sources with enabled status in tests/unit/test_source_manager.py
- [ ] T009 [P] [US1] Unit test for add_source() with URL validation, method validation, and duplicate ID rejection in tests/unit/test_source_manager.py
- [ ] T010 [P] [US1] Unit test for remove_source() rejecting built-in sources and accepting custom sources in tests/unit/test_source_manager.py
- [ ] T011 [P] [US1] Unit test for enable_source() and disable_source() with last-source guard (cannot disable all) in tests/unit/test_source_manager.py
- [ ] T012 [P] [US1] Contract test for `ai-digest sources list` output format (table with ✓/✗ indicators, built-in vs custom grouping) in tests/contract/test_cli_sources.py
- [ ] T013 [P] [US1] Contract test for `ai-digest sources add` success and error cases (duplicate ID, invalid URL, invalid method) in tests/contract/test_cli_sources.py
- [ ] T014 [P] [US1] Contract test for `ai-digest sources remove` custom vs built-in rejection with correct exit codes in tests/contract/test_cli_sources.py
- [ ] T015 [P] [US1] Contract test for `ai-digest sources enable/disable` with already-enabled/disabled and last-source guard in tests/contract/test_cli_sources.py
- [ ] T016 [US1] Integration test for full source lifecycle (add → list → disable → enable → remove → list) with config.json persistence in tests/integration/test_source_management.py

### Implementation for User Story 1

- [ ] T017 [US1] Implement generate_source_id() in src/services/source_manager.py (lowercase, replace spaces/special chars with hyphens, strip non-alphanumeric, validate uniqueness against all sources)
- [ ] T018 [US1] Implement list_sources() in src/services/source_manager.py (read built-in from src/config/sources.py + custom from config, merge enabled status, return sorted list)
- [ ] T019 [US1] Implement add_source() in src/services/source_manager.py (validate URL starts with http/https, validate method in [rss, api, html], check ID uniqueness, append to custom sources, add to enabled list, save config)
- [ ] T020 [US1] Implement remove_source() in src/services/source_manager.py (reject built-in with error message suggesting `disable`, remove custom source from config, remove from enabled list, save config)
- [ ] T021 [US1] Implement enable_source() and disable_source() in src/services/source_manager.py (verify source exists, check last-source guard on disable, update enabled list, save config)
- [ ] T022 [US1] Add `sources` subcommand argument parser with list/add/remove/enable/disable actions in src/cli/commands.py (--name, --url, --method for add; source_id positional for remove/enable/disable per cli-interface.md)
- [ ] T023 [US1] Implement sources CLI handlers dispatching to source_manager functions in src/cli/commands.py (map subcommand action → source_manager call, handle return values and errors)
- [ ] T024 [US1] Implement sources list output formatting in src/cli/formatter.py (table with ✓/✗ status, built-in vs custom sections, source_id/name/method/url columns per cli-interface.md)
- [ ] T025 [US1] Add error message formatting for source management edge cases in src/cli/commands.py (duplicate ID, built-in removal rejection, last-source guard, non-existent source per cli-interface.md)

**Checkpoint**: User can run all `ai-digest sources` subcommands. Sources persist across sessions via config.json. Built-in sources protected from removal.

---

## Phase 4: User Story 2 — Podcast Summarization (Priority: P2)

**Goal**: Users can provide a podcast URL and receive a transcribed, summarized text output — all processed locally without cloud APIs

**Independent Test**: Run `ai-digest podcast https://example.com/episode.mp3 --model tiny` with mocked dependencies, verify output includes title, duration, transcript word count, summary text, and compression ratio in the specified format. Verify missing dependency detection with clear install instructions.

### Tests for User Story 2 (TDD — Write and verify FAIL first) ⚠️

- [ ] T026 [P] [US2] Unit test for PodcastEpisode dataclass validation (valid URL, non-empty title ≥3 chars, duration ≥0) in tests/unit/test_podcast_service.py
- [ ] T027 [P] [US2] Unit test for PodcastSummary dataclass validation (non-empty transcript ≥100 chars, non-empty summary, compression ratio 0.01–0.5, valid model_size) in tests/unit/test_podcast_service.py
- [ ] T028 [P] [US2] Unit test for check_podcast_dependencies() detecting yt-dlp and faster-whisper availability in tests/unit/test_podcast_service.py
- [ ] T029 [P] [US2] Unit test for download_podcast_audio() with mocked subprocess (yt-dlp success, failure, timeout) in tests/unit/test_podcast_service.py
- [ ] T030 [P] [US2] Unit test for transcribe_audio() with mocked WhisperModel (segments to text, model selection) in tests/unit/test_podcast_service.py
- [ ] T031 [P] [US2] Unit test for clean_transcript() removing filler words (um, uh, like, you know) and collapsing whitespace in tests/unit/test_podcast_service.py
- [ ] T032 [P] [US2] Unit test for summarize_podcast() full pipeline with mocked download and transcribe stages in tests/unit/test_podcast_service.py
- [ ] T033 [P] [US2] Contract test for `ai-digest podcast <URL>` output format (title, source, URL, duration, transcript words, model, summary, compression) in tests/contract/test_cli_podcast.py
- [ ] T034 [P] [US2] Contract test for `ai-digest podcast` error cases (missing deps exit code 1, download failure exit code 4, transcription failure exit code 5, invalid model) in tests/contract/test_cli_podcast.py
- [ ] T035 [US2] Integration test for full podcast pipeline (download → transcribe → clean → summarize) with mocked external tools in tests/integration/test_podcast_summary.py

### Implementation for User Story 2

- [ ] T036 [P] [US2] Create PodcastEpisode dataclass in src/models/podcast.py (episode_id UUID, url, title, audio_path, duration_seconds, source_name, downloaded_at with validation per data-model.md §5)
- [ ] T037 [P] [US2] Create PodcastSummary dataclass in src/models/podcast.py (summary_id UUID, episode_id, transcript, transcript_word_count, summary, summary_word_count, compression_ratio, model_size, transcription_time_seconds, processed_at with validation per data-model.md §6)
- [ ] T038 [US2] Implement check_podcast_dependencies() in src/services/podcast_service.py (check yt-dlp on PATH via shutil.which, check faster-whisper importable, return clear error messages with install instructions)
- [ ] T039 [US2] Implement download_podcast_audio() in src/services/podcast_service.py (subprocess.run yt-dlp with --extract-audio --audio-format wav --no-playlist, timeout 300s, return audio file path per research.md §8.1)
- [ ] T040 [US2] Implement transcribe_audio() in src/services/podcast_service.py (WhisperModel with device=cpu compute_type=int8, language=en, join segment texts, return transcript per research.md §8.2)
- [ ] T041 [US2] Implement clean_transcript() in src/services/podcast_service.py (regex remove filler words, collapse whitespace per research.md §8.3)
- [ ] T042 [US2] Implement summarize_podcast() pipeline in src/services/podcast_service.py (download → transcribe → clean → reuse frequency_summarize(ratio=0.3) from src/services/summarizer.py → build PodcastSummary → cleanup temp files per research.md §8.3)
- [ ] T043 [US2] Add `podcast` subcommand argument parser in src/cli/commands.py (URL positional arg, --model flag with choices [tiny, base, small, medium] default from config per cli-interface.md)
- [ ] T044 [US2] Implement podcast CLI handler in src/cli/commands.py (check dependencies first, call summarize_podcast, handle exit codes 0/1/4/5, print progress to stderr)
- [ ] T045 [US2] Implement podcast summary output formatting in src/cli/formatter.py (title, source, URL, duration, transcript word count, model, summary text, compression % per cli-interface.md)
- [ ] T046 [US2] Add podcast config defaults loading (`[podcast]` section: default_model, cleanup_audio, max_duration_seconds) in src/config/loader.py

**Checkpoint**: User can run `ai-digest podcast <URL>` to get a formatted summary. Missing dependencies show clear install instructions. Transcription runs locally on CPU.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and cleanup across both user stories

- [ ] T047 [P] Update README.md with source management CLI usage examples (list, add, remove, enable, disable per quickstart.md §Managing Sources)
- [ ] T048 [P] Update README.md with podcast summarization usage, prerequisites, and model selection guide per quickstart.md §Podcast Summarization
- [ ] T049 [P] Add `[podcast]` section with commented defaults to config file generation on first run in src/config/loader.py
- [ ] T050 [P] Run quickstart.md validation (verify all source management and podcast examples work end-to-end)
- [ ] T051 [P] Validate exit codes match cli-interface.md contract (0 success, 1 arg/config error, 4 download failure, 5 transcription failure)
- [ ] T052 Code cleanup with ruff across all new and modified files (src/services/source_manager.py, src/services/podcast_service.py, src/models/podcast.py, src/cli/commands.py, src/cli/formatter.py, src/config/loader.py)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 - Source Management (Phase 3)**: Depends on Foundational (Phase 2) — specifically T003/T004 for config save and T005/T006 for subcommand routing
- **User Story 2 - Podcast Summarization (Phase 4)**: Depends on Foundational (Phase 2) — specifically T005/T006 for subcommand routing. Does NOT depend on US1.
- **Polish (Phase 5)**: Depends on both user stories being complete

### User Story Dependencies

- **User Story 1 (P1 — Source Management)**: Can start after Foundational (Phase 2). No dependencies on US2.
- **User Story 2 (P2 — Podcast Summarization)**: Can start after Foundational (Phase 2). No dependencies on US1. Can be implemented in parallel with US1.

### Within Each User Story (TDD Workflow)

1. **Tests FIRST**: Write ALL test tasks for the story, verify they FAIL
2. **Models**: Create/update data models (can be parallel if different files)
3. **Services**: Implement core logic (depends on models)
4. **CLI**: Wire CLI handlers (depends on services)
5. **Validation**: Run tests, verify GREEN, commit story

### Parallel Opportunities

- **Phase 1 (Setup)**: T001 and T002 [P] can run in parallel
- **Phase 2 (Foundational)**: T003/T004 (config) and T005/T006 (CLI) operate on different files — can run in parallel as two pairs
- **Phase 3 (US1 Tests)**: T007–T011 [P] (unit tests) can run in parallel. T012–T015 [P] (contract tests) can run in parallel.
- **Phase 3 (US1 Implementation)**: T017–T021 sequential within source_manager.py. T022–T025 depend on source_manager being complete.
- **Phase 4 (US2 Tests)**: T026–T032 [P] (unit tests) can all run in parallel. T033–T034 [P] (contract tests) can run in parallel.
- **Phase 4 (US2 Implementation)**: T036/T037 [P] can run in parallel (independent dataclasses). T038–T042 sequential within podcast_service.py. T043/T044 depend on service completion.
- **US1 and US2 can be implemented fully in parallel** after Foundational phase completes (different service files, different test files, shared CLI file needs coordination only for subcommand parsers).
- **Phase 5 (Polish)**: T047–T051 [P] can all run in parallel.

---

## Parallel Example: User Story 1 (Source Management)

```bash
# Launch all unit test tasks in parallel (TDD — verify FAIL first):
Task: "Unit test for generate_source_id() in tests/unit/test_source_manager.py"
Task: "Unit test for list_sources() in tests/unit/test_source_manager.py"
Task: "Unit test for add_source() in tests/unit/test_source_manager.py"
Task: "Unit test for remove_source() in tests/unit/test_source_manager.py"
Task: "Unit test for enable/disable_source() in tests/unit/test_source_manager.py"

# Launch all contract test tasks in parallel:
Task: "Contract test for sources list in tests/contract/test_cli_sources.py"
Task: "Contract test for sources add in tests/contract/test_cli_sources.py"
Task: "Contract test for sources remove in tests/contract/test_cli_sources.py"
Task: "Contract test for sources enable/disable in tests/contract/test_cli_sources.py"

# After all tests FAIL, implement source_manager.py sequentially:
Task: "Implement generate_source_id() in src/services/source_manager.py"
Task: "Implement list_sources() in src/services/source_manager.py"
Task: "Implement add_source() in src/services/source_manager.py"
Task: "Implement remove_source() in src/services/source_manager.py"
Task: "Implement enable/disable_source() in src/services/source_manager.py"

# Then wire CLI (depends on source_manager):
Task: "Add sources subcommand parser in src/cli/commands.py"
Task: "Implement sources CLI handlers in src/cli/commands.py"
```

---

## Parallel Example: User Story 2 (Podcast Summarization)

```bash
# Launch all unit test tasks in parallel (TDD — verify FAIL first):
Task: "Unit test for PodcastEpisode model in tests/unit/test_podcast_service.py"
Task: "Unit test for PodcastSummary model in tests/unit/test_podcast_service.py"
Task: "Unit test for check_podcast_dependencies() in tests/unit/test_podcast_service.py"
Task: "Unit test for download_podcast_audio() in tests/unit/test_podcast_service.py"
Task: "Unit test for transcribe_audio() in tests/unit/test_podcast_service.py"
Task: "Unit test for clean_transcript() in tests/unit/test_podcast_service.py"
Task: "Unit test for summarize_podcast() in tests/unit/test_podcast_service.py"

# After all tests FAIL, implement models (parallel):
Task: "Create PodcastEpisode dataclass in src/models/podcast.py"
Task: "Create PodcastSummary dataclass in src/models/podcast.py"

# Then implement service (sequential):
Task: "Implement check_podcast_dependencies() in src/services/podcast_service.py"
Task: "Implement download_podcast_audio() in src/services/podcast_service.py"
Task: "Implement transcribe_audio() in src/services/podcast_service.py"
Task: "Implement clean_transcript() in src/services/podcast_service.py"
Task: "Implement summarize_podcast() pipeline in src/services/podcast_service.py"

# Then wire CLI:
Task: "Add podcast subcommand parser in src/cli/commands.py"
Task: "Implement podcast CLI handler in src/cli/commands.py"
```

---

## Implementation Strategy

### MVP First (Source Management Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T006) — **CRITICAL BLOCKER**
3. Complete Phase 3: User Story 1 — Source Management (T007–T025)
4. **STOP and VALIDATE**: Run `ai-digest sources list`, `ai-digest sources add`, verify all subcommands work
5. Deploy/demo MVP: Users can manage their source list interactively

**MVP Delivers**: Interactive source management without config file editing

### Incremental Delivery

1. Setup + Foundational → Infrastructure ready (T001–T006)
2. Add US1 (Source Management) → Test independently → Source CRUD via CLI (T007–T025)
3. Add US2 (Podcast Summarization) → Test independently → Audio → text → summary (T026–T046)
4. Polish → Documentation and cleanup (T047–T052)

### Parallel Team Strategy

With two developers (after Foundational Phase 2 complete):

1. **Both complete Setup + Foundational together** (T001–T006)
2. **Parallel implementation**:
   - Developer A: User Story 1 — Source Management (T007–T025)
   - Developer B: User Story 2 — Podcast Summarization (T026–T046)
3. **Both converge on Polish** (T047–T052)

---

## TDD Workflow Per Story

**CRITICAL**: Constitution mandates Test-First approach (NON-NEGOTIABLE)

For each user story:

1. **RED**: Write ALL test tasks, run pytest, verify failures
2. **GREEN**: Implement code tasks, run pytest until all pass
3. **REFACTOR**: Clean up, run pytest to ensure still green
4. **COMMIT**: Story complete, tests passing

**Example (US1 — Source Management)**:

```bash
# Step 1: RED
pytest tests/unit/test_source_manager.py       # FAIL (module not found)
pytest tests/contract/test_cli_sources.py       # FAIL (subcommand not implemented)
pytest tests/integration/test_source_management.py  # FAIL

# Step 2: GREEN
# Implement T017–T025
pytest tests/unit/test_source_manager.py       # PASS
pytest tests/contract/test_cli_sources.py       # PASS
pytest tests/integration/test_source_management.py  # PASS

# Step 3: REFACTOR
ruff check src/services/source_manager.py
ruff check src/cli/commands.py
pytest tests/                                   # All PASS

# Step 4: COMMIT
git add src/services/source_manager.py src/cli/ src/config/loader.py tests/
git commit -m "US1: Implement source management CLI"
```

---

## Success Validation

After implementation, verify:

- **Source Management**:
  - `ai-digest sources list` shows all 22+ built-in sources with status indicators
  - `ai-digest sources add --name "Test" --url https://test.com/feed.xml` creates source with ID `test`
  - `ai-digest sources remove test` removes custom source
  - `ai-digest sources remove hackernews` fails with "use disable instead" message
  - `ai-digest sources disable <id>` marks source as disabled
  - Disabling last enabled source fails with guard message
  - Changes persist in `~/.ai-digest/config.json` across sessions
  - Config backup (`.bak`) created on each write

- **Podcast Summarization**:
  - `ai-digest podcast <URL>` produces formatted summary output
  - `ai-digest podcast <URL> --model tiny` uses tiny model
  - Missing `yt-dlp` shows clear install instructions (exit code 1)
  - Missing `faster-whisper` shows clear install instructions (exit code 1)
  - Download failure returns exit code 4
  - Transcription failure returns exit code 5
  - Temp audio files cleaned up after processing
  - Summary compression ratio logged

---

## Notes

- **[P] tasks**: Different files or independent functions, no dependencies, can execute in parallel
- **[Story] label**: Maps task to specific user story (US1 = Source Management, US2 = Podcast) for traceability
- **TDD mandatory**: Constitution requires tests BEFORE implementation — NON-NEGOTIABLE
- **File paths explicit**: Every task includes exact file path for clarity
- **Independent stories**: US1 and US2 are fully independent and can be implemented in parallel
- **Existing code reuse**: podcast summarization reuses `frequency_summarize()` from src/services/summarizer.py
- **Optional deps**: Podcast dependencies (yt-dlp, faster-whisper) are optional extras — base install unchanged
- **Config strategy**: Reads TOML (tomllib stdlib), writes JSON (json stdlib) — no new dependencies for source management
- **Verify tests fail**: Before implementing, run pytest to confirm RED state
- **Commit frequently**: After each task or logical group
- **Stop at checkpoints**: Validate story independently before moving to next
