# Agent System Updates - Accuracy-Driven Routing

## Summary

Updated the agent system to implement **accuracy-driven decision making** where the accuracy score determines whether to provide troubleshooting steps or route to professional service.

## Key Changes

### 1. Core Orchestrator (`agents/core_orchestrator.py`)

**Added Accuracy-Driven Workflow:**
- The orchestrator now checks the accuracy score returned by the RAG retrieval agent
- Routes based on accuracy level:
  - **≥75% (High/Very High)** → Provide troubleshooting steps
  - **60-74% (Medium)** → Provide steps with disclaimer
  - **<60% (Low)** → Recommend professional service
  - **0% + Error** → Wrong appliance type detected, ask for correct model

**New Decision Point (Phase 3):**
```
STEP 1: Check for Wrong Model Error
  - If error = "appliance_type_mismatch"
  - Display error message
  - Ask for correct model
  - DO NOT proceed

STEP 2: Check Accuracy Score
  - Extract accuracy score from RAG results

STEP 3: Route Based on Accuracy
  - Scenario A: High Accuracy (≥75%) + Safe → Troubleshooting
  - Scenario B: Medium Accuracy (60-74%) → Troubleshooting with disclaimer
  - Scenario C: Low Accuracy (<60%) → Service
  - Scenario D: Unsafe Actions → Service (regardless of accuracy)
```

**Added Accuracy Score Display:**
```
📊 **Accuracy Score: 78.5% (High)**
These troubleshooting steps are highly accurate for your {Brand} {Model} {Type}.

Breakdown:
- Problem-Solution Match: 82% (55% weight)
- Model Match: 100% (25% weight)
- Brand Match: 100% (20% weight)
```

**Added Wrong Model Detection:**
```
⚠️ ERROR: The model {model} is a {detected_type}, not a {expected_type}.
Please provide the correct {expected_type} model number.
```

### 2. RAG Retrieval Agent (`agents/rag_retrieval_agent.py`)

**Updated Tool Call Requirements:**
- Now REQUIRES passing: `user_model`, `user_brand`, `appliance_type`
- These parameters are essential for accuracy scoring

**Updated Output Format:**
- Now includes `accuracy_score` in all responses
- Includes error details when wrong model detected

**Example Output:**
```json
{
  "rag_results": {
    "query_used": "...",
    "context": "...",
    "accuracy_score": {
      "accuracy": 78.5,
      "level": "High",
      "breakdown": {
        "similarity": 82.0,
        "model_match": 100,
        "brand_match": 100
      },
      "error": null,
      "error_message": null
    }
  }
}
```

**Wrong Model Detection:**
```json
{
  "rag_results": {
    "accuracy_score": {
      "accuracy": 0,
      "level": "Wrong Appliance Type",
      "error": "appliance_type_mismatch",
      "error_message": "⚠️ ERROR: The model WD53DBA900H is a laundry combo, not a refrigerator...",
      "detected_model_type": "laundry combo",
      "expected_type": "refrigerator"
    }
  }
}
```

## Accuracy Score Components

The accuracy score measures **"How effectively will this solution solve the customer's specific problem for their exact appliance model?"**

### Components (Weighted):
1. **Problem-Solution Match (55%)** - MOST IMPORTANT
   - Measures how well the manual content addresses the specific problem
   - Based on cosine similarity between query and retrieved content

2. **Model Match (25%)**
   - Whether we have the manual for this exact model
   - 100% for exact match, 80% for series match, 50% for brand series match

3. **Brand Match (20%)**
   - Whether the manual is from the correct brand

### Accuracy Levels:
- **90%+ (Very High)**: Exact model, highly relevant → Very likely to solve
- **75-89% (High)**: Good match, relevant → Should solve problem
- **60-74% (Medium)**: Partial match → May help, provide with disclaimer
- **40-59% (Low)**: Limited match → Recommend service
- **0-39% (Very Low)**: No relevant info → Require service
- **0% + Error**: Wrong appliance type → Ask for correct model

## User Experience Improvements

### Before:
- No indication of how confident the system is
- Provided troubleshooting steps even when accuracy was low
- No detection of wrong model provided

### After:
- **Clear accuracy score** displayed with every response
- **Automatic routing** based on accuracy:
  - High accuracy → Troubleshooting
  - Low accuracy → Service recommendation
- **Wrong model detection**:
  - Detects when user provides microwave model for refrigerator problem
  - Returns 0% accuracy with clear error message
  - Asks user to provide correct model

### Example User Interaction:

**High Accuracy (78.5%):**
```
📊 **Accuracy Score: 78.5% (High)**
These troubleshooting steps are highly accurate for your Samsung RS28A5F61SR refrigerator.

**How to Fix: Refrigerator Not Cooling**

**Step 1: Check Temperature Settings**
Set refrigerator to 38°F and freezer to 0°F.
Why: Incorrect settings can prevent proper cooling.

**Step 2: Clean Condenser Coils**
...

Did that solve your issue?
```

**Low Accuracy (45%):**
```
I don't have high-confidence troubleshooting information for your LG LFXS28968S refrigerator.

📊 **Accuracy Score: 45% (Low)**
- Problem-Solution Match: 50%
- Model Match: 0%
- Brand Match: 100%

Reason: No exact manual found for this LG model.

To ensure proper resolution, I recommend professional service. I can create a service ticket. Would you like me to do that?
```

**Wrong Model:**
```
⚠️ ERROR: The model WD53DBA900H is a laundry combo, not a refrigerator.
Please provide the correct refrigerator model number so I can help you with accurate troubleshooting steps.
```

## Technical Implementation

### Files Modified:
1. `agents/core_orchestrator.py` - Main orchestrator with accuracy-driven routing
2. `agents/rag_retrieval_agent.py` - Updated to return accuracy scores

### Backend Changes (Already Implemented):
1. `tools.py`:
   - `search_samsung_manuals_rag()` - Returns accuracy scores
   - `calculate_accuracy_score()` - Calculates accuracy with new formula
   - `_check_model_appliance_type()` - Detects wrong appliance type

2. Accuracy Formula:
   ```python
   accuracy = (
       similarity * 0.55 +      # Problem-solution relevance
       model_match * 0.25 +     # Model match
       brand_match * 0.20       # Brand match
   )
   ```

## Testing

The system has been tested with 10 test contexts:
- High accuracy cases (78.5%, 78.4%, 74.7%)
- Medium accuracy cases (63.3%, 61.4%)
- Low accuracy / No information cases (0%)
- **Wrong model detection** (0% with error message)

See `accuracy_reports/` directory for detailed test results.

## Next Steps

1. **Test the agents in conversation** to ensure routing works correctly
2. **Monitor user feedback** on accuracy score display
3. **Adjust thresholds** if needed based on real-world performance
4. **Add more appliance manuals** to improve coverage

## Benefits

✅ **User Trust**: Clear accuracy score builds confidence
✅ **Better Outcomes**: Only provide troubleshooting when likely to work
✅ **Reduced Frustration**: Don't waste time on low-accuracy solutions
✅ **Error Prevention**: Catch wrong model before providing incorrect steps
✅ **Professional When Needed**: Route to service when appropriate
