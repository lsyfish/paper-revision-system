# CLAUDE.md — Paper Revision System

This file provides guidance for AI assistants working in this codebase.

---

## Project Overview

**Paper Revision System** (论文修改工作流系统) is a Python library and CLI tool for automated academic paper processing. It detects and removes AI writing traces, manages citations and references, identifies overlapping content, and restructures document sections — all operating on `.docx` files.

---

## Repository Structure

```
paper-revision-system/
├── src/                        # All production source code
│   ├── models.py               # Core dataclasses and enums (23+ types)
│   ├── exceptions.py           # Custom exception hierarchy
│   ├── paper_revision_system.py  # Main orchestrator + TaskPriorityManager
│   ├── docx_processor.py       # DOCX pack/unpack via zipfile + lxml
│   ├── humanizer.py            # AI trace detection & text humanization
│   ├── error_handler.py        # ErrorHandler + DegradationHandler + retry decorator
│   ├── validator.py            # Document consistency validation
│   ├── reference_manager.py    # Citation and bibliography management
│   ├── content_restructurer.py # Overlap detection + content migration
│   ├── rollback_manager.py     # Snapshot and rollback mechanism
│   └── academic_search.py      # Literature search (mock implementation)
├── tests/                      # 21 test files, ~6,900 lines
│   └── conftest.py             # Shared pytest fixtures
├── examples/                   # 6 runnable demo scripts
├── docs/                       # Implementation docs (Markdown)
├── humanizer_cli.py            # CLI entry point
├── requirements.txt
└── pytest.ini
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.x |
| DOCX parsing | `lxml` + `zipfile` (standard library) |
| Testing | `pytest`, `hypothesis` (property-based) |
| Coverage | `pytest-cov` |
| Test timeouts | `pytest-timeout` |

No external AI/LLM APIs. No database. No web framework. Pure Python library.

---

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run tests with coverage (configured by default in pytest.ini)
pytest --cov=src --cov-report=term-missing

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run a specific test file
pytest tests/test_humanizer.py -v

# CLI humanization tool
python humanizer_cli.py input.docx --output output.docx --language zh
python humanizer_cli.py input.docx --output output.docx --language en
python humanizer_cli.py input.docx --output output.docx --language auto
```

---

## Architecture: How Components Interact

### Main Workflow Pipeline

```
Input DOCX
    → DOCXProcessor.unpack()         # Extract XML from zip
    → TaskPriorityManager            # Assign and sort tasks by priority
    → Execute tasks sequentially     # Each executor modifies document
    → Validator                      # Post-modification consistency check
    → DOCXProcessor.pack()           # Repackage to DOCX
    → RevisionReport                 # Summary of all changes
```

### Task Priority Levels (execution order)

| Priority | Task Type |
|---|---|
| P1 | Abstract-Body Framework Alignment |
| P2 | Content Migration (remove overlaps) |
| P3 | Terminology Replacement |
| P4 | Research Limitations Documentation |
| P5 | Add References |
| P6 | Delete References |
| P7 | Fix Citations |
| P8 | Humanization (AI trace removal) |

Structure changes run before content changes, which run before reference management, which runs before language optimization.

### Key Classes and Their Roles

- **`PaperRevisionSystem`** — Top-level orchestrator. Registers task executors, drives the full pipeline, generates `RevisionReport`.
- **`TaskPriorityManager`** — Auto-assigns priority from task ID/description, sorts tasks before execution.
- **`DOCXProcessor`** — Wraps zipfile operations; produces `UnpackedDocument` containing parsed XML.
- **`HumanizeProcessor`** — 24+ regex patterns for detecting AI writing traits in Chinese and English; auto-detects language via 30% Chinese character threshold.
- **`ErrorHandler`** — Three-level handling: fatal (halt + cleanup), task-level (skip task + continue), warnings (record only).
- **`DegradationHandler`** — Runs advanced function; on failure falls back to simpler version. Tracks degradation count.
- **`RollbackManager`** — Snapshots document state; supports per-operation, per-task, and full rollback.
- **`ContentRestructurer`** — Computes similarity between sections; flags overlaps above 0.6 threshold.
- **`ReferenceManager`** — Parses `<w:p>` bibliography entries, maps citations to references, validates numbering.
- **`Validator`** — Checks abstract–body keyword alignment, sequential citation numbering, reference field completeness.

---

## Core Data Models (`src/models.py`)

Key dataclasses to know:

```python
UnpackedDocument   # Extracted DOCX with XML tree and metadata
ContentBlock       # A document section or paragraph
Reference          # Bibliography entry (authors, title, year, DOI, ...)
Citation           # In-text reference with location info
AITrace            # Detected AI artifact (pattern, confidence, suggestion)
Overlap            # Duplicate content detected between two sections
RevisionTask       # A single task (id, priority, status, modifications: List[Modification])
Modification       # One recorded change (type, timestamp, location, old, new, success)
RevisionReport     # Full execution summary (tasks, counts, success rates, duration)
ValidationError    # A validation issue (type, severity, description)
Literature         # Academic paper metadata for search results
```

Key enums:

```python
ModificationType   # CONTENT_MIGRATION, TERM_REPLACEMENT, REFERENCE_ADD, REFERENCE_DELETE,
                   # CITATION_FIX, ABSTRACT_ALIGN, HUMANIZATION
Language           # CHINESE, ENGLISH, AUTO
```

---

## Error Handling Conventions

This codebase uses a structured three-tier approach — follow it when adding new code:

1. **Fatal errors** (`PaperRevisionError`) — call `error_handler.handle_fatal_error()`. Saves progress to `paper_revision_progress.json`, runs cleanup, re-raises.
2. **Task-level errors** — call `error_handler.handle_task_error()`. Marks task as failed, logs context, continues with remaining tasks.
3. **Warnings** — call `error_handler.handle_warning()`. Recorded in report; does not interrupt execution.

For operations that may degrade gracefully (e.g., literature search, language optimization):

```python
result = degradation_handler.with_degradation(
    advanced_func, fallback_func, "context_name", *args
)
```

For transient failures (network, I/O), use the retry decorator:

```python
@retry_on_temporary_error(max_retries=3, base_delay=1.0)
def my_function(): ...
```

---

## Testing Conventions

### Test Categories (pytest markers)

| Marker | Purpose |
|---|---|
| `unit` | Single class/function in isolation |
| `integration` | Multi-component workflows |
| `property` | Hypothesis property-based tests |
| `slow` | Long-running tests |

### Coverage Requirement

> Maintain **>80% code coverage** for all new code. This is enforced by project contribution guidelines.

### Writing Tests

- Use fixtures from `tests/conftest.py` for shared document/task setup.
- Use `@given` from `hypothesis` for data-driven edge cases.
- Test modification recording: every task execution must produce `Modification` entries on the task object.
- Test rollback: after rollback, document state must match the pre-modification snapshot.

---

## Code Style

- **PEP 8** throughout. No exceptions.
- **Type hints** required on all public functions (use `typing` module).
- **Docstrings** on all modules, classes, and public methods.
- **Logging**: use structured logging. DEBUG for internal state, INFO for workflow milestones, WARNING for recoverable issues, ERROR/CRITICAL for failures.
- **Dataclasses** for structured data; avoid plain dicts for inter-module data transfer.
- **Enums** for fixed sets of values (never string literals for types).

### Commit Message Format

```
<type>: <short summary>

Types: feat, fix, refactor, test, docs, chore
Example: feat: add synonym-based term replacement strategy
```

---

## Key Constraints and Gotchas

1. **DOCX = ZIP + XML**: All document manipulation works on extracted XML via lxml. Never open `.docx` directly with Word API.
2. **XML namespaces**: Office Open XML uses namespaces (`w:`, `r:`, etc.). Always use the correct namespace prefix when querying/modifying XML nodes.
3. **Task priority is auto-assigned**: `TaskPriorityManager._extract_task_type()` infers type from task ID and description keywords. If your task isn't getting the right priority, check the keyword matching logic.
4. **Language detection**: `HumanizeProcessor` auto-detects Chinese vs English based on whether ≥30% of characters are Chinese. Pass `Language.CHINESE` or `Language.ENGLISH` explicitly if you need deterministic behavior.
5. **Modification recording is mandatory**: Every task executor must append `Modification` objects to `task.modifications`. The `RevisionReport` success rates depend on this.
6. **`AcademicSearchService` is a mock**: It returns synthetic data. A real implementation would integrate an external literature API.
7. **No environment variables**: Configuration is passed directly to constructors. There is no `.env` loading.
8. **Progress checkpoint**: On fatal error, state is saved to `paper_revision_progress.json` in the working directory for debugging/resumption.

---

## Adding New Features

### Adding a New Task Type

1. Add a value to `ModificationType` enum in `src/models.py`.
2. Add priority mapping in `TaskPriorityManager` in `src/paper_revision_system.py`.
3. Implement the executor function with signature `(task: RevisionTask, document: UnpackedDocument) -> RevisionTask`.
4. Register the executor: `system.register_task_executor(ModificationType.YOUR_TYPE, your_executor)`.
5. Write unit tests covering the executor logic and modification recording.

### Adding New AI Trace Patterns

Edit `src/humanizer.py`. Patterns are stored as compiled regex with metadata (pattern type, language, confidence). Add to the appropriate language section and add corresponding test cases in `tests/test_humanizer.py`.

### Adding New Validation Rules

Add a method to `Validator` in `src/validator.py` following the existing pattern: return `List[ValidationIssue]`. Call it from `generate_validation_report()`. Add tests in `tests/test_docx_validation.py`.
