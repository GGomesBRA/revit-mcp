# 🚀 Quick Start: Create 3 NBR 6118 Concrete Columns with Rebar

## Step 1: Restart Revit MCP Server ⚠️ IMPORTANT

The new family management tools were just added and need the server to restart:

1. In Revit, go to the **RevitMCP** tab
2. Click **"Start Revit MCP"** button
3. Wait for the output window to show "Server running on http://127.0.0.1:48884"

## Step 2: Open Claude Desktop or MCP Client

Make sure your MCP client is configured with the revit-mcp server (it should already be set up).

## Step 3: Run This Complete Script

Copy and paste this into Claude Desktop:

```
Please help me create 3 concrete columns with NBR 6118 compliant reinforcement:

1. Load the concrete column family from:
   C:/ProgramData/Autodesk/RVT 2024/Libraries/Brazil/Structural Columns/M_Concreto-Coluna Retangular.rfa

2. Activate these column types:
   - 200x200mm
   - 300x300mm  
   - 400x600mm

3. Place the 3 columns at coordinates:
   - Column C1 (20x20cm) at x=0, y=0, level="Nível 1"
   - Column C2 (30x30cm) at x=5, y=0, level="Nível 1"
   - Column C3 (40x60cm) at x=10, y=0, level="Nível 1"

4. Detail each column with reinforcement following NBR 6118:
   - C1: 4Ø10mm bars, stirrups @ 150mm, cover 30mm
   - C2: 4Ø12mm bars, stirrups @ 200mm, cover 30mm
   - C3: 4Ø16mm bars, stirrups @ 150mm, cover 30mm

Use the revit-mcp tools to accomplish this.
```

## What Will Happen:

Claude will automatically:
1. ✅ Load the concrete column family using `load_family()`
2. ✅ Activate the three sizes using `activate_family_symbol()`
3. ✅ Place 3 columns using `place_column()`
4. ✅ Detail each with rebar using `place_rebar_cage_column()`

## Expected Result in Revit:

You'll see:
- **3 concrete columns** at 5m spacing
- Each with **4 longitudinal bars at corners**
- Each with **stirrups distributed along height**
- All **NBR 6118 compliant** (minimum steel, spacing, cover)

## Troubleshooting:

### Error: "Family file not found"
- Check the path for your Revit version (2024/2025/2026)
- Update path in the command to match your installation

### Error: "RebarBarType not found"
- Your project doesn't have rebar types loaded
- Load from: `C:/ProgramData/Autodesk/RVT/Libraries/Brazil/Annotations/M_Rebar Shape.rfa`
- Or omit `barType` parameter - it will use first available

### Error: "Tool not found"
- You forgot to restart the MCP server
- Go back to Step 1 ☝️

### Error: "Column is not concrete"
- The placed columns are steel (UC-Universal Columns)
- This is why we load the concrete family first
- Make sure Step 1 (load family) completes before Step 3 (place columns)

## Advanced: Manual MCP Tool Calls

If you prefer to call tools directly:

```python
# 1. Load family
result = await load_family(
    "C:/ProgramData/Autodesk/RVT 2024/Libraries/Brazil/Structural Columns/M_Concreto-Coluna Retangular.rfa"
)

# 2. Activate symbols
for symbol in result["symbols"]:
    if symbol["name"] in ["200x200mm", "300x300mm", "400x600mm"]:
        await activate_family_symbol(symbol["id"])

# 3. Place columns
c1 = await place_column(x=0, y=0, z=0, level="Nível 1", type="200x200mm")
c2 = await place_column(x=5, y=0, z=0, level="Nível 1", type="300x300mm")
c3 = await place_column(x=10, y=0, z=0, level="Nível 1", type="400x600mm")

# 4. Detail with rebar
await place_rebar_cage_column(
    columnId=c1["elementId"],
    barType="Ø10 CA50",
    stirrupShape="Stirrup",
    stirrupSpacing=0.15,
    cover=0.03
)

await place_rebar_cage_column(
    columnId=c2["elementId"],
    barType="Ø12 CA50",
    stirrupShape="Stirrup",
    stirrupSpacing=0.20,
    cover=0.03
)

await place_rebar_cage_column(
    columnId=c3["elementId"],
    barType="Ø16 CA50",
    stirrupShape="Stirrup",
    stirrupSpacing=0.15,
    cover=0.03
)
```

## Available MCP Tools:

### Family Management (NEW! ⭐)
- `list_families()` 
- `get_family_symbols(familyId)`
- `load_family(filePath)`
- `activate_family_symbol(symbolId)`
- `search_families(query, category)`

### Element Creation
- `place_column(x, y, z, level, type)`
- `create_wall_line(x1, y1, x2, y2, z, level, wall_type)`
- `place_rebar_cage_column(columnId, barType, stirrupShape, stirrupSpacing, cover)` ⭐

### Queries
- `get_levels()`
- `get_element_types()`
- `quantify_walls()`

### Geometry
- `draw_model_line(x1, y1, z1, x2, y2, z2)`
- `draw_detail_line(x1, y1, x2, y2, z1, z2)`
- `draw_model_polyline(points)`

## Success! 🎉

If everything worked, you now have:
- ✅ 3 concrete columns with different dimensions
- ✅ Reinforcement detailing according to NBR 6118
- ✅ Proper steel ratios, spacing, and cover
- ✅ Ready for structural documentation

## Next Steps:

1. Modify column positions and dimensions as needed
2. Adjust rebar configuration for your specific loads
3. Explore other MCP tools for walls, beams, etc.
4. Check out `REVIT_MCP_IMPLEMENTATION_SUMMARY.md` for full documentation

---

**Need Help?** Check the logs:
- Server log: Output window in Revit (after clicking Start Revit MCP)
- Route log: `C:\Users\m170488\AppData\Roaming\pyRevit\Extensions\revit_routes.log`

