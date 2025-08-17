# Data Schemas

This document describes the data structures used throughout the RLCF API. All schemas are defined using Pydantic models for automatic validation and documentation generation.

## User Management Schemas

### User
```json
{
  "id": 1,
  "username": "string",
  "authority_score": 0.75,
  "track_record_score": 0.8,
  "baseline_credential_score": 1.2,
  "credentials": [
    {
      "id": 1,
      "type": "ACADEMIC_DEGREE",
      "value": "JD",
      "verified": true
    }
  ]
}
```

**Field Descriptions:**
- `id`: Unique user identifier (auto-generated)
- `username`: Unique username (required)
- `authority_score`: Current authority score [0.0, 2.0]
- `track_record_score`: Historical performance [0.0, 1.0]
- `baseline_credential_score`: Credential-based score [0.0, 2.0]
- `credentials`: List of user credentials

### UserCreate
```json
{
  "username": "string",
  "authority_score": 0.5,
  "track_record_score": 0.5,
  "baseline_credential_score": 0.0
}
```

**Field Validation:**
- `username`: Must be unique, 3-50 characters
- `authority_score`: Optional, defaults to 0.5
- `track_record_score`: Optional, defaults to 0.5
- `baseline_credential_score`: Optional, defaults to 0.0

### Credential
```json
{
  "id": 1,
  "type": "ACADEMIC_DEGREE",
  "value": "JD",
  "verified": true
}
```

**Credential Types:**
- `ACADEMIC_DEGREE`: Bachelor, LLM, JD, PhD
- `PROFESSIONAL_EXPERIENCE`: Years of experience (numeric)
- `PUBLICATION`: Number of publications (numeric)
- `INSTITUTIONAL_ROLE`: Junior, Senior, Partner

### CredentialCreate
```json
{
  "type": "ACADEMIC_DEGREE",
  "value": "JD",
  "verified": false
}
```

## Task Management Schemas

### LegalTask
```json
{
  "id": 1,
  "task_type": "STATUTORY_RULE_QA",
  "input_data": {
    "question": "string",
    "context_full": "string",
    "rule_id": "string"
  },
  "ground_truth_data": {
    "answer_text": "string"
  },
  "status": "BLIND_EVALUATION",
  "created_at": "2024-01-15T10:30:00Z",
  "responses": []
}
```

**Task Types (Enum):**
- `SUMMARIZATION`
- `CLASSIFICATION`
- `QA`
- `STATUTORY_RULE_QA`
- `PREDICTION`
- `NLI`
- `NER`
- `DRAFTING`
- `RISK_SPOTTING`
- `DOCTRINE_APPLICATION`
- `COMPLIANCE_RISK_SPOTTING`
- `DOC_CLAUSE_CLASSIFICATION`
- `DRAFTING_GENERATION_PARALLEL`
- `NAMED_ENTITY_BIO`
- `NLI_ENTAILMENT`
- `SUMMARIZATION_PAIRS`
- `VIOLATION_OUTCOME_PREDICTION`

**Task Status (Enum):**
- `OPEN`: Task is available for AI response generation
- `BLIND_EVALUATION`: Task is in blind evaluation phase
- `CLOSED`: Task evaluation is complete

### LegalTaskCreate
```json
{
  "task_type": "QA",
  "input_data": {
    "context": "Legal context here...",
    "question": "What is the legal question?"
  }
}
```

**Dynamic Input Data by Task Type:**

#### QA Tasks
```json
{
  "context": "string",
  "question": "string"
}
```

#### STATUTORY_RULE_QA Tasks
```json
{
  "id": "string",
  "question": "string",
  "rule_id": "string",
  "context_full": "string",
  "context_count": 0,
  "relevant_articles": "string",
  "tags": "string",
  "category": "string",
  "metadata_full": "string"
}
```

#### CLASSIFICATION Tasks
```json
{
  "text": "string",
  "unit": "string"
}
```

#### PREDICTION Tasks
```json
{
  "facts": "string"
}
```

### Response
```json
{
  "id": 1,
  "task_id": 1,
  "output_data": {
    "message": "AI-generated response",
    "confidence": 0.85
  },
  "model_version": "gpt-3.5-turbo",
  "created_at": "2024-01-15T10:35:00Z",
  "feedback": []
}
```

## Feedback Schemas

### Feedback
```json
{
  "id": 1,
  "response_id": 1,
  "user_id": 1,
  "feedback_data": {
    "validated_answer": "string",
    "position": "correct",
    "reasoning": "string"
  },
  "accuracy_score": 0.85,
  "consistency_score": 0.78,
  "community_helpfulness_rating": 4.2,
  "submitted_at": "2024-01-15T11:00:00Z"
}
```

### FeedbackCreate
```json
{
  "response_id": 1,
  "user_id": 1,
  "feedback_data": {
    "validated_answer": "string",
    "position": "correct",
    "reasoning": "string"
  }
}
```

**Dynamic Feedback Data by Task Type:**

#### QA Feedback
```json
{
  "validated_answer": "string",
  "position": "correct|incorrect",
  "reasoning": "string"
}
```

#### STATUTORY_RULE_QA Feedback
```json
{
  "validated_answer": "string",
  "confidence": "high|medium|low",
  "position": "correct|partially_correct|incorrect",
  "reasoning": "string",
  "sources_verified": true
}
```

#### CLASSIFICATION Feedback
```json
{
  "validated_labels": ["label1", "label2"],
  "reasoning": "string"
}
```

#### PREDICTION Feedback
```json
{
  "chosen_outcome": "violation|no_violation",
  "reasoning": "string"
}
```

## Authority & Aggregation Schemas

### AuthorityCalculationRequest
```json
{
  "recent_performance": 0.85
}
```

### AuthorityCalculationResponse
```json
{
  "user_id": 1,
  "new_authority_score": 0.78,
  "components": {
    "baseline_credentials": 1.2,
    "track_record": 0.75,
    "recent_performance": 0.85
  },
  "weights": {
    "baseline_credentials": 0.3,
    "track_record": 0.5,
    "recent_performance": 0.2
  }
}
```

### AggregationResult
```json
{
  "task_id": 1,
  "aggregation_result": {
    "primary_answer": "string",
    "confidence_level": 0.85,
    "disagreement_score": 0.25,
    "alternative_positions": [
      {
        "position": "string",
        "support": 0.15,
        "reasoning": "string"
      }
    ],
    "expert_disagreement": {
      "consensus_areas": ["string"],
      "contention_points": ["string"],
      "reasoning_patterns": ["string"]
    },
    "epistemic_metadata": {
      "uncertainty_sources": ["string"],
      "suggested_research": ["string"]
    }
  }
}
```

### BiasReport
```json
{
  "task_id": 1,
  "bias_scores": {
    "demographic": 0.05,
    "professional": 0.12,
    "temporal": 0.03,
    "geographic": 0.08,
    "confirmation": 0.10,
    "anchoring": 0.07
  },
  "total_bias_score": 0.23,
  "bias_level": "low",
  "mitigation_recommendations": [
    "string"
  ],
  "generated_at": "2024-01-15T12:00:00Z"
}
```

**Bias Levels:**
- `low`: total_bias_score ≤ 0.5
- `medium`: 0.5 < total_bias_score ≤ 1.0
- `high`: total_bias_score > 1.0

## Configuration Schemas

### ModelConfig
```json
{
  "authority_weights": {
    "baseline_credentials": 0.3,
    "track_record": 0.5,
    "recent_performance": 0.2
  },
  "track_record": {
    "update_factor": 0.05
  },
  "thresholds": {
    "disagreement": 0.4
  },
  "baseline_credentials": {
    "types": {
      "ACADEMIC_DEGREE": {
        "weight": 0.3,
        "scoring_function": {
          "type": "map",
          "values": {
            "Bachelor": 1.0,
            "LLM": 1.1,
            "JD": 1.2,
            "PhD": 1.5
          },
          "default": 0.0
        }
      }
    }
  }
}
```

**Scoring Function Types:**
- `map`: Discrete value mapping
- `formula`: Mathematical expression evaluation

**Mathematical Constraints:**
- Authority weights must sum to 1.0
- All scores are non-negative
- Authority scores are clamped to [0.0, 2.0]

### TaskConfig
```json
{
  "task_types": {
    "QA": {
      "input_data": {
        "context": "str",
        "question": "str"
      },
      "ground_truth_keys": ["answers"],
      "feedback_data": {
        "validated_answer": "str",
        "position": "Literal['correct', 'incorrect']",
        "reasoning": "str"
      }
    }
  }
}
```

## AI Service Schemas

### AIModelConfig
```json
{
  "name": "openai/gpt-4",
  "api_key": "string",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

### AIGenerationRequest
```json
{
  "task_type": "STATUTORY_RULE_QA",
  "input_data": {},
  "model_config": {
    "name": "openai/gpt-4",
    "api_key": "string",
    "temperature": 0.7
  }
}
```

### AIGenerationResponse
```json
{
  "success": true,
  "response_data": {
    "answer": "string",
    "confidence": 0.9,
    "reasoning": "string"
  },
  "model_used": "openai/gpt-4"
}
```

## Devil's Advocate Schemas

### DevilsAdvocateAssignment
```json
{
  "id": 1,
  "task_id": 1,
  "user_id": 5,
  "instructions": "string",
  "assigned_at": "2024-01-15T09:00:00Z"
}
```

### DevilsAdvocatePrompts
```json
{
  "task_type": "STATUTORY_RULE_QA",
  "base_prompts": [
    "What are the potential weaknesses in this reasoning?",
    "Are there alternative interpretations that weren't considered?"
  ],
  "task_specific_prompts": [
    "What important statutory nuances or exceptions are missing?"
  ],
  "count": 3
}
```

## Export Schemas

### TaskExportOptions
```json
{
  "format": "csv",
  "task_type": "QA",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "include_feedback": true
}
```

**Export Formats:**
- `csv`: Comma-separated values
- `json`: JSON format
- `yaml`: YAML format
- `scientific`: Academic publication format

## Validation Rules

### General Rules
- All dates in ISO 8601 format
- Scores normalized to appropriate ranges
- Required fields must be present
- Enum values must match exactly

### Authority Score Constraints
- `authority_score`: [0.0, 2.0]
- `track_record_score`: [0.0, 1.0]
- `baseline_credential_score`: [0.0, 2.0]

### Mathematical Constraints
- Authority weights must sum to 1.0
- Disagreement threshold: [0.0, 1.0]
- Update factor: [0.0, 1.0]

### Text Constraints
- `username`: 3-50 characters, alphanumeric + underscore
- `reasoning`: Minimum 10 characters for meaningful feedback
- API keys: Not logged or stored in plain text

## Error Responses

### ValidationError
```json
{
  "detail": [
    {
      "loc": ["field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### HTTPException
```json
{
  "detail": "Error description",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

**Next Steps:**
- [Authentication](authentication.md) - API security setup
- [API Endpoints](endpoints.md) - Complete endpoint reference
- [API Usage Examples](../examples/api-usage/) - Code examples
