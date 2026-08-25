# 🛠️ Developer Guidelines & Important Notes

## ⚠️ Critical Tool Behavior: File Editing

### The "Apply" Button Requirement

**IMPORTANT**: When the assistant suggests file changes using `edit_existing_file` or `single_find_and_replace` tools:

1. **The change is only a suggestion/preview** - it does NOT automatically save
2. **YOU MUST CLICK THE "APPLY" BUTTON** for changes to actually be saved to the file
3. Without clicking Apply, the running application will continue using old code

### Workflow Steps
```
Step 1: Assistant uses edit tool → Shows code diff suggestion
       ↓
Step 2: YOU click "Apply" button ← CRITICAL STEP!
       ↓
Step 3: File is actually modified on disk
       ↓
Step 4: Test the application (restart if needed)
       ↓
Step 5: Report results for next iteration
```

### Example Scenario
```python
# Assistant suggests:
# "Edit: Remove QApplication.invokeLater() wrapper"
# [Shows diff preview]

❌ WRONG: Just read the suggestion and move on
✅ CORRECT: Click "Apply", then test the app, then report results
```

---

## Git Workflow

### Commit Strategy (Recommended)
- **Separate commits per logical fix** for better traceability
- Use descriptive messages referencing specific issues
- Example: `fix(engine): update callback signature for Diffusers v0.31+ API`

### Standard Commit Format
```bash
git add <files>
git commit -m "<type>(<scope>): <subject>"

Types: feat, fix, docs, style, refactor, test, chore
Scopes: engine, ui, core, model_manager, etc.
```

---

## Documentation Updates

### When to Update Docs
- After fixing critical bugs (add to CHANGELOG.md)
- At end of each session (update DEVELOPMENT_LOG.md)
- Before feature completion (update CURRENT_TASK.md)

### Doc File Purposes
| File | Purpose | Update Frequency |
|------|---------|------------------|
| CHANGELOG.md | Version history & releases | After significant changes |
| DEVELOPMENT_LOG.md | Daily activities & decisions | End of each session |
| CURRENT_TASK.md | Active issues list | When task status changes |
| TODO_LIST.md | Feature roadmap | Major milestone completion |

---

## Debugging Tips

### Progress Bar Issues
- Check if data is being received (terminal logs)
- Verify callback signature matches library version
- Ensure UI updates happen on main thread
- Add debug `print()` statements at key points

### Sampler Parameter Issues
- Verify parameter flows from UI → Engine → Diffusers
- Check if sampler must be set at pipeline creation time
- Review Diffusers v0.31+ release notes for breaking changes

---

## Common Pitfalls to Avoid

1. **Forgetting to click Apply** when editing files (most common!)
2. Assuming `QApplication.invokeLater()` works in PyQt6 (it doesn't)
3. Using old Diffusers API signatures with v0.31+
4. Modifying files without updating documentation
5. Committing multiple unrelated changes in one commit

---

*Developer Guidelines v0.1 | Last Updated: 2025-08-23*
