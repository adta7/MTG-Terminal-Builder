# Phase 1: Layer 2 Bootstrap & Pattern Evolution

**Goal:** Build trustworthy mechanical tagging by identifying gaps, fixing patterns, and validating against golden set.

**Timeline:** 3-4 hours across these phases

---

## Phase 1A: Bootstrap with Test Data (30 min)

### Objectives
- Create a mini Scryfall dataset (mono-black cards)
- Load into database
- Run scanner to identify baseline gaps

### Tasks
- [ ] Create `tests/fixtures/sample_cards.json` (20-30 mono-black cards)
- [ ] Load cards into database
- [ ] Run scanner: coverage gaps
- [ ] Run scanner: unmatched phrases
- [ ] Generate reports
- [ ] Analyze output

**Success Criteria:**
- Scanner identifies zero-tag cards
- Unmatched phrase clusters show mechanic families
- Reports are human-readable

---

## Phase 1B: Analyze Gaps (30 min)

### Objectives
- Understand what patterns are missing
- Prioritize which patterns to add
- Document the backlog

### Tasks
- [ ] Read coverage gaps report
- [ ] Read unmatched phrase clusters
- [ ] Identify top 5 missing patterns
- [ ] Map patterns to test cards
- [ ] Create pattern backlog

**Success Criteria:**
- Clear list of 5+ missing patterns
- Each pattern has 2-3 example cards
- Priority ordering (common first)

---

## Phase 2: Add Missing Patterns (1-2 hours)

### Objectives
- Add 5-10 missing mechanical patterns
- Each pattern emits evidence
- All tests pass, no regressions

### Tasks (repeat for each pattern)
- [ ] Identify pattern (e.g., "Forced_Sacrifice")
- [ ] Write regex with multiple test cases
- [ ] Add to tags.py with confidence level
- [ ] Write 2+ unit tests (positive + negative)
- [ ] Run full test suite (expect 360+)
- [ ] Verify no golden test regressions

**Success Criteria:**
- Each new pattern has unit tests
- All 354+ tests passing
- Golden set integrity maintained
- Coverage gaps decrease in new scan

---

## Phase 3: Evidence Integration (30 min)

### Objectives
- Convert existing mechanical tagger to emit evidence
- Verify end-to-end evidence tracking
- Run validation script again

### Tasks
- [ ] Create evidence-emitting adapter for tag_mechanical()
- [ ] Update one rule as proof of concept
- [ ] Run scanner again
- [ ] Query evidence for tagged cards
- [ ] Verify rule_id, ability_kind, text_role present
- [ ] Run validation script
- [ ] Confirm output matches TEST 1

**Success Criteria:**
- Evidence emitted for all new tags
- Evidence query returns complete metadata
- Validation script shows "WORKING CORRECTLY"

---

## Phase 4: Final Validation (30 min)

### Objectives
- Full regression test
- Verify golden set
- Prepare for next phase

### Tasks
- [ ] Run full test suite
- [ ] Run golden set tests (should skip, that's ok)
- [ ] Run validate_foundation.py
- [ ] Review scanner output (improved coverage)
- [ ] Create summary report

**Success Criteria:**
- 360+ tests passing
- Golden set validation passes
- Scanner shows fewer gaps than baseline
- No regressions

---

## Testing Checkpoints

**After each phase, run:**

```bash
# Quick test
python -m pytest tests/ -q

# Full validation
python validate_foundation.py

# Check specific areas
python -m pytest tests/test_tags.py -v
python -m pytest tests/test_golden_mechanical_tags.py::TestGoldenSetIntegrity -v
```

---

## What to Commit After Each Phase

**Phase 1A:** Test data fixture
```bash
git add tests/fixtures/sample_cards.json
git commit -m "Add sample cards for testing"
```

**Phase 1B:** Analysis notes (optional, can be in LEARN.md)

**Phase 2:** New patterns
```bash
git add src/mtgdeck/tags.py tests/test_tags.py
git commit -m "Add 5 new mechanical patterns with evidence"
```

**Phase 3:** Evidence integration
```bash
git add src/mtgdeck/tags.py tests/test_tags.py
git commit -m "Integrate evidence emission in tag_mechanical()"
```

**Phase 4:** Final validation (no changes, just confirmation)

---

## Exit Criteria

✅ Phase 1 complete when:
- Scanner runs successfully
- Coverage gaps identified
- Unmatched phrases clustered

✅ Phase 2 complete when:
- 5+ patterns added
- All tests passing
- Golden set unbroken
- Coverage gaps reduced

✅ Phase 3 complete when:
- Evidence emitted for all tags
- Evidence queries working
- Validation script green

✅ Phase 4 complete when:
- 360+ tests passing
- No regressions
- Summary report generated

---

## Notes

- **Do NOT chase perfect 36k coverage.** Focus on black/colorless cards first.
- **Do NOT add patterns blindly.** Only add patterns identified by the scanner.
- **Do commit frequently.** One pattern = one commit.
- **Do test after each pattern.** Catch regressions early.
- **Do check the logs.** If a test fails, read the output carefully.

---

## Success Looks Like

At the end:
- Scanner runs on test data without errors
- Identifies specific gaps (e.g., "Forced_Sacrifice missing")
- 5-10 new patterns added with evidence
- All tests passing
- Coverage improved (fewer zero-tag cards)
- Golden set still intact
- Validation script confirms all systems working

**Ready to start Phase 1A?**
