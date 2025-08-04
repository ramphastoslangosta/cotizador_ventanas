# Development Protocol - Window Quotation System

## 🔄 **Standard Development Workflow**

This document establishes the protocol for making changes to the Window Quotation System deployed on DigitalOcean.

---

## 📋 **Pre-Development Checklist**

### 1. **System Analysis Phase**
- [ ] Study existing code structure and dependencies
- [ ] Identify all affected files and components
- [ ] Review database schema and model relationships
- [ ] Check for existing similar implementations
- [ ] Document current state vs desired state

### 2. **Planning Phase**
- [ ] Create TodoWrite task list for the changes
- [ ] Break down complex changes into smaller steps
- [ ] Identify potential breaking changes or dependencies
- [ ] Plan rollback strategy if needed

---

## 🛠️ **Development Process**

### **Step 1: Local Development**
```bash
# Work on local machine first
cd "/Users/rafaellang/Library/Mobile Documents/com~apple~CloudDocs/Proyectos/cotizador_v1/fastapi-auth-example"

# Make all necessary changes locally
# Test changes locally if possible
```

### **Step 2: Code Review & Validation**
- [ ] Review all changes for consistency
- [ ] Ensure proper error handling
- [ ] Verify database model compatibility
- [ ] Check for security implications
- [ ] Validate business logic

### **Step 3: Git Workflow**
```bash
# Stage changes
git add [specific_files]

# Commit with descriptive message
git commit -m "Description of changes

- Specific change 1
- Specific change 2
- Any breaking changes noted

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub
git push origin main
```

### **Step 4: Deployment to DigitalOcean**
```bash
# SSH to droplet
ssh root@159.65.174.94

# Navigate to app directory
cd /home/ventanas/app

# Pull latest changes
git pull origin main

# Stop current services
docker-compose -f docker-compose.beta.yml stop app

# Remove old image if needed
docker rmi app-app  # Only if significant changes

# Rebuild and start
docker-compose -f docker-compose.beta.yml up -d --build app

# Wait for startup
sleep 15

# Verify deployment
curl http://localhost:8000/health
```

### **Step 5: Post-Deployment Verification**
```bash
# Check container status
docker-compose -f docker-compose.beta.yml ps

# Check logs for errors
docker-compose -f docker-compose.beta.yml logs app --tail=20

# Test key functionality
curl -I http://localhost:8000/
```

---

## 🗄️ **Database Changes Protocol**

### **For Schema Changes:**
1. **NEVER** directly modify database on droplet
2. Update SQLAlchemy models locally first
3. Test model changes thoroughly
4. Consider migration scripts for production
5. Document all schema changes

### **For Sample Data Updates:**
1. Update `initialize_sample_data()` function
2. Test data initialization locally if possible
3. On droplet, may need to:
   ```bash
   # Clear existing data if needed (CAUTION!)
   docker-compose -f docker-compose.beta.yml exec postgres psql -U ventanas_user -d ventanas_beta_db -c "TRUNCATE TABLE app_materials, app_products CASCADE;"
   
   # Re-initialize data
   docker-compose -f docker-compose.beta.yml exec app python -c "
   from database import get_db
   from services.product_bom_service_db import initialize_sample_data
   db = next(get_db())
   initialize_sample_data(db)
   db.close()
   "
   ```

---

## 🚨 **Emergency Procedures**

### **Rollback Process:**
```bash
# If deployment fails, quick rollback
git log --oneline -n 5  # Find previous working commit
git reset --hard [previous_commit_hash]
git push --force origin main

# On droplet
cd /home/ventanas/app
git pull origin main
docker-compose -f docker-compose.beta.yml restart app
```

### **Service Recovery:**
```bash
# If services are down
docker-compose -f docker-compose.beta.yml down
docker-compose -f docker-compose.beta.yml up -d

# Check what's wrong
docker-compose -f docker-compose.beta.yml logs app --tail=50
```

---

## 📁 **File Organization Standards**

### **Key Files to Always Check:**
- `main.py` - Main application file
- `database.py` - Database models and services
- `config.py` - Configuration settings
- `services/product_bom_service_db.py` - Sample data initialization
- `models/` - Pydantic models
- `docker-compose.beta.yml` - Production configuration
- `.env` - Environment variables (server only)

### **Documentation Updates:**
- Update `CLAUDE.md` for significant changes
- Update `PROJECT_STRUCTURE.md` if needed
- Document API changes in comments

---

## 🔧 **Common Tasks Quick Reference**

### **Add New Model:**
1. Update `database.py` SQLAlchemy model
2. Update corresponding Pydantic model in `models/`
3. Update database services if needed
4. Update sample data initialization
5. Test, commit, deploy

### **Add New Endpoint:**
1. Add route to `main.py`
2. Add corresponding template if needed
3. Update frontend JavaScript if needed
4. Test functionality locally
5. Commit and deploy

### **Fix Startup Issues:**
1. Check logs: `docker-compose -f docker-compose.beta.yml logs app --tail=30`
2. Common issues:
   - Missing environment variables
   - Database connection problems
   - Import errors
   - Permission issues with logs/static directories

### **Update Sample Data:**
1. Modify `initialize_sample_data()` function
2. Consider data dependencies and relationships
3. Test initialization logic
4. Deploy and re-initialize if needed

---

## 🎯 **Best Practices**

### **Code Quality:**
- Always use type hints
- Add docstrings for complex functions
- Handle errors gracefully
- Follow existing code patterns
- Use descriptive variable names

### **Database:**
- Use transactions for related operations
- Always validate data before insertion
- Consider foreign key relationships
- Index important query fields

### **Security:**
- Validate all user inputs
- Use parameterized queries
- Check permissions on file operations
- Never log sensitive information

### **Performance:**
- Optimize database queries
- Use appropriate indexes
- Monitor memory usage on 2GB droplet
- Consider caching for frequently accessed data

---

## 📝 **Change Log Template**

When making significant changes, document them:

```markdown
## Change: [Brief Description]
**Date:** [YYYY-MM-DD]
**Files Modified:** [list of files]

### What Changed:
- [ ] Change 1
- [ ] Change 2

### Testing Performed:
- [ ] Test 1
- [ ] Test 2

### Deployment Notes:
- Any special deployment steps
- Environment variables added/changed
- Database migrations needed

### Rollback Plan:
- How to undo changes if needed
```

---

## 🚀 **Current System Status**

**Environment:** Production Beta on DigitalOcean  
**URL:** http://159.65.174.94:8000  
**Database:** PostgreSQL with initialized sample data  
**Status:** ✅ Operational (PDF generation temporarily disabled)  

**Last Major Update:** Fixed PDF imports and permissions issues  
**Next Planned:** Enhanced sample data with categories and colors  

---

*This protocol ensures consistent, safe, and trackable development practices for the Window Quotation System.*