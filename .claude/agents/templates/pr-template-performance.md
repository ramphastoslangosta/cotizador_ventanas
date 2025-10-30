## ⚡ Performance Optimization

**Task ID**: {TASK_ID}
**Priority**: {PRIORITY}
**Performance Impact**: {IMPACT_LEVEL}
**Related Code Review**: [Link to finding in report]

### 🎯 Performance Issue Description
{DETAILED_DESCRIPTION}

**Affected Components**:
- {COMPONENT_1} (current: {CURRENT_METRIC}, target: {TARGET_METRIC})
- {COMPONENT_2} (current: {CURRENT_METRIC}, target: {TARGET_METRIC})

### 🔍 Root Cause Analysis
{ROOT_CAUSE_EXPLANATION}

**Bottleneck Identified**:
- Location: {FILE_PATH} (lines {LINES})
- Metric: {METRIC_TYPE}
- Current Performance: {CURRENT_VALUE}
- Target Performance: {TARGET_VALUE}

### ✅ Optimizations Implemented
- [ ] Algorithm complexity reduced from O({BEFORE}) to O({AFTER})
- [ ] Database queries optimized ({N} queries → {M} queries)
- [ ] Caching implemented for {RESOURCE_TYPE}
- [ ] Async processing added for {OPERATION}
- [ ] Memory usage reduced
- [ ] Performance tests created

### 🧪 Benchmarking Results

**Before Optimization**:
```
{BENCHMARK_BEFORE}
```

**After Optimization**:
```
{BENCHMARK_AFTER}
```

**Improvement Summary**:
- Response Time: {BEFORE}ms → {AFTER}ms ({PERCENT}% improvement)
- Throughput: {BEFORE} req/s → {AFTER} req/s ({PERCENT}% improvement)
- Memory Usage: {BEFORE}MB → {AFTER}MB ({PERCENT}% reduction)
- Database Queries: {BEFORE} → {AFTER} ({PERCENT}% reduction)

### 📋 Performance Checklist
- [ ] Baseline metrics captured
- [ ] Optimization implemented
- [ ] Benchmarks run on representative data
- [ ] Load testing completed
- [ ] Memory profiling verified
- [ ] Database query analysis done
- [ ] No regression in other areas
- [ ] Monitoring configured

### 🚀 Deployment Plan
**Risk Level**: {RISK_LEVEL}

**Prerequisites**:
- [ ] Staging environment load tested
- [ ] Database indexes: {CREATED/MODIFIED/NONE}
- [ ] Cache configuration: {DETAILS}
- [ ] Resource limits adjusted: {DETAILS}

**Rollback Procedure**:
```bash
# Emergency rollback steps
git checkout main
git revert {COMMIT_HASH}
git push origin main
# Cache flush: {COMMANDS}
# Index rollback: {COMMANDS}
```

### 📊 Impact Analysis
- **User Experience**: {DESCRIPTION}
- **Infrastructure Cost**: {INCREASE/DECREASE/NEUTRAL} ({DETAILS})
- **Scalability**: {IMPROVEMENT_DESCRIPTION}
- **Database Load**: {IMPACT_DESCRIPTION}

### 👥 Reviewers Required
- [ ] @performance-lead (mandatory)
- [ ] @senior-developer
- [ ] @devops-team (for infrastructure impact)
- [ ] @database-admin (if DB changes)

### 🔗 Related Tasks
**Dependencies**: {DEPENDENCY_TASKS}
**Blocks**: {BLOCKED_TASKS}

---
**Estimated Effort**: {EFFORT} days
**Completion Deadline**: {DATE}
