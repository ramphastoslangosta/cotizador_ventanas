## 🏗️ Architecture Refactoring

**Task ID**: {TASK_ID}
**Priority**: {PRIORITY}
**Refactoring Type**: {TYPE}
**Related Code Review**: [Link to finding in report]

### 🎯 Architecture Issue Description
{DETAILED_DESCRIPTION}

**Current State**:
- Pattern: {CURRENT_PATTERN}
- Coupling: {COUPLING_LEVEL}
- SOLID Violations: {VIOLATIONS}
- Technical Debt: {DEBT_SCORE}

**Target State**:
- Pattern: {TARGET_PATTERN}
- Coupling: {TARGET_COUPLING}
- SOLID Compliance: {COMPLIANCE_LEVEL}
- Technical Debt Reduction: {REDUCTION_AMOUNT}

### 🔍 Root Cause Analysis
{ROOT_CAUSE_EXPLANATION}

**Design Issues**:
- {ISSUE_1}: {FILE_PATH} (lines {LINES})
- {ISSUE_2}: {FILE_PATH} (lines {LINES})
- {ISSUE_3}: {FILE_PATH} (lines {LINES})

### ✅ Refactoring Changes
- [ ] {PATTERN_NAME} pattern implemented
- [ ] Dependencies inverted (Dependency Inversion Principle)
- [ ] Interfaces segregated (Interface Segregation Principle)
- [ ] Single responsibility enforced
- [ ] Open/closed principle applied
- [ ] Liskov substitution verified
- [ ] Tests updated/created
- [ ] Documentation updated

### 🧪 Verification Evidence

**Before Refactoring**:
```
Complexity: {COMPLEXITY_SCORE}
Coupling: {COUPLING_SCORE}
Cohesion: {COHESION_SCORE}
```

**After Refactoring**:
```
Complexity: {COMPLEXITY_SCORE_AFTER}
Coupling: {COUPLING_SCORE_AFTER}
Cohesion: {COHESION_SCORE_AFTER}
```

**Code Examples**:

*Before*:
```{LANGUAGE}
{CODE_BEFORE}
```

*After*:
```{LANGUAGE}
{CODE_AFTER}
```

### 📋 Architecture Checklist
- [ ] SOLID principles reviewed
- [ ] Design patterns appropriately applied
- [ ] Separation of concerns enforced
- [ ] Dependencies properly managed
- [ ] Abstractions at correct level
- [ ] No circular dependencies
- [ ] Testability improved
- [ ] Backward compatibility maintained (or migration plan exists)

### 🚀 Deployment Plan
**Risk Level**: {RISK_LEVEL}

**Breaking Changes**: {YES/NO}
{BREAKING_CHANGES_DESCRIPTION}

**Prerequisites**:
- [ ] Migration scripts created: {DETAILS}
- [ ] Backward compatibility verified
- [ ] Integration tests passing
- [ ] Documentation updated

**Rollback Procedure**:
```bash
# Emergency rollback steps
git checkout main
git revert {COMMIT_HASH}
git push origin main
# Migration rollback: {COMMANDS}
# Data migration reversal: {STEPS}
```

### 📊 Impact Analysis
- **Code Maintainability**: {IMPROVEMENT_DESCRIPTION}
- **Testability**: {IMPROVEMENT_DESCRIPTION}
- **Future Extensibility**: {IMPROVEMENT_DESCRIPTION}
- **Team Productivity**: {IMPACT_DESCRIPTION}

### 🎓 Knowledge Transfer
**New Patterns Introduced**:
- {PATTERN_1}: {BRIEF_EXPLANATION}
- {PATTERN_2}: {BRIEF_EXPLANATION}

**Documentation**:
- Architecture Decision Record: {LINK}
- Design Documentation: {LINK}
- Migration Guide: {LINK}

### 👥 Reviewers Required
- [ ] @architect-lead (mandatory)
- [ ] @senior-developer
- [ ] @team-lead (for breaking changes)
- [ ] @qa-lead (for test coverage)

### 🔗 Related Tasks
**Dependencies**: {DEPENDENCY_TASKS}
**Blocks**: {BLOCKED_TASKS}
**Follow-up Tasks**: {FUTURE_TASKS}

---
**Estimated Effort**: {EFFORT} days
**Completion Deadline**: {DATE}
