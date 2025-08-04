# Sample Data Enhancement Plan
**Window Quotation System - Comprehensive Material Catalog**

Following Development Protocol established in `DEVELOPMENT_PROTOCOL.md`

---

## 🎯 **Project Objective**

Enhance the current sample data initialization to include:
- ✅ Proper material categorization (Perfiles, Vidrio, Herrajes, Consumibles)
- ✅ Complete color system for aluminum profiles
- ✅ Glass material options with specifications
- ✅ Material-color pricing relationships
- ✅ Enhanced product codes and descriptions

---

## 📋 **Pre-Development Analysis Complete**

### **Current State:**
- Basic materials without proper categories (all default to "Otros")
- No color system implemented
- Missing glass materials
- No material-color pricing variations
- Basic product codes and descriptions

### **Target State:**
- 4 distinct material categories with proper classification
- 6+ standard aluminum colors with pricing variations
- 5+ glass types with specifications
- 20+ material-color combinations
- Professional product codes and detailed descriptions

---

## 🗂️ **Detailed Implementation Plan**

### **Phase 1: Database Schema Validation** ⏱️ 15 minutes
**Files to Review:**
- [ ] `database.py` - Confirm Color and MaterialColor models
- [ ] `models/product_bom_models.py` - Verify MaterialType enum
- [ ] `services/product_bom_service_db.py` - Check existing service methods

**Tasks:**
1. [ ] Verify Color table structure and relationships
2. [ ] Confirm MaterialColor junction table functionality
3. [ ] Check if DatabaseColorService exists and is functional
4. [ ] Review MaterialType enum values

### **Phase 2: Enhanced Sample Data Design** ⏱️ 30 minutes
**File to Modify:** `services/product_bom_service_db.py`

#### **2.1 Material Categories Structure:**
```python
MATERIAL_CATEGORIES = {
    "Perfiles": [
        # Línea Nacional 3"
        {"name": "Perfil Riel Superior 3\"", "code": "PER-NAC3-RS", "cost": 52.00},
        {"name": "Perfil Jamba 3\"", "code": "PER-NAC3-JA", "cost": 48.00},
        {"name": "Perfil Zócalo 3\"", "code": "PER-NAC3-ZO", "cost": 55.00},
        {"name": "Perfil Traslape 3\"", "code": "PER-NAC3-TR", "cost": 60.00},
        # Serie 35
        {"name": "Perfil Contramarco Serie 35", "code": "PER-S35-CM", "cost": 65.00},
        {"name": "Perfil Marco Móvil Serie 35", "code": "PER-S35-MM", "cost": 70.00},
        # Fijos
        {"name": "Perfil Fijo Escalonado 3\"", "code": "PER-NAC3-FE", "cost": 78.90},
        {"name": "Junquillo Fijo 3\"", "code": "PER-NAC3-JF", "cost": 28.90},
    ],
    "Vidrio": [
        {"name": "Vidrio Flotado 6mm", "code": "VID-FLOT-6", "cost": 145.00, "unit": "M2"},
        {"name": "Vidrio Templado 6mm", "code": "VID-TEMP-6", "cost": 280.00, "unit": "M2"},
        {"name": "Vidrio Laminado 6mm", "code": "VID-LAM-6", "cost": 320.00, "unit": "M2"},
        {"name": "Vidrio Reflectivo Bronze 6mm", "code": "VID-REF-BR6", "cost": 195.00, "unit": "M2"},
        {"name": "Vidrio Doble Acristalamiento", "code": "VID-DOBLE-6", "cost": 450.00, "unit": "M2"},
    ],
    "Herrajes": [
        {"name": "Rodamiento Doble Línea 3\"", "code": "HER-ROD-3", "cost": 15.00},
        {"name": "Brazo Proyectante 10\"", "code": "HER-BRA-10", "cost": 70.00},
        {"name": "Cremona Serie 35", "code": "HER-CRE-S35", "cost": 45.00},
        {"name": "Cerradura Multipunto", "code": "HER-CER-MP", "cost": 150.00},
        {"name": "Bisagra Reforzada", "code": "HER-BIS-REF", "cost": 25.00},
    ],
    "Consumibles": [
        {"name": "Felpa Negra 1/2\"", "code": "CON-FEL-NEG", "cost": 2.50},
        {"name": "Silicona Neutra Transparente", "code": "CON-SIL-NEU", "cost": 80.00},
        {"name": "Pijas #8 x 1\"", "code": "CON-PIJ-8x1", "cost": 0.50},
        {"name": "Cuñas de Hule", "code": "CON-CUN-HUL", "cost": 0.80},
        {"name": "Tornillo Autoperforante", "code": "CON-TOR-AUTO", "cost": 1.20},
    ]
}
```

#### **2.2 Color System Design:**
```python
ALUMINUM_COLORS = [
    {"name": "Natural", "code": "NAT", "description": "Aluminio natural sin pintura"},
    {"name": "Blanco", "code": "BLA", "description": "Blanco texturizado"},
    {"name": "Negro", "code": "NEG", "description": "Negro mate texturizado"},
    {"name": "Bronze", "code": "BRO", "description": "Bronze anodizado"},
    {"name": "Champagne", "code": "CHA", "description": "Champagne anodizado"},
    {"name": "Madera Clara", "code": "MCA", "description": "Imitación madera color claro"},
]

# Color pricing multipliers
COLOR_PRICING = {
    "Natural": 1.00,    # Base price
    "Blanco": 1.15,     # 15% premium
    "Negro": 1.20,      # 20% premium  
    "Bronze": 1.25,     # 25% premium
    "Champagne": 1.25,  # 25% premium
    "Madera Clara": 1.40, # 40% premium
}
```

### **Phase 3: Service Layer Enhancement** ⏱️ 20 minutes
**Files to Modify:**
- [ ] `database.py` - Add/verify DatabaseColorService
- [ ] `services/product_bom_service_db.py` - Update initialization function

**Tasks:**
1. [ ] Implement color initialization in `initialize_sample_data()`
2. [ ] Create material-color relationships for profiles
3. [ ] Add glass materials with proper MaterialType.VIDRIO
4. [ ] Update existing materials with proper categories

### **Phase 4: Enhanced Product Definitions** ⏱️ 25 minutes
**Update BOM formulas to include:**
- [ ] Glass area calculations: `area_m2` for glass materials
- [ ] Color-aware profile specifications
- [ ] Comprehensive material descriptions
- [ ] Waste factors by material type

#### **4.1 Enhanced BOM Example:**
```python
# Ventana Corrediza with Glass
corrediza_bom = [
    # Profiles (will have color variations)
    BOMItem(material_id=profiles["riel_superior"], material_type=MaterialType.PERFIL, 
            quantity_formula="width_m", description="Riel Superior"),
    # Glass (separate material)
    BOMItem(material_id=glass["flotado_6mm"], material_type=MaterialType.VIDRIO,
            quantity_formula="area_m2 * 0.5", description="Vidrio por paño (50% del área total)"),
    # Hardware
    BOMItem(material_id=hardware["rodamientos"], material_type=MaterialType.HERRAJE,
            quantity_formula="4", description="Rodamientos (4 por ventana)"),
    # Consumables  
    BOMItem(material_id=consumables["felpa"], material_type=MaterialType.CONSUMIBLE,
            quantity_formula="4 * (width_m / 2 + height_m)", description="Felpa perimetral"),
]
```

### **Phase 5: Testing & Validation** ⏱️ 20 minutes
**Local Testing Tasks:**
1. [ ] Create test script to validate data initialization
2. [ ] Check all foreign key relationships
3. [ ] Verify color-material associations
4. [ ] Test material categorization
5. [ ] Validate enhanced product codes

### **Phase 6: Deployment Following Protocol** ⏱️ 15 minutes
**Following DEVELOPMENT_PROTOCOL.md:**
1. [ ] Git commit with descriptive message
2. [ ] Push to GitHub
3. [ ] SSH to DigitalOcean droplet
4. [ ] Pull latest changes
5. [ ] Clear existing sample data (if needed)
6. [ ] Re-initialize with enhanced data
7. [ ] Verify deployment

---

## 📁 **Files That Will Be Modified**

### **Primary Files:**
- `services/product_bom_service_db.py` - Main sample data logic
- `database.py` - Verify/add color services (if needed)

### **Files to Review (No changes expected):**
- `models/product_bom_models.py` - Confirm MaterialType enum
- `database.py` - Color and MaterialColor models
- `main.py` - Color-related endpoints (future)

---

## 🧪 **Testing Strategy**

### **Data Integrity Tests:**
```python
# Test script to run after initialization
def test_sample_data():
    # Check material categories
    assert materials_with_category("Perfiles").count() >= 8
    assert materials_with_category("Vidrio").count() >= 5
    assert materials_with_category("Herrajes").count() >= 5
    assert materials_with_category("Consumibles").count() >= 5
    
    # Check color system
    assert Color.query.count() >= 6
    assert MaterialColor.query.count() >= 30  # 6 colors × 5+ profiles
    
    # Check glass materials exist
    assert materials_with_type(MaterialType.VIDRIO).count() >= 5
```

### **Business Logic Tests:**
- [ ] Verify color pricing multipliers apply correctly
- [ ] Test glass area calculations in BOMs
- [ ] Validate material-color combinations
- [ ] Check product code uniqueness

---

## 🚀 **Deployment Checklist**

### **Pre-Deployment:**
- [ ] All local tests pass
- [ ] Code review completed
- [ ] Git commit with proper message format
- [ ] GitHub push successful

### **Deployment Steps:**
```bash
# Following DEVELOPMENT_PROTOCOL.md
ssh root@159.65.174.94
cd /home/ventanas/app
git pull origin main

# Clear existing sample data (CAUTION!)
docker-compose -f docker-compose.beta.yml exec postgres psql -U ventanas_user -d ventanas_beta_db -c "
DELETE FROM material_colors;
DELETE FROM app_materials; 
DELETE FROM app_products;
DELETE FROM colors;
"

# Re-initialize with enhanced data
docker-compose -f docker-compose.beta.yml exec app python -c "
from database import get_db
from services.product_bom_service_db import initialize_sample_data
db = next(get_db())
initialize_sample_data(db)
db.close()
print('Enhanced sample data initialized!')
"
```

### **Post-Deployment Verification:**
- [ ] Check material categories: 4 distinct categories populated
- [ ] Verify color system: 6+ colors with pricing variations
- [ ] Confirm glass materials: 5+ glass types available
- [ ] Test material-color relationships: 30+ combinations
- [ ] Validate product codes: Professional format implemented

---

## 📊 **Expected Outcomes**

### **Material Catalog:**
- **Perfiles:** 8+ aluminum profiles with 6 color options each (48+ combinations)
- **Vidrio:** 5+ glass types with specifications and proper pricing
- **Herrajes:** 5+ hardware components with detailed descriptions
- **Consumibles:** 5+ consumable materials with accurate costs

### **Color System:**
- 6 standard aluminum colors with pricing multipliers
- 30+ material-color combinations for profiles
- Color selection integrated into quotation process

### **Enhanced User Experience:**
- Professional product codes (PER-NAC3-RS, VID-FLOT-6, etc.)
- Detailed material descriptions
- Accurate pricing with color premiums
- Complete glass specifications

---

## ⏰ **Estimated Timeline**

**Total Time:** ~2 hours 5 minutes

- **Phase 1:** Schema Validation (15 min)
- **Phase 2:** Data Design (30 min)  
- **Phase 3:** Service Enhancement (20 min)
- **Phase 4:** Product Updates (25 min)
- **Phase 5:** Testing (20 min)
- **Phase 6:** Deployment (15 min)

---

## 🎯 **Success Criteria**

✅ **Functional Requirements:**
- All materials properly categorized (Perfiles, Vidrio, Herrajes, Consumibles)
- Color system operational with pricing variations
- Glass materials integrated with area-based calculations
- Enhanced product codes and descriptions implemented

✅ **Technical Requirements:**
- Database relationships maintained
- No breaking changes to existing functionality
- Sample data initialization completes without errors
- All foreign key constraints satisfied

✅ **Business Requirements:**
- Realistic pricing structure with color premiums
- Professional material catalog for user testing
- Complete quotation workflow with material/color selection
- Production-ready data structure for beta users

---

**Next Session Action:** Execute this plan following the established Development Protocol, starting with Phase 1: Database Schema Validation.

---

*This plan follows the established Development Protocol and ensures safe, systematic implementation of enhanced sample data.*