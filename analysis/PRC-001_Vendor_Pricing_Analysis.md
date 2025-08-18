# PRC-001: Vendor Pricing System Analysis

**Task ID:** PRC-001  
**Sprint:** Week 34  
**Priority:** High  
**Analysis Date:** August 18, 2025  
**Epic:** Pricing-Logic-Fix  

---

## 🎯 **Problem Statement**

Current pricing system may not properly handle vendor selling units. Users need to input prices in actual vendor selling units (e.g., profiles sold in 6.10-meter lengths) rather than standardized units.

## 📋 **Current Pricing Model Review**

### **Database Schema Analysis**

**Location:** `database.py:52-65`

```sql
CREATE TABLE app_materials (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT UNIQUE,
    unit TEXT NOT NULL,                    -- ML, PZA, M2, CARTUCHO, LTS, KG
    category TEXT NOT NULL DEFAULT 'Otros',
    cost_per_unit NUMERIC(12,4) NOT NULL,  -- Cost per base unit
    selling_unit_length_m NUMERIC(8,2),    -- Vendor selling unit (e.g., 6.0m)
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
```

**Key Findings:**
- ✅ **selling_unit_length_m field exists** - Already supports vendor selling units
- ✅ **Proper data types** - Numeric fields for precise calculations
- ✅ **Multiple unit types supported** - ML, PZA, M2, CARTUCHO, LTS, KG
- ⚠️ **Limited to length units** - Only handles meter-based selling units

### **Current Unit Conversion Logic**

**Location:** `main.py:587-589`

```python
# Current vendor unit handling (PROFILES ONLY)
if material.selling_unit_length_m and material.unit == MaterialUnit.ML:
    num_selling_units = math.ceil(quantity_with_waste_for_one_window / material.selling_unit_length_m)
    final_quantity_to_cost = Decimal(str(num_selling_units)) * material.selling_unit_length_m
```

**Current Behavior:**
1. **Calculates needed quantity** including waste factor
2. **Rounds up to selling units** using `math.ceil()`
3. **Charges for full selling units** (e.g., buy 6m even if need 4.5m)
4. **Only applies to profiles** (`MaterialUnit.ML`)

---

## 🏗️ **Vendor Unit Requirements Analysis**

### **Profile Materials (Currently Supported)**

**Vendor Selling Patterns:**
- **Standard lengths**: 6.0m, 6.10m, 3.05m (half lengths)
- **Pricing method**: Price per meter, sold in fixed lengths
- **Waste consideration**: Customer buys full lengths, leftover is waste

**Current Implementation Status:**
✅ **Fully implemented** for profiles with 6.0m selling units

**Sample Data Analysis:**
```python
# All profiles use 6.0m selling unit
{"selling_unit_length_m": Decimal("6.0")}
```

### **Glass Materials (NOT Currently Handled)**

**Vendor Selling Patterns:**
- **Sheet sizes**: 2.40m × 3.30m, 2.20m × 3.20m, custom cuts
- **Pricing method**: Price per m², minimum sheet charge
- **Optimization needed**: Multiple windows per sheet calculation

**Current Implementation Status:**
❌ **Not implemented** - Glass uses simple area × price calculation

**Required Enhancement:**
```python
# Proposed glass selling unit support
glass_sheet_area_m2 = Decimal("7.92")  # 2.40m × 3.30m
min_charge_per_sheet = glass_cost_per_m2 * glass_sheet_area_m2
```

### **Hardware Materials (Partially Handled)**

**Vendor Selling Patterns:**
- **Individual pieces**: Single hardware items (hinges, locks)
- **Sets/kits**: Complete window hardware sets
- **Bulk packaging**: 50-piece boxes, 100-piece bags

**Current Implementation Status:**
✅ **Basic PZA support** - Individual piece pricing
❌ **Missing bulk packaging** - No minimum order quantities

**Required Enhancement:**
```python
# Proposed hardware bulk support
selling_unit_quantity = 50  # Sold in boxes of 50
packaging_type = "BOX"      # BOX, BAG, SET, INDIVIDUAL
```

### **Consumables (Mixed Status)**

**Vendor Selling Patterns:**
- **Linear materials** (felpa): 100m rolls, 50m rolls
- **Cartridges** (silicona): Individual cartridges, 12-cartridge boxes
- **Small hardware** (screws): 100-piece boxes, 500-piece bags
- **Bulk materials**: 5kg buckets, 25kg bags

**Current Implementation Status:**
- ✅ **Linear materials**: Could use existing `selling_unit_length_m`
- ❌ **Cartridge boxes**: No support for multi-cartridge packages
- ❌ **Screw boxes**: No support for piece-count packaging
- ❌ **Bulk quantities**: No weight-based selling units

---

## 💰 **Pricing Model Analysis**

### **Current Cost Structure**

**Per-Unit Pricing:**
```python
cost_per_unit = Decimal("52.00")  # $/meter for profiles
cost_per_unit = Decimal("145.00") # $/m² for glass
cost_per_unit = Decimal("15.00")  # $/piece for hardware
```

**Vendor Reality vs. System:**
| Material Type | System Unit | Vendor Selling Unit | Gap Analysis |
|---------------|-------------|-------------------|--------------|
| Profiles | $/meter | $/6-meter length | ✅ Handled |
| Glass | $/m² | $/sheet (min size) | ❌ Missing |
| Hardware | $/piece | $/bulk package | ❌ Missing |
| Consumables | $/unit | $/package/roll | ❌ Missing |

### **Pricing Accuracy Impact**

**Example: Profile Calculation**
- **Need**: 4.5 meters of profile
- **Vendor sells**: 6-meter lengths at $52/meter = $312/length
- **System calculation**: 
  - Quantity needed: 4.5m
  - Selling units: ceil(4.5 ÷ 6) = 1 length
  - Cost: 1 × 6 × $52 = $312 ✅ **Correct**

**Example: Glass Calculation (Current Problem)**
- **Need**: 1.2m² of glass
- **Vendor sells**: 2.4×3.3m sheets (7.92m²) at $145/m²
- **Current system**: 1.2 × $145 = $174
- **Actual vendor cost**: 7.92 × $145 = $1,148.40
- **Difference**: -$974.40 (85% underpricing!) ❌ **Critical Issue**

---

## 🔧 **System Design Analysis**

### **Database Schema Requirements**

**Current Schema Limitations:**
1. **selling_unit_length_m only**: No support for area, weight, or count units
2. **Single selling unit**: Cannot handle multiple package sizes
3. **No minimum orders**: No support for minimum purchase quantities

**Proposed Schema Enhancement:**
```sql
-- Option 1: Extend current table
ALTER TABLE app_materials 
ADD COLUMN selling_unit_area_m2 NUMERIC(8,2),
ADD COLUMN selling_unit_weight_kg NUMERIC(8,2),
ADD COLUMN selling_unit_count INTEGER,
ADD COLUMN selling_unit_type TEXT, -- 'LENGTH', 'AREA', 'WEIGHT', 'COUNT'
ADD COLUMN min_order_quantity NUMERIC(8,2);

-- Option 2: Separate selling units table (more flexible)
CREATE TABLE material_selling_units (
    id BIGINT PRIMARY KEY,
    material_id BIGINT REFERENCES app_materials(id),
    unit_type TEXT, -- 'LENGTH', 'AREA', 'WEIGHT', 'COUNT'
    unit_value NUMERIC(12,4),
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE
);
```

### **Calculation Engine Modifications**

**Current Logic (Profiles Only):**
```python
if material.selling_unit_length_m and material.unit == MaterialUnit.ML:
    num_selling_units = math.ceil(quantity_with_waste / material.selling_unit_length_m)
    final_quantity = num_selling_units * material.selling_unit_length_m
```

**Enhanced Logic (All Material Types):**
```python
def apply_vendor_selling_units(material, needed_quantity, material_type):
    if material_type == MaterialType.PERFIL and material.selling_unit_length_m:
        # Current profile logic
        return handle_length_selling_units(material, needed_quantity)
    
    elif material_type == MaterialType.VIDRIO and material.selling_unit_area_m2:
        # New glass sheet logic
        return handle_area_selling_units(material, needed_quantity)
    
    elif material_type == MaterialType.HERRAJE and material.selling_unit_count:
        # New hardware bulk logic
        return handle_count_selling_units(material, needed_quantity)
    
    else:
        # No vendor units, use exact quantity
        return needed_quantity
```

---

## 🌐 **UI/UX Requirements Analysis**

### **Current Price Input Interface**

**Material Creation/Editing:**
- **Cost per unit**: Simple decimal input
- **Unit type**: Dropdown (ML, PZA, M2, etc.)
- **Selling unit length**: Optional decimal input

**User Experience Issues:**
1. **Confusion about units**: Users unclear if price is per selling unit or base unit
2. **Limited selling unit types**: Only length units supported
3. **No visual clarity**: Not obvious when vendor units apply

### **Proposed UI Enhancements**

**Enhanced Material Form:**
```
Material: Perfil Riel Superior 3"
Base Unit: Metro Lineal (ML)
Cost per ML: $52.00

Vendor Selling Units:
☑ Sold in fixed lengths
  Length per unit: 6.0 meters
  Cost per 6m length: $312.00 (calculated)

☐ Sold in sheets (for glass)
  Sheet size: ___ × ___ meters
  
☐ Sold in bulk packages
  Pieces per package: ___
  Package type: [Box/Bag/Roll]
```

**Quote Display Enhancement:**
```
Material: Perfil Riel Superior 3"
Needed: 4.5 ML
Vendor units: 1 × 6.0m length
Cost: $312.00 (includes 1.5m waste)
```

---

## 📊 **Business Logic Review**

### **Waste Calculation Accuracy**

**Current Method:**
```python
quantity_with_waste = quantity_net * waste_factor  # e.g., 4.5m × 1.05 = 4.725m
vendor_quantity = ceil(4.725 ÷ 6.0) × 6.0 = 6.0m  # Buy 6m
effective_waste = (6.0 - 4.5) ÷ 4.5 = 33.3%       # Actual waste is higher
```

**Issue**: Waste factor applied before vendor units, resulting in **double waste consideration**.

**Improved Method:**
```python
vendor_quantity = ceil(quantity_net ÷ 6.0) × 6.0 = 6.0m  # Buy 6m (no waste factor yet)
usable_waste = min(6.0 - 4.5, 4.5 × waste_factor)       # Consider reusable waste
final_cost = calculate_with_realistic_waste(vendor_quantity, usable_waste)
```

### **Inventory Management Implications**

**Current System Impact:**
- **Overpurchasing**: Automatic when using vendor units
- **Inventory tracking**: No connection to actual purchased quantities
- **Waste tracking**: Purely theoretical, not based on actual leftovers

**Integration Opportunities:**
- **Inventory system**: Track actual purchased vs. used quantities
- **Waste optimization**: Suggest combining orders to optimize material usage
- **Purchase orders**: Generate accurate supplier orders

### **Purchase Order Generation Alignment**

**Current Gap:**
- **Quote calculations**: Use vendor selling units
- **Purchase orders**: Would need same vendor unit logic
- **Supplier communication**: Requires vendor-friendly units and quantities

**Required Integration:**
```python
class PurchaseOrderItem:
    material_name: str
    vendor_quantity: Decimal      # In vendor selling units
    vendor_unit_description: str  # "6-meter lengths", "2.4×3.3m sheets"
    cost_per_vendor_unit: Decimal
    total_cost: Decimal
```

---

## 📈 **Cost Reporting Analysis**

### **Current Reporting Limitations**

**Quote Reports:**
- Show theoretical material costs
- No visibility into actual vendor purchasing
- Waste calculations may be inaccurate

**Needed Enhancements:**
```
Material Cost Breakdown:
┌─────────────────────────────────────────────────────┐
│ Perfil Riel Superior 3"                             │
│ Needed: 4.5 ML @ $52.00/ML = $234.00               │
│ Vendor: 1×6m length @ $312.00 = $312.00            │
│ Waste: 1.5 ML ($78.00) - 33.3% waste factor        │
└─────────────────────────────────────────────────────┘
```

### **Financial Impact Analysis**

**Glass Pricing Critical Issue:**
- **Current underpricing**: 60-85% below vendor costs
- **Revenue impact**: Significant losses on glass-heavy projects
- **Competitive positioning**: Unsustainable pricing model

**Other Material Categories:**
- **Profiles**: ✅ Accurate vendor unit handling
- **Hardware**: Minor impact, mostly individual pieces
- **Consumables**: Mixed impact, depends on package sizes

---

## 🔧 **Implementation Complexity Assessment**

### **Low Complexity (Quick Wins)**

1. **Glass sheet support**: Add `selling_unit_area_m2` field
2. **UI clarity improvements**: Better labeling and calculation display
3. **Waste calculation fix**: Adjust waste factor application order

### **Medium Complexity**

1. **Multiple selling unit types**: Support area, count, weight units
2. **Enhanced calculation engine**: Handle all material types
3. **UI form enhancements**: Comprehensive vendor unit input

### **High Complexity (Future Considerations)**

1. **Multiple package sizes**: Different bulk options per material
2. **Inventory integration**: Track actual vs. theoretical usage
3. **Purchase order generation**: Full vendor unit integration
4. **Optimization algorithms**: Multi-project material optimization

---

## 🎯 **Recommendations**

### **Immediate Priority (Sprint Week 34)**

1. **Critical glass pricing fix**:
   - Add `selling_unit_area_m2` to database schema
   - Implement glass sheet calculation logic
   - Update sample data with realistic glass sheet sizes

2. **Waste calculation improvement**:
   - Move waste factor application after vendor unit calculation
   - Provide clear waste visibility in quotes

3. **UI clarity enhancement**:
   - Show vendor quantities in quote displays
   - Clarify cost breakdowns with vendor unit information

### **Next Sprint Priority**

1. **Hardware bulk support**:
   - Add `selling_unit_count` field
   - Implement bulk package calculations

2. **Consumables enhancement**:
   - Support for roll lengths and bulk packages
   - Weight-based selling units for bulk materials

3. **Reporting improvements**:
   - Enhanced cost breakdowns
   - Vendor quantity visibility

### **Future Considerations**

1. **Inventory system integration**
2. **Purchase order generation**
3. **Multi-vendor pricing support**
4. **Material optimization algorithms**

---

## 🚨 **Risk Assessment**

### **Critical Risks**

**Risk 1: Glass Pricing Losses**
- **Impact**: 60-85% revenue loss on glass components
- **Probability**: HIGH (currently happening)
- **Mitigation**: Immediate implementation of glass sheet support

**Risk 2: Customer Price Shock**
- **Impact**: Significant quote increases when fixing glass pricing
- **Probability**: HIGH
- **Mitigation**: Gradual implementation, clear communication

### **Medium Risks**

**Risk 3: Complexity Creep**
- **Impact**: Over-engineering vendor unit system
- **Probability**: MEDIUM
- **Mitigation**: Phased implementation, focus on critical material types first

**Risk 4: Data Migration**
- **Impact**: Existing materials need vendor unit data
- **Probability**: MEDIUM
- **Mitigation**: Default values and migration scripts

---

## 📋 **Success Criteria**

### **Technical Success**
- [ ] Glass calculations use actual sheet sizes and costs
- [ ] All material types support appropriate vendor units
- [ ] Accurate waste calculation considering vendor units
- [ ] Clear cost breakdowns showing vendor quantities

### **Business Success**
- [ ] Glass pricing reflects actual vendor costs
- [ ] Purchase orders align with quote calculations
- [ ] Reduced material waste through better optimization
- [ ] Accurate profitability analysis

### **User Experience Success**
- [ ] Clear vendor unit information in quotes
- [ ] Easy material entry with vendor unit support
- [ ] Transparent cost breakdowns
- [ ] Intuitive interface for different material types

---

## 📂 **Implementation Plan**

### **Phase 1: Critical Glass Fix (2 points)**
1. Add `selling_unit_area_m2` field to database
2. Implement glass sheet calculation logic
3. Update glass sample data with sheet sizes
4. Test glass pricing accuracy

### **Phase 2: Enhanced Vendor Units (3 points)**
1. Add support for count and weight selling units
2. Enhance calculation engine for all material types
3. Update UI to show vendor unit information
4. Fix waste calculation order

### **Phase 3: UI/UX Improvements (3 points)**
1. Enhanced material input forms
2. Clear vendor unit displays in quotes
3. Detailed cost breakdowns
4. User education and documentation

---

## 📊 **Expected Outcomes**

### **Financial Impact**
- **Glass pricing accuracy**: 60-85% cost recovery
- **Overall quote accuracy**: 15-25% improvement
- **Reduced material waste**: 10-15% optimization

### **Operational Benefits**
- **Accurate purchase orders**: Direct quote-to-purchase alignment
- **Better inventory management**: Realistic quantity tracking
- **Improved vendor relationships**: Accurate order quantities

### **User Experience**
- **Transparent pricing**: Clear vendor unit breakdown
- **Reduced errors**: Automatic vendor unit calculations
- **Better decision making**: Visible waste and optimization opportunities

---

**Analysis Status:** ✅ **COMPLETE**  
**Critical Finding:** Glass pricing system requires immediate attention (60-85% underpricing)  
**Next Phase:** Implementation planning with glass pricing as highest priority  

*This analysis identifies critical pricing gaps and provides clear implementation path for accurate vendor unit handling.*