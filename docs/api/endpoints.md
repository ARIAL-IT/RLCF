# REST API Endpoints

## Overview

The RLCF framework provides a comprehensive REST API for managing users, tasks, feedback, and system configuration. All endpoints support JSON request/response format and include detailed OpenAPI documentation.

## Base URL

```
http://localhost:8000
```

## Authentication

### Admin Endpoints
Some endpoints require API key authentication:

```bash
curl -H "X-API-KEY: your-api-key" http://localhost:8000/admin/endpoint
```

Set the API key via environment variable:
```bash
export ADMIN_API_KEY=your-secret-key
```

## User Management

### Create User
```http
POST /users/
```

**Request Body:**
```json
{
  "username": "john_doe",
  "authority_score": 0.5,
  "track_record_score": 0.5,
  "baseline_credential_score": 0.0
}
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "authority_score": 0.5,
  "track_record_score": 0.5,
  "baseline_credential_score": 0.0,
  "credentials": []
}
```

### Get User
```http
GET /users/{user_id}
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
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

### List All Users
```http
GET /users/all?limit=50&offset=0
```

### Add Credential to User
```http
POST /users/{user_id}/credentials/
```

**Request Body:**
```json
{
  "type": "ACADEMIC_DEGREE",
  "value": "JD",
  "verified": true
}
```

## Task Management

### Create Legal Task
```http
POST /tasks/
```

**Request Body:**
```json
{
  "task_type": "STATUTORY_RULE_QA",
  "input_data": {
    "question": "What are the requirements for contract formation?",
    "rule_id": "contract_law_001",
    "context_full": "Legal context here...",
    "relevant_articles": "Article 1, Article 2"
  }
}
```

**Response:**
```json
{
  "id": 1,
  "task_type": "STATUTORY_RULE_QA",
  "input_data": {
    "question": "What are the requirements for contract formation?",
    "rule_id": "contract_law_001",
    "context_full": "Legal context here...",
    "relevant_articles": "Article 1, Article 2"
  },
  "status": "BLIND_EVALUATION",
  "created_at": "2024-01-15T10:30:00Z",
  "responses": [
    {
      "id": 1,
      "output_data": {
        "answer": "AI-generated response...",
        "confidence": 0.85
      },
      "model_version": "gpt-3.5-turbo"
    }
  ]
}
```

### Get Task Details
```http
GET /tasks/{task_id}
```

### List All Tasks
```http
GET /tasks/all?limit=50&status=OPEN&task_type=QA
```

**Query Parameters:**
- `limit` - Number of results (default: 50)
- `offset` - Pagination offset
- `status` - Filter by task status
- `task_type` - Filter by task type
- `user_id` - Filter by user ID

### Update Task Status
```http
PUT /tasks/{task_id}/status
```

**Request Body:**
```json
{
  "status": "AGGREGATED"
}
```

## Feedback Management

### Submit Feedback
```http
POST /feedback/
```

**Request Body:**
```json
{
  "response_id": 1,
  "user_id": 1,
  "feedback_data": {
    "validated_answer": "Corrected AI response...",
    "confidence": "high",
    "position": "partially_correct",
    "reasoning": "The AI response was mostly accurate but missed key details...",
    "sources_verified": true
  }
}
```

**Response:**
```json
{
  "id": 1,
  "response_id": 1,
  "user_id": 1,
  "feedback_data": {
    "validated_answer": "Corrected AI response...",
    "confidence": "high",
    "position": "partially_correct",
    "reasoning": "The AI response was mostly accurate but missed key details...",
    "sources_verified": true
  },
  "accuracy_score": 0.8,
  "consistency_score": 0.75,
  "community_helpfulness_rating": null,
  "submitted_at": "2024-01-15T11:00:00Z"
}
```

### Get Task Feedback
```http
GET /feedback/task/{task_id}
```

### Get User Feedback
```http
GET /feedback/user/{user_id}
```

## Authority Management

### Calculate User Authority
```http
POST /authority/calculate/{user_id}
```

**Request Body:**
```json
{
  "recent_performance": 0.85
}
```

**Response:**
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

### Get Authority Statistics
```http
GET /authority/stats
```

**Response:**
```json
{
  "total_users": 100,
  "average_authority": 0.72,
  "authority_distribution": {
    "0.0-0.2": 5,
    "0.2-0.4": 15,
    "0.4-0.6": 30,
    "0.6-0.8": 35,
    "0.8-1.0": 15
  },
  "top_authorities": [
    {"user_id": 1, "username": "expert_user", "authority_score": 1.85}
  ]
}
```

## Aggregation & Analysis

### Run Task Aggregation
```http
POST /aggregation/run/{task_id}
```

**Response:**
```json
{
  "task_id": 1,
  "aggregation_result": {
    "primary_answer": "Contract formation requires offer, acceptance, and consideration...",
    "confidence_level": 0.85,
    "disagreement_score": 0.25,
    "alternative_positions": [
      {
        "position": "Alternative interpretation...",
        "support": 0.15,
        "reasoning": "Minority view based on..."
      }
    ],
    "expert_disagreement": {
      "consensus_areas": ["Offer and acceptance required"],
      "contention_points": ["Role of consideration in modern contracts"],
      "reasoning_patterns": ["Formalist vs functionalist approaches"]
    }
  },
  "bias_analysis": {
    "total_bias_score": 0.23,
    "bias_level": "low",
    "individual_bias_scores": {
      "demographic": 0.05,
      "professional": 0.12,
      "temporal": 0.03,
      "geographic": 0.08,
      "confirmation": 0.10,
      "anchoring": 0.07
    }
  }
}
```

### Get Disagreement Analysis
```http
GET /aggregation/disagreement/{task_id}
```

### Get Bias Report
```http
GET /bias/task/{task_id}/report
```

**Response:**
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
    "Consider geographic diversity in expert panel",
    "Implement rotation in evaluation assignments"
  ],
  "generated_at": "2024-01-15T12:00:00Z"
}
```

## Configuration Management

### Get Current Model Configuration
```http
GET /config/model
```

**Response:**
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
            "JD": 1.2,
            "PhD": 1.5
          }
        }
      }
    }
  }
}
```

### Update Model Configuration
```http
PUT /config/model
```

**Headers:** `X-API-KEY: your-api-key`

**Request Body:**
```json
{
  "authority_weights": {
    "baseline_credentials": 0.25,
    "track_record": 0.55,
    "recent_performance": 0.2
  },
  "thresholds": {
    "disagreement": 0.35
  }
}
```

### Get Task Configuration
```http
GET /config/tasks
```

### Update Task Configuration
```http
PUT /config/tasks
```

## Devil's Advocate System

### Get Advocate Assignments
```http
GET /devils-advocate/assignments/{task_id}
```

**Response:**
```json
{
  "task_id": 1,
  "assignments": [
    {
      "user_id": 5,
      "username": "critical_expert",
      "instructions": "Focus on potential weaknesses in legal reasoning",
      "assigned_at": "2024-01-15T09:00:00Z"
    }
  ],
  "assignment_probability": 0.1,
  "total_eligible_users": 30
}
```

### Get Critical Prompts
```http
GET /devils-advocate/prompts/{task_type}
```

**Response:**
```json
{
  "task_type": "STATUTORY_RULE_QA",
  "base_prompts": [
    "What are the potential weaknesses in this reasoning?",
    "Are there alternative interpretations that weren't considered?"
  ],
  "task_specific_prompts": [
    "What important statutory nuances or exceptions are missing?",
    "How might opposing counsel challenge this interpretation?"
  ],
  "count": 4
}
```

## AI Service Integration

### Generate AI Response
```http
POST /ai/generate_response
```

**Headers:** `X-API-KEY: your-api-key`

**Request Body:**
```json
{
  "task_type": "STATUTORY_RULE_QA",
  "input_data": {
    "question": "What constitutes a valid contract?",
    "context_full": "Legal context..."
  },
  "model_config": {
    "name": "openai/gpt-4",
    "api_key": "sk-...",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

**Response:**
```json
{
  "success": true,
  "response_data": {
    "answer": "A valid contract requires...",
    "confidence": 0.9,
    "reasoning": "Based on fundamental contract law principles..."
  },
  "model_used": "openai/gpt-4"
}
```

### Get Available AI Models
```http
GET /ai/models
```

**Response:**
```json
{
  "models": [
    {
      "id": "openai/gpt-4",
      "name": "GPT-4",
      "description": "Most capable OpenAI model",
      "recommended_for": ["complex_legal_analysis", "statutory_interpretation"]
    },
    {
      "id": "anthropic/claude-3-sonnet",
      "name": "Claude 3 Sonnet",
      "description": "Excellent for legal reasoning and analysis",
      "recommended_for": ["legal_reasoning", "risk_assessment", "drafting"]
    }
  ]
}
```

## Data Export

### Export Task Dataset
```http
GET /export/tasks?format=csv&task_type=QA&start_date=2024-01-01
```

**Query Parameters:**
- `format` - Export format: `csv`, `json`, `yaml`
- `task_type` - Filter by task type
- `start_date` - Start date filter
- `end_date` - End date filter
- `include_feedback` - Include feedback data

### Export Scientific Dataset
```http
GET /export/dataset?format=scientific
```

Exports data in academic publication format with:
- Statistical summaries
- Bias analysis reports
- Authority score distributions
- Uncertainty preservation metrics

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error description",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `401` - Unauthorized
- `403` - Forbidden (API key required)
- `404` - Not Found
- `422` - Unprocessable Entity (schema validation)
- `500` - Internal Server Error

## Rate Limiting

API endpoints may be rate-limited in production:
- Standard endpoints: 100 requests/minute
- Admin endpoints: 50 requests/minute
- AI generation endpoints: 10 requests/minute

## OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

**Next Steps:**
- [Data Schemas](schemas.md) - Request/response schema definitions
- [Authentication](authentication.md) - Detailed authentication setup
- [API Usage Examples](../examples/api-usage/) - Code examples
