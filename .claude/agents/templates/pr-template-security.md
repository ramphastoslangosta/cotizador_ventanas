## 🔒 Security Vulnerability Fix

**Task ID**: {TASK_ID}
**Priority**: {PRIORITY}
**Severity**: {SEVERITY}
**Related Code Review**: [Link to finding in report]

### 🎯 Vulnerability Description
{DETAILED_DESCRIPTION}

**Affected Files**:
- {FILE_PATH_1} (lines {LINES})
- {FILE_PATH_2} (lines {LINES})

### 🔍 Root Cause Analysis
{ROOT_CAUSE_EXPLANATION}

### ✅ Solution Implemented
- [ ] Vulnerability patched with {SOLUTION_TYPE}
- [ ] Input validation added
- [ ] Output sanitization implemented
- [ ] Security tests created
- [ ] Code review by security team
- [ ] Documentation updated

### 🧪 Testing Evidence

**Before Fix**:
```
{VULNERABILITY_DEMONSTRATION}
```

**After Fix**:
```
{PATCHED_BEHAVIOR}
```

**Test Coverage**:
- Unit tests: {TEST_FILE} (lines {LINES})
- Integration tests: {TEST_FILE} (lines {LINES})
- Security tests: {TEST_FILE} (lines {LINES})

### 📋 Security Checklist
- [ ] OWASP Top 10 reviewed
- [ ] Input validation comprehensive
- [ ] Output encoding correct
- [ ] Authentication verified
- [ ] Authorization enforced
- [ ] Secrets removed from code
- [ ] Error messages sanitized
- [ ] Logging doesn't expose sensitive data
- [ ] Rate limiting considered
- [ ] Session management secure

### 🚀 Deployment Plan
**Risk Level**: {RISK_LEVEL}

**Prerequisites**:
- [ ] Staging environment tested
- [ ] Database migrations: {YES/NO}
- [ ] Configuration changes: {DETAILS}
- [ ] Monitoring alerts configured

**Rollback Procedure**:
```bash
# Emergency rollback steps
git checkout main
git revert {COMMIT_HASH}
git push origin main
# Additional cleanup: {STEPS}
```

### 📊 Performance Impact
- Response time delta: {MEASUREMENT}
- Memory usage delta: {MEASUREMENT}
- Database query impact: {MEASUREMENT}

### 👥 Reviewers Required
- [ ] @security-lead (mandatory)
- [ ] @senior-developer
- [ ] @devops-team (for deployment)

### 🔗 Related Tasks
**Dependencies**: {DEPENDENCY_TASKS}
**Blocks**: {BLOCKED_TASKS}

---
**Estimated Effort**: {EFFORT} days
**Completion Deadline**: {DATE}
