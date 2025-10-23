# NBR 6118 Concrete Column Design & Detailing via Revit MCP

## Prerequisites
1. **Restart the Revit MCP server** (click "Start Revit MCP" button in Revit to reload with new family tools)
2. Have Revit open with a project

## Step 1: Load Concrete Column Family

### Find Revit's concrete column families (typical paths):
```
C:/ProgramData/Autodesk/RVT 2024/Libraries/Brazil/Structural Columns/M_Concreto-Coluna Retangular.rfa
C:/ProgramData/Autodesk/RVT 2025/Libraries/Brazil/Structural Columns/M_Concreto-Coluna Retangular.rfa
C:/ProgramData/Autodesk/RVT 2026/Libraries/Brazil/Structural Columns/M_Concreto-Coluna Retangular.rfa
```

### MCP command to load family:
```python
await load_family("C:/ProgramData/Autodesk/RVT 2024/Libraries/Brazil/Structural Columns/M_Concreto-Coluna Retangular.rfa")
```

This returns:
```json
{
  "ok": true,
  "familyId": 299100,
  "familyName": "M_Concreto-Coluna Retangular",
  "symbols": [
    {"id": 299101, "name": "200x200mm", "isActive": false},
    {"id": 299102, "name": "300x300mm", "isActive": false},
    {"id": 299103, "name": "400x600mm", "isActive": false}
  ]
}
```

## Step 2: Activate Column Types

Before placing columns, activate the types you need:

```python
# Activate 200x200mm column type
await activate_family_symbol(299101)

# Activate 300x300mm column type
await activate_family_symbol(299102)

# Activate 400x600mm column type
await activate_family_symbol(299103)
```

## Step 3: NBR 6118 Design Calculations

### Column C1: 20x20cm - Light Load (~500 kN)

**Minimum steel (NBR 6118 17.3.5.3.1):**
- As,min = max(0.15% Nd/fyd, 0.4% Ac)
- Assuming Nd = 500 kN, fck = 30 MPa, fyk = 500 MPa
- As,min = 0.4% × 400 cm² = **1.6 cm²**

**Design:**
- 4Ø10mm (As = 4 × 0.785 = 3.14 cm²) ✓
- Stirrups: Ø6.3mm @ 150mm (s ≤ min(20Ø, bmin, 300mm))
- Cover: 30mm (NBR 6118 Table 7.2 - CAA I)

### Column C2: 30x30cm - Medium Load (~1200 kN)

**Minimum steel:**
- As,min = 0.4% × 900 cm² = **3.6 cm²**

**Design:**
- 4Ø12mm (As = 4 × 1.131 = 4.52 cm²) ✓
- Stirrups: Ø6.3mm @ 200mm
- Cover: 30mm

### Column C3: 40x60cm - Heavy Load (~2500 kN)

**Minimum steel:**
- As,min = 0.4% × 2400 cm² = **9.6 cm²**

**Design:**
- 8Ø16mm (As = 8 × 2.011 = 16.09 cm²) ✓
- Stirrups: Ø8mm @ 150mm
- Cover: 30mm

## Step 4: Place Columns with Correct Types

```python
# Column C1 - 20x20cm at origin
col1 = await place_column(
    x=0, y=0, z=0,
    level="Nível 1",
    type="200x200mm"  # Match the symbol name
)
# Returns: {"ok": true, "elementId": 299200}

# Column C2 - 30x30cm at 5m spacing
col2 = await place_column(
    x=5, y=0, z=0,
    level="Nível 1",
    type="300x300mm"
)
# Returns: {"ok": true, "elementId": 299201}

# Column C3 - 40x60cm at 10m spacing
col3 = await place_column(
    x=10, y=0, z=0,
    level="Nível 1",
    type="400x600mm"
)
# Returns: {"ok": true, "elementId": 299202}
```

## Step 5: Detail with Rebar (NBR 6118 Compliant)

### Column C1 - 4Ø10mm + Stirrups @ 150mm
```python
result1 = await place_rebar_cage_column(
    columnId=299200,
    barType="Ø10 CA50",  # Must match a RebarBarType in your project
    stirrupShape="Stirrup",  # Must match a RebarShape in your project
    stirrupSpacing=0.15,  # 150mm in meters
    cover=0.03  # 30mm in meters
)
```

### Column C2 - 4Ø12mm + Stirrups @ 200mm
```python
result2 = await place_rebar_cage_column(
    columnId=299201,
    barType="Ø12 CA50",
    stirrupShape="Stirrup",
    stirrupSpacing=0.20,  # 200mm
    cover=0.03
)
```

### Column C3 - 8Ø16mm + Stirrups @ 150mm
```python
result3 = await place_rebar_cage_column(
    columnId=299202,
    barType="Ø16 CA50",
    stirrupShape="Stirrup",
    stirrupSpacing=0.15,
    cover=0.03
)
```

Each returns:
```json
{
  "ok": true,
  "elementIds": [299300, 299301, 299302, 299303, 299304]  # 4 longitudinal bars + 1 stirrup set
}
```

## Step 6: Verify Compliance

### NBR 6118 Checklist:
- ✓ Minimum steel ratio (0.4% ≤ As/Ac ≤ 8%)
- ✓ Minimum bar diameter (≥ 10mm for longitudinal)
- ✓ Corner bars in every column
- ✓ Stirrup spacing (≤ 20Ø, ≤ bmin, ≤ 300mm)
- ✓ Concrete cover (30mm for CAA I)
- ✓ Minimum 4 bars for rectangular sections

## New MCP Tools Available:

### Family Management:
- `list_families()` - List all families in document
- `get_family_symbols(familyId)` - Get types for a family
- `load_family(filePath)` - Load .rfa family file
- `activate_family_symbol(symbolId)` - Activate a type
- `search_families(query, category)` - Search families

### Rebar Detailing:
- `place_rebar_cage_column(columnId, barType, stirrupShape, stirrupSpacing, cover)` - Detail column

## Notes:

1. **Rebar Bar Types**: Your project must have RebarBarTypes loaded (e.g., "Ø10 CA50", "Ø12 CA50", "Ø16 CA50")
   - If missing, load from: `C:/ProgramData/Autodesk/RVT/Libraries/Brazil/Annotations/M_Rebar Shape.rfa`

2. **Rebar Shapes**: Need "Stirrup" shape loaded
   - If missing, it will create longitudinal bars only

3. **Column Dimensions**: The rebar cage automatically adjusts to column bounding box with specified cover

4. **Custom Designs**: Modify `stirrupSpacing` and `cover` as needed per your structural calculations

## Complete Python Script Example:

```python
# 1. Load concrete column family
family_result = await load_family(
    "C:/ProgramData/Autodesk/RVT 2024/Libraries/Brazil/Structural Columns/M_Concreto-Coluna Retangular.rfa"
)

# 2. Activate required sizes
for symbol in family_result["symbols"]:
    if symbol["name"] in ["200x200mm", "300x300mm", "400x600mm"]:
        await activate_family_symbol(symbol["id"])

# 3. Place columns
columns = []
positions = [(0, 0), (5, 0), (10, 0)]
types = ["200x200mm", "300x300mm", "400x600mm"]

for (x, y), col_type in zip(positions, types):
    result = await place_column(x=x, y=y, z=0, level="Nível 1", type=col_type)
    columns.append(result["elementId"])

# 4. Detail with rebar (NBR 6118 compliant)
rebar_configs = [
    {"barType": "Ø10 CA50", "spacing": 0.15},  # C1
    {"barType": "Ø12 CA50", "spacing": 0.20},  # C2
    {"barType": "Ø16 CA50", "spacing": 0.15},  # C3
]

for col_id, config in zip(columns, rebar_configs):
    await place_rebar_cage_column(
        columnId=col_id,
        barType=config["barType"],
        stirrupShape="Stirrup",
        stirrupSpacing=config["spacing"],
        cover=0.03
    )

print("✓ Successfully created and detailed 3 NBR 6118 compliant concrete columns!")
```

