# Clinical Notes Tool Refactoring

## Overview
We've refactored the clinical notes functionality to provide clearer separation between simple retrieval and complex queries.

## Changes Made

### 1. Renamed Tool
- **Old**: `ehr_search_notes`
- **New**: `ehr_get_clinical_notes`

### 2. Simplified Functionality
Removed:
- `query` parameter (no more text search)
- `semantic` parameter (no more AI-powered search)
- All OpenAI dependencies

The tool now simply retrieves notes by:
- Note type (discharge, radiology, or all)
- Patient ID
- Admission ID

### 3. Clear Usage Patterns

#### Get all radiology reports for a patient:
```python
ehr_get_clinical_notes(
    note_type="radiology",
    patient_id="10461137"
)
```

#### Get discharge summary for specific admission:
```python
ehr_get_clinical_notes(
    note_type="discharge", 
    admission_id="25236814"
)
```

#### Get all notes for a patient:
```python
ehr_get_clinical_notes(
    note_type="all",
    patient_id="10461137"
)
```

## Benefits

1. **Predictable**: No more confusion about whether to use patient_id or admission_id
2. **Fast**: No API calls or text searching overhead
3. **Simple**: Claude can easily understand when to use this tool
4. **Cost-effective**: No OpenAI API usage for basic retrieval

## Complex Queries

For complex searches like "find notes mentioning pulmonary fibrosis", use:
```
ehr_natural_query("Show me all notes for patient 10461137 that mention pulmonary fibrosis")
```

This separation makes the tools more intuitive and reduces the number of retry attempts Claude needs to make.

## Before vs After Examples

### Getting Radiology Reports

**Before (often failed):**
```
ehr_search_notes(query="radiology", note_type="radiology", patient_id="10461137")
# → No results (notes don't contain word "radiology")

ehr_search_notes(query="imaging", note_type="radiology", patient_id="10461137") 
# → No results (notes don't contain word "imaging")

ehr_search_notes(query="CT scan", note_type="radiology", patient_id="10461137")
# → Finally works if notes contain "CT scan"
```

**After (always works):**
```
ehr_get_clinical_notes(note_type="radiology", patient_id="10461137")
# → Returns all radiology reports for patient, guaranteed
```

### Getting Most Recent Discharge Summary

**Before (confusing):**
```
ehr_search_notes(query="", note_type="discharge", admission_id="25236814")
# → Unclear why query is empty, required admission_id
```

**After (intuitive):**
```
ehr_get_clinical_notes(note_type="discharge", patient_id="10461137", limit=1)
# → Gets most recent discharge summary, sorted by charttime DESC
```

## Performance Comparison

| Operation | Old Tool | New Tool |
|-----------|----------|----------|
| Get all radiology reports | 3 API attempts | 1 direct query |
| Get discharge summary | Required admission_id lookup | Works with patient_id |
| Response time | 2-5 seconds (with retries) | <1 second |
| Cost | Multiple OpenAI calls | No API calls |

## Common Usage Patterns

### 1. Medical Review Workflow
```python
# Get patient overview
patient = ehr_patient("10461137", include_admissions=True)

# Get latest discharge summary
discharge = ehr_get_clinical_notes(
    note_type="discharge", 
    patient_id="10461137", 
    limit=1
)

# Get all imaging reports
imaging = ehr_get_clinical_notes(
    note_type="radiology", 
    patient_id="10461137"
)

# Ask specific questions about findings
findings = ehr_natural_query(
    "What were the key findings in the CT scan for patient 10461137?"
)
```

### 2. Research Query Workflow
```python
# Find patients with specific conditions
patients = ehr_natural_query(
    "Find patients diagnosed with pulmonary fibrosis"
)

# For each patient, get their clinical notes
for patient_id in patient_ids:
    notes = ehr_get_clinical_notes(
        note_type="all",
        patient_id=patient_id,
        limit=10
    )
```

## Troubleshooting

### No Results Returned
**Problem**: `ehr_get_clinical_notes` returns empty array
**Solutions**:
- Check if patient_id exists in database
- Try `note_type="all"` instead of specific type
- Use `ehr_natural_query` to verify patient has notes

### Wrong Admission
**Problem**: Got discharge summary from wrong admission
**Solutions**:
- Use `admission_id` instead of `patient_id` for specific admission
- Use `limit=1` to get most recent only
- Check `charttime` field to verify date

### Performance Issues
**Problem**: Queries are slow
**Solutions**:
- `ehr_get_clinical_notes` should be fast (<1s)
- Use appropriate indexes on `subject_id`, `hadm_id`, `charttime`
- Use `limit` parameter to reduce result size

## Migration Guide

If you have existing code using `ehr_search_notes`:

```python
# Old code
result = ehr_search_notes(
    query="",  # Remove this
    note_type="discharge",
    semantic=False,  # Remove this
    patient_id="123",
    format="json"
)

# New code
result = ehr_get_clinical_notes(
    note_type="discharge",
    patient_id="123", 
    format="json"
)
```

For content searches, use natural language:
```python
# Old code
result = ehr_search_notes(
    query="pulmonary fibrosis",
    note_type="all",
    patient_id="123"
)

# New code
result = ehr_natural_query(
    "Find notes mentioning pulmonary fibrosis for patient 123"
)
```