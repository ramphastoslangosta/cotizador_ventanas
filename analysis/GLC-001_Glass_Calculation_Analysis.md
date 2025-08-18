# GLC-001: Glass Calculation BOM Integration Analysis

**Task ID:** GLC-001  
**Sprint:** Week 34  
**Priority:** High  
**Analysis Date:** August 18, 2025  
**Epic:** Glass-Logic-Fix  

---

## 🎯 **Problem Statement**

Current quote generation uses legacy glass calculation functions instead of registered glass materials in the BOM (Bill of Materials) system. This creates inconsistencies between material catalog and actual pricing calculations.

## 📋 **Current State Analysis**

### **Legacy Glass Calculation Logic**

**Location:** `services/product_bom_service_db.py:160-174`

```python
def get_glass_cost_per_m2(self, glass_type: GlassType) -> Decimal:
    """Obtiene el costo por m2 de un tipo de vidrio."""
    _GLASS_CATALOG = [
        Glass(id=1, name="Vidrio Claro 4mm", glass_type=GlassType.CLARO_4MM, cost_per_m2=Decimal('85.00'), thickness=4),
        Glass(id=2, name="Vidrio Claro 6mm", glass_type=GlassType.CLARO_6MM, cost_per_m2=Decimal('120.00'), thickness=6),
        # ... 7 hardcoded glass types
    ]
```

**Issues with Current Approach:**
1. **Hardcoded data**: Glass prices are embedded in code, not database
2. **Limited types**: Only 7 glass types vs. 5 available in BOM system
3. **Inconsistent pricing**: BOM glass materials have different prices than legacy catalog
4. **No formula evaluation**: Glass calculation is simple area × price, no BOM formulas
5. **Separate calculation path**: Glass bypasses BOM system entirely

### **BOM Glass Materials System**

**Location:** `services/product_bom_service_db.py:311-326`

BOM system includes properly registered glass materials:
- Vidrio Flotado 6mm: $145.00/m² (vs $120.00 legacy)
- Vidrio Templado 6mm: $280.00/m² (vs $195.00 legacy)
- Vidrio Laminado 6mm: $320.00/m² (vs $220.00 legacy)
- Vidrio Reflectivo Bronze 6mm: $195.00/m² (vs $180.00 legacy)
- Vidrio Doble Acristalamiento: $450.00/m² (not in legacy)

### **Current Quote Calculation Flow**

**Location:** `main.py:613-617`

```python
# Current glass calculation (LEGACY PATH)
glass_cost_per_m2 = product_bom_service.get_glass_cost_per_m2(item.selected_glass_type)
glass_waste_factor = Decimal('1.05') 
total_glass_cost = area_m2 * glass_cost_per_m2 * glass_waste_factor * item.quantity
```

**Problems:**
1. **Bypasses BOM**: Glass is calculated separately from BOM materials
2. **Fixed waste factor**: 1.05 hardcoded vs. dynamic BOM waste factors
3. **No formula flexibility**: Cannot use complex formulas like "area_m2 * 0.5" for split windows
4. **Type mismatch**: Uses `GlassType` enum instead of BOM material IDs

---

## 🔄 **Data Flow Analysis**

### **Current Data Flow (PROBLEMATIC)**
```
Quote Request → WindowItem.selected_glass_type (GlassType enum)
             → get_glass_cost_per_m2(glass_type)
             → _GLASS_CATALOG lookup (hardcoded)
             → area_m2 × price × 1.05 × quantity
```

### **BOM Data Flow (DESIRED)**
```
Quote Request → WindowItem.selected_glass_type (should map to material_id)
             → Product BOM → glass BOMItem with material_id
             → evaluate_formula(quantity_formula, formula_vars)
             → apply waste_factor from BOM
             → material.cost_per_unit from database
```

---

## 📊 **Pricing Comparison Analysis**

| Glass Type | Legacy Price | BOM Price | Difference | Impact |
|------------|--------------|-----------|------------|---------|
| Claro 6mm | $120.00 | $145.00 | +$25.00 | +20.8% |
| Templado 6mm | $195.00 | $280.00 | +$85.00 | +43.6% |
| Laminado 6mm | $220.00 | $320.00 | +$100.00 | +45.5% |
| Reflectivo 6mm | $180.00 | $195.00 | +$15.00 | +8.3% |

**Critical Finding:** Legacy system significantly underprices glass, potentially causing **20-45% revenue loss** on glass components.

---

## 🏗️ **BOM Integration Analysis**

### **Existing BOM Glass Examples**

1. **Ventana Corrediza (50% glass coverage):**
```python
BOMItem(
    material_id=created_glass["Vidrio Flotado 6mm"].id, 
    material_type=MaterialType.VIDRIO, 
    quantity_formula="area_m2 * 0.5", 
    description="Vidrio por paño (50% del área total)"
)
```

2. **Ventana Fija (100% glass coverage):**
```python
BOMItem(
    material_id=created_glass["Vidrio Templado 6mm"].id, 
    material_type=MaterialType.VIDRIO, 
    quantity_formula="area_m2", 
    description="Vidrio templado completo"
)
```

### **BOM Formula Capabilities**

The BOM system supports dynamic formulas that legacy system cannot:
- **Split coverage**: `"area_m2 * 0.5"` for windows with frames
- **Complex geometry**: Could support `"(width_m - 0.1) * (height_m - 0.1)"` for frame deductions
- **Quantity adjustments**: `"math.ceil(area_m2 / 2.5)"` for sheet optimization
- **Waste factors**: Individual waste factors per glass type (not hardcoded 1.05)

---

## 🔧 **Technical Integration Requirements**

### **1. UI/UX Changes Required**

**Current Interface Issue:**
- Users select from `GlassType` enum (CLARO_4MM, TEMPLADO_6MM, etc.)
- System needs to map these to actual BOM material IDs

**Solution Options:**
1. **Map enum to material**: Create mapping function `glass_type_to_material_id()`
2. **Change UI to material selection**: Replace enum with actual glass materials from BOM
3. **Hybrid approach**: Keep enum for UX, map to BOM materials internally

### **2. Product BOM Schema Validation**

Each product must have exactly one glass BOMItem:
- **Validation**: Products without glass BOMItem should error gracefully
- **Default glass**: Consider default glass types for products missing glass BOMs
- **Multiple glass**: Handle products with multiple glass types (e.g., different panes)

### **3. Backwards Compatibility**

**Existing Quotes:** 
- Quotes already created with legacy system must remain valid
- Consider migration strategy for re-calculating existing quotes

**API Compatibility:**
- `/quotes/calculate` endpoint expects `selected_glass_type` as enum
- May need to maintain enum support while adding BOM integration

---

## ⚡ **Performance Implications**

### **Current Performance**
- **Legacy**: O(1) lookup in hardcoded array (7 items)
- **Memory**: Minimal, hardcoded data

### **BOM System Performance**
- **Database lookup**: Material query by ID (indexed, fast)
- **Formula evaluation**: `SafeFormulaEvaluator` overhead (minimal)
- **Memory**: Slightly higher due to database objects

**Assessment**: Performance impact negligible, database queries are well-indexed.

---

## 🗃️ **Database Impact Analysis**

### **No Schema Changes Required**
✅ All necessary tables and columns already exist:
- `app_materials` with `category='Vidrio'`
- `app_products` with BOM formulas in JSONB
- BOM items with `material_type='VIDRIO'`

### **Sample Data Compatibility**
✅ Sample data already includes comprehensive glass materials:
- 5 glass types properly categorized
- Realistic pricing based on market rates
- Proper BOM integration in sample products

---

## 🧪 **Testing Requirements**

### **Unit Tests Needed**
1. **Glass BOM lookup**: Test material resolution from glass type
2. **Formula evaluation**: Test glass quantity formulas
3. **Price calculation**: Verify BOM vs legacy price accuracy
4. **Waste factor application**: Test dynamic waste factors

### **Integration Tests Needed**
1. **Quote calculation**: End-to-end quote with BOM glass
2. **UI integration**: Glass selection and calculation flow
3. **API compatibility**: Ensure existing endpoints work

### **Regression Tests Needed**
1. **Existing quotes**: Verify no breaking changes
2. **Performance**: Compare calculation speeds
3. **Price accuracy**: Validate all glass types calculate correctly

---

## 📋 **Implementation Roadmap**

### **Phase 1: Analysis Completion (Current)**
- [x] Map current glass calculation logic
- [x] Identify BOM glass material structure  
- [x] Document integration requirements
- [x] Assess performance and compatibility impact

### **Phase 2: Backend Integration (Next Sprint)**
**Estimated Effort:** 5 story points
1. **Create glass type mapping function**
2. **Modify `calculate_window_item_from_bom()` to handle glass BOMs**
3. **Update `ProductBOMServiceDB` to remove legacy glass method**
4. **Add validation for products missing glass BOMs**

### **Phase 3: Frontend Updates (Next Sprint)**
**Estimated Effort:** 3 story points  
1. **Update glass selection UI to use BOM materials**
2. **Maintain enum compatibility for existing API**
3. **Update quote display to show BOM-calculated glass costs**

### **Phase 4: Testing & Validation (Next Sprint)**
**Estimated Effort:** 2 story points
1. **Comprehensive testing suite**
2. **Price validation against legacy system**
3. **Performance benchmarking**

---

## 🚨 **Risk Assessment**

### **High Risk Items**

**Risk 1: Price Increase Impact**
- **Impact:** 20-45% glass price increases may shock users
- **Mitigation:** Gradual rollout, clear communication about accurate pricing
- **Probability:** High

**Risk 2: Formula Complexity**
- **Impact:** Complex glass formulas may be harder to debug than simple calculation
- **Mitigation:** Comprehensive logging, formula validation tools
- **Probability:** Medium

**Risk 3: API Breaking Changes**
- **Impact:** Frontend may break if glass selection changes
- **Mitigation:** Maintain backwards compatibility, phased migration
- **Probability:** Low

### **Medium Risk Items**

**Risk 4: Data Migration**
- **Impact:** Existing quotes may need recalculation
- **Mitigation:** Keep legacy calculation available for historical quotes
- **Probability:** Medium

**Risk 5: Performance Degradation**
- **Impact:** BOM calculation slower than hardcoded lookup
- **Mitigation:** Database optimization, caching strategies
- **Probability:** Low

---

## 💡 **Recommendations**

### **Immediate Actions (Sprint Week 34)**
1. **Complete this analysis** ✅
2. **Validate sample data pricing** with business stakeholders
3. **Design glass type mapping strategy**
4. **Plan UI/UX changes for glass selection**

### **Next Sprint Priority Actions**
1. **Implement BOM glass integration** in backend
2. **Create migration strategy** for existing quotes
3. **Update frontend** to use BOM glass materials
4. **Comprehensive testing** of price accuracy

### **Business Decision Required**
**Glass Pricing Strategy:**
- Accept 20-45% price increases for accuracy?
- Gradual price adjustment over time?
- Maintain legacy prices with BOM formulas?

---

## 📈 **Success Criteria**

### **Technical Success**
- [ ] Glass calculations use BOM materials instead of hardcoded catalog
- [ ] Formula evaluation works correctly for all glass types
- [ ] Performance remains acceptable (< 100ms per quote)
- [ ] No breaking changes to existing API endpoints

### **Business Success**
- [ ] Accurate glass pricing reflects actual material costs
- [ ] Formula flexibility enables complex window configurations
- [ ] Easy maintenance through database instead of code changes
- [ ] Consistent pricing methodology across all material types

### **User Experience Success**
- [ ] Glass selection remains intuitive and user-friendly
- [ ] Quote calculations complete without errors
- [ ] Price changes are clearly communicated and justified
- [ ] Historical quotes remain accessible and valid

---

## 📂 **Next Steps**

1. **Review analysis with stakeholders** to validate findings
2. **Get business approval** for pricing strategy
3. **Create implementation plan** for Sprint Week 35
4. **Begin technical implementation** following this analysis

---

**Analysis Status:** ✅ **COMPLETE**  
**Next Phase:** Implementation Planning  
**Business Impact:** HIGH - Revenue accuracy improvement  
**Technical Complexity:** MEDIUM - Well-defined integration path  

*This analysis provides the foundation for implementing accurate, flexible glass calculation using the existing BOM infrastructure.*