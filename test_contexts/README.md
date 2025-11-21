# RAG Testing with User Context

Test the RAG system in isolation with predefined user contexts.

## Test Context Files

### Samsung Appliances
- `user_context_microwave.json` - Samsung MC12DB8700 microwave - food not heating
- `user_context_microwave_display_error.json` - Samsung MC12DB8700 microwave - error code C-10
- `user_context_refrigerator.json` - Samsung RS28A5F61** refrigerator - not cooling, warm temperature
- `user_context_refrigerator_ice_maker.json` - Samsung RS28A5F61** refrigerator - ice maker not producing ice
- `user_context_refrigerator_water_leak.json` - Samsung RS28A5F61** refrigerator - water leaking from door
- `user_context_washer_not_draining.json` - Samsung WD8000D washer - not draining water

### LG Appliances
- `user_context_lg_refrigerator.json` - LG LRMDS3006S refrigerator - loud buzzing noise
- `user_context_dryer_not_heating.json` - LG DLEX4000B dryer - not heating, clothes damp
- `user_context_washer_vibration.json` - LG WM4000HWA washer - extreme vibration during spin

## Usage

### Run Test with Predefined Context

```bash
# Test microwave context
python test_rag_with_context.py --context test_contexts/user_context_microwave.json

# Test refrigerator context
python test_rag_with_context.py --context test_contexts/user_context_refrigerator.json
```

### Run Test with Custom Query

```bash
python test_rag_with_context.py \
  --context test_contexts/user_context_microwave.json \
  --query "microwave not heating food troubleshooting steps"
```

## What It Tests

1. **Basic RAG Search** - No filtering, all results
2. **Enhanced RAG Search** - With 70% similarity threshold
3. **Accuracy Scoring** - Shows breakdown of:
   - **Problem-Solution Relevance** - Does the content address their specific problem?
   - **Model Match** - Is it the right appliance model?
   - **Brand Match** - Is it the right brand?
4. **Threshold Testing** - Tests different similarity thresholds (90%, 80%, 70%, 60%, 50%)

## Output

The test shows:
- Number of results found
- Top result previews
- **Accuracy score breakdown:**
  - Problem-Solution Relevance (similarity to user's specific problem)
  - Model Match (exact model match percentage)
  - Brand Match (brand matching percentage)
- Final accuracy score (how effectively the solution will solve their problem)

## Test All Contexts

```bash
# Run all Samsung tests
for file in test_contexts/user_context_*.json; do
  echo "Testing: $file"
  python test_rag_with_context.py --context "$file"
  echo ""
done
```

## Creating Your Own Context

Copy one of the JSON files and modify:

```json
{
  "appliance": {
    "brand": "Samsung",       // Brand name
    "type": "microwave",      // Appliance type
    "model": "MC12DB8700"     // Model number
  },
  "problem": {
    "description": "food not heating up properly",  // Problem description
    "symptoms": [...]  // Detailed symptoms
  }
}
```

## Goal

Target: **90%+ accuracy score** - meaning the troubleshooting steps will effectively solve the customer's specific problem for their appliance model.

### What the Accuracy Score Means

| Score | Meaning |
|-------|---------|
| 90%+ | Very High - Steps will very likely solve the specific problem |
| 75-89% | High - Steps should work for this problem |
| 60-74% | Medium - Steps might help but may not fully resolve the issue |
| 40-59% | Low - Steps may not address the specific problem |
| <40% | Very Low - Steps unlikely to solve this problem |
