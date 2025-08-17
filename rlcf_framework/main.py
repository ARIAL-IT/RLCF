from fastapi import FastAPI, Depends, HTTPException, Security, Query, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import ValidationError, create_model
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, func
from sqlalchemy.orm import selectinload
from fastapi import Response # Import Response
from . import (
    models,
    schemas,
    authority_module,
    aggregation_engine,
    services,
    export_dataset,
)
from .ai_service import openrouter_service, AIModelConfig, cleanup_ai_service
from .database import SessionLocal
from .models import TaskStatus, TaskType  # Import TaskType Enum
from .dependencies import get_db, get_model_settings, get_task_settings
from .config import (
    ModelConfig,
    load_model_config,
    TaskConfig,
    load_task_config,
    ModelConfig,
    TaskConfig,
)
import yaml
from .database import engine
import os
import numpy
import pandas as pd
import io
import logging
import traceback
import json

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rlcf_detailed.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Sicurezza Semplice per l'Endpoint di Configurazione ---
# In produzione, usare OAuth2 o un sistema più robusto.
API_KEY = os.getenv("ADMIN_API_KEY", "supersecretkey")
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(status_code=403, detail="Could not validate credentials")


# --- App e DB Setup ---
app = FastAPI(title="RLCF Framework API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


@app.on_event("startup")
async def startup_event():
    """Initialize database and create admin user if it doesn't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    
    async with SessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                select(models.User).filter(models.User.username == "admin")
            )
            admin_user = result.scalar_one_or_none()
            if not admin_user:
                print("Admin user not found, creating one...")
                new_admin = models.User(
                    username="admin",
                    authority_score=1.0,
                    baseline_credential_score=1.0,
                    track_record_score=1.0,
                )
                session.add(new_admin)
                await session.commit()
                print("Default admin user created.")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    await cleanup_ai_service()


# --- Endpoint di Amministrazione / Governance ---


@app.get("/config/model", response_model=ModelConfig, tags=["Admin & Config"])
async def get_model_config(model_settings: ModelConfig = Depends(get_model_settings)):
    """Restituisce la configurazione del modello attualmente in uso dal file YAML."""
    return model_settings


@app.put("/config/model", response_model=ModelConfig, tags=["Admin & Config"])
async def update_model_config(config: ModelConfig, api_key: str = Depends(get_api_key)):
    """
    Aggiorna il file di configurazione del modello (richiede API Key).
    Questa operazione sovrascrive model_config.yaml e ricarica la configurazione
    per tutti i processi successivi senza riavviare il server.
    """
    try:
        with open("rlcf_framework/model_config.yaml", "w") as f:
            yaml.dump(config.dict(), f, sort_keys=False, indent=2)

        # Ricarica la configurazione globale per renderla subito attiva
        from . import config

        config.model_settings = load_model_config()

        return config.model_settings
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to write or reload config: {e}"
        )


@app.get("/config/tasks", response_model=TaskConfig, tags=["Admin & Config"])
async def get_task_config(task_settings: TaskConfig = Depends(get_task_settings)):
    """Restituisce la configurazione dei task attualmente in uso dal file YAML."""
    return task_settings


@app.put("/config/tasks", response_model=TaskConfig, tags=["Admin & Config"])
async def update_task_config(config: TaskConfig, api_key: str = Depends(get_api_key)):
    """
    Aggiorna il file di configurazione dei task (richiede API Key).
    Questa operazione sovrascrive task_config.yaml e ricarica la configurazione
    per tutti i processi successivi senza riavviare il server.
    """
    try:
        with open("rlcf_framework/task_config.yaml", "w") as f:
            yaml.dump(config.dict(), f, sort_keys=False, indent=2)

        # Ricarica la configurazione globale per renderla subito attiva
        from . import config

        config.task_settings = load_task_config()

        return config.task_settings
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to write or reload config: {e}"
        )


@app.post("/users/", response_model=schemas.User, tags=["Users"])
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = models.User(username=user.username)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@app.get("/users/all", response_model=list[schemas.User], tags=["Database Viewer"])
async def get_all_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User))
    users = result.scalars().all()
    # Convert to dict to avoid lazy loading issues
    return [
        {
            "id": user.id,
            "username": user.username,
            "authority_score": user.authority_score,
            "track_record_score": user.track_record_score,
            "baseline_credential_score": user.baseline_credential_score,
            "credentials": []  # Empty to avoid async issues
        }
        for user in users
    ]


@app.get("/users/{user_id}", response_model=schemas.User, tags=["Users"])
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).filter(models.User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Convert to dict to avoid lazy loading issues
    return {
        "id": user.id,
        "username": user.username,
        "authority_score": user.authority_score,
        "track_record_score": user.track_record_score,
        "baseline_credential_score": user.baseline_credential_score,
        "credentials": []  # Empty to avoid async issues
    }


@app.post("/users/{user_id}/credentials/", response_model=schemas.User, tags=["Users"])
async def add_credential_to_user(
    user_id: int,
    credential: schemas.CredentialCreate,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(models.User)
        .options(selectinload(models.User.credentials))
        .filter(models.User.id == user_id)
    )
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_credential = models.Credential(**credential.dict(), user_id=user_id)
    db.add(db_credential)
    await db.commit()

    await authority_module.calculate_baseline_credentials(db, user_id)
    await db.refresh(db_user)
    return db_user


@app.post("/tasks/", response_model=schemas.LegalTask, tags=["Tasks"])
async def create_legal_task(
    task: schemas.LegalTaskCreate, db: AsyncSession = Depends(get_db)
):
    db_task = models.LegalTask(
        task_type=task.task_type.value, 
        input_data=task.input_data,
        status=models.TaskStatus.BLIND_EVALUATION.value
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    # Try to generate realistic AI response, fallback to placeholder if needed
    try:
        # Default model config for now - TODO: make configurable
        default_model_config = AIModelConfig(
            name="openai/gpt-3.5-turbo",
            api_key=os.getenv("OPENROUTER_API_KEY", ""),
            temperature=0.7
        )
        
        if default_model_config.api_key:
            ai_response_data = await openrouter_service.generate_response(
                task.task_type.value, 
                task.input_data, 
                default_model_config
            )
        else:
            # Fallback to placeholder if no API key
            ai_response_data = {
                "message": f"AI response placeholder for {task.task_type.value} (no API key configured)",
                "task_type": task.task_type.value,
                "is_placeholder": True
            }
    except Exception as e:
        logger.warning(f"Failed to generate AI response: {e}")
        ai_response_data = {
            "message": f"AI response placeholder for {task.task_type.value} (generation failed)",
            "task_type": task.task_type.value,
            "error": str(e),
            "is_placeholder": True
        }
    
    db_response = models.Response(
        task_id=db_task.id, 
        output_data=ai_response_data, 
        model_version=ai_response_data.get("model_name", "placeholder-1.0")
    )
    db.add(db_response)
    await db.commit()
    await db.refresh(db_task, attribute_names=["responses"])
    for response in db_task.responses:
        await db.refresh(response, attribute_names=["feedback"])

    return db_task


@app.get("/tasks/all", tags=["Database Viewer"])
async def get_all_tasks(
    limit: int = Query(None, description="Limit number of results"),
    status: str = Query(None, description="Filter by task status"),
    task_type: str = Query(None, description="Filter by task type"),
    offset: int = Query(None, description="Offset for pagination"),
    user_id: int = Query(None, description="Filter by user ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get all tasks with optional filtering and pagination."""
    query = select(models.LegalTask)
    
    # Apply filters
    if status:
        query = query.filter(models.LegalTask.status == status)
    if task_type:
        query = query.filter(models.LegalTask.task_type == task_type)
    
    # Apply ordering for consistent pagination
    query = query.order_by(models.LegalTask.created_at.desc())
    
    # Apply pagination
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    # Convert to dict to avoid lazy loading issues and ensure consistent response
    return [
        {
            "id": task.id,
            "task_type": task.task_type,
            "input_data": task.input_data,
            "ground_truth_data": task.ground_truth_data,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "responses": []  # Empty to avoid async issues
        }
        for task in tasks
    ]


@app.get("/tasks/{task_id}", response_model=schemas.LegalTask, tags=["Tasks"])
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single task by ID."""
    result = await db.execute(
        select(models.LegalTask)
        .options(selectinload(models.LegalTask.responses))
        .filter(models.LegalTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/tasks/{task_id}", response_model=schemas.LegalTask, tags=["Tasks"])
async def update_task(
    task_id: int,
    task_update: schemas.LegalTaskCreate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Update a task."""
    result = await db.execute(select(models.LegalTask).filter(models.LegalTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.task_type = task_update.task_type.value
    task.input_data = task_update.input_data
    
    await db.commit()
    await db.refresh(task)
    return task


@app.put("/tasks/{task_id}/status", tags=["Tasks"])
async def update_task_status(
    task_id: int,
    status_update: dict,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Update task status."""
    result = await db.execute(select(models.LegalTask).filter(models.LegalTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    new_status = status_update.get("status")
    if new_status not in [status.value for status in models.TaskStatus]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    task.status = new_status
    await db.commit()
    
    return {"message": f"Task {task_id} status updated to {new_status}"}


@app.delete("/tasks/{task_id}", tags=["Tasks"])
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Delete a task."""
    result = await db.execute(select(models.LegalTask).filter(models.LegalTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(task)
    await db.commit()
    
    return {"message": f"Task {task_id} deleted successfully"}


@app.post("/tasks/bulk_delete", tags=["Tasks"])
async def bulk_delete_tasks(
    task_ids: dict,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Delete multiple tasks."""
    ids = task_ids.get("task_ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="No task IDs provided")
    
    result = await db.execute(
        select(models.LegalTask).filter(models.LegalTask.id.in_(ids))
    )
    tasks = result.scalars().all()
    
    for task in tasks:
        await db.delete(task)
    
    await db.commit()
    
    return {"message": f"Deleted {len(tasks)} tasks", "deleted_count": len(tasks)}


@app.post("/tasks/bulk_update_status", tags=["Tasks"])
async def bulk_update_task_status(
    update_data: dict,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Update status of multiple tasks."""
    task_ids = update_data.get("task_ids", [])
    new_status = update_data.get("status")
    
    if not task_ids:
        raise HTTPException(status_code=400, detail="No task IDs provided")
    
    if new_status not in [status.value for status in models.TaskStatus]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.execute(
        select(models.LegalTask).filter(models.LegalTask.id.in_(task_ids))
    )
    tasks = result.scalars().all()
    
    for task in tasks:
        task.status = new_status
    
    await db.commit()
    
    return {
        "message": f"Updated {len(tasks)} tasks to status {new_status}",
        "updated_count": len(tasks)
    }


@app.post("/tasks/update_open_to_evaluation", tags=["Tasks"])
async def update_open_tasks_to_evaluation(
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Utility endpoint to update all OPEN tasks to BLIND_EVALUATION status."""
    result = await db.execute(
        select(models.LegalTask).filter(models.LegalTask.status == models.TaskStatus.OPEN.value)
    )
    open_tasks = result.scalars().all()
    
    for task in open_tasks:
        task.status = models.TaskStatus.BLIND_EVALUATION.value
    
    await db.commit()
    
    return {
        "message": f"Updated {len(open_tasks)} OPEN tasks to BLIND_EVALUATION status",
        "updated_count": len(open_tasks)
    }


@app.post("/tasks/{task_id}/assign", response_model=schemas.TaskAssignment, tags=["Tasks"])
async def assign_task_to_user(
    task_id: int,
    assignment: schemas.TaskAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    # Validate task
    result = await db.execute(select(models.LegalTask).filter(models.LegalTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Validate user
    result = await db.execute(select(models.User).filter(models.User.id == assignment.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_assignment = models.TaskAssignment(
        task_id=task_id,
        user_id=assignment.user_id,
        role=assignment.role,
    )
    db.add(db_assignment)
    await db.commit()
    await db.refresh(db_assignment)

    return db_assignment


@app.get("/tasks/{task_id}/assignees", response_model=list[schemas.TaskAssignment], tags=["Tasks"])
async def list_task_assignees(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.TaskAssignment).filter(models.TaskAssignment.task_id == task_id)
    )
    return result.scalars().all()


@app.post("/users/bulk", response_model=list[schemas.User], tags=["Users"])
async def create_users_bulk(
    payload: schemas.BulkUserCreate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    created = []
    for username in payload.usernames:
        db_user = models.User(username=username)
        db.add(db_user)
        await db.flush()
        created.append(db_user)
    await db.commit()
    # Return as plain dicts to avoid lazy relationship loading
    return [
        {
            "id": u.id,
            "username": u.username,
            "authority_score": u.authority_score,
            "track_record_score": u.track_record_score,
            "baseline_credential_score": u.baseline_credential_score,
            "credentials": [],
        }
        for u in created
    ]

@app.post(
    "/tasks/batch_from_yaml/", response_model=List[schemas.LegalTask], tags=["Tasks"]
)
async def create_legal_tasks_from_yaml(
    yaml_content: str,
    db: AsyncSession = Depends(get_db),
    task_settings: TaskConfig = Depends(get_task_settings),
    api_key: str = Depends(get_api_key),  # Richiede API Key per sicurezza
):
    """
    Crea uno o più task legali da un contenuto YAML fornito.
    Il YAML deve contenere una lista di task, ognuno con 'task_type' e 'input_data'.
    """
    try:
        data = yaml.safe_load(yaml_content)
        tasks_data = schemas.TaskListFromYaml(tasks=data.get("tasks", [])).tasks
    except (yaml.YAMLError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML or data format: {e}")

    created_tasks = []
    for task_data in tasks_data:
        try:
            # Validate input_data using the existing LegalTaskCreate schema's validator
            validated_task_data = schemas.LegalTaskCreate(
                task_type=task_data.task_type, input_data=task_data.input_data
            )

            # Separate input_data and ground_truth_data based on task_config
            task_type_enum = TaskType(task_data.task_type)
            task_type_config = task_settings.task_types.get(task_type_enum.value)

            input_data_for_db = {}
            ground_truth_data_for_db = {}

            if task_type_config and task_type_config.ground_truth_keys:
                for key, value in task_data.input_data.items():
                    if key in task_type_config.ground_truth_keys:
                        ground_truth_data_for_db[key] = value
                    else:
                        input_data_for_db[key] = value
            else:
                input_data_for_db = (
                    task_data.input_data
                )  # If no ground_truth_keys, all is input

            db_task = models.LegalTask(
                task_type=validated_task_data.task_type.value,
                input_data=input_data_for_db,
                ground_truth_data=(
                    ground_truth_data_for_db if ground_truth_data_for_db else None
                ),
                status=models.TaskStatus.BLIND_EVALUATION.value,
            )
            db.add(db_task)
            await db.flush()  # Flush to get the task ID before creating response

            # Create a dummy response with flexible output_data
            dummy_output_data = {
                "message": "AI response placeholder for " + db_task.task_type
            }
            db_response = models.Response(
                task_id=db_task.id,
                output_data=dummy_output_data,
                model_version="dummy-0.1",
            )
            db.add(db_response)

            await db.refresh(db_task)
            created_tasks.append(db_task)
        except ValidationError as e:
            await db.rollback()  # Rollback any partial changes for this task
            raise HTTPException(
                status_code=422, detail=f"Validation error for a task: {e}"
            )
        except Exception as e:
            await db.rollback()  # Rollback any partial changes for this task
            raise HTTPException(status_code=500, detail=f"Error processing task: {e}")

    await db.commit()
    return created_tasks


def detect_task_type_from_csv(df: pd.DataFrame) -> str:
    """
    Auto-detect task type from CSV columns.
    """
    columns = set(df.columns.str.lower())
    
    # STATUTORY_RULE_QA detection
    if {'question', 'answer_text', 'context_full'}.issubset(columns):
        return "STATUTORY_RULE_QA"
    
    # QA detection
    if {'question', 'context'}.issubset(columns) and 'answer' in ' '.join(columns):
        return "QA"
    
    # CLASSIFICATION detection
    if {'text', 'labels'}.issubset(columns) or {'text', 'category'}.issubset(columns):
        return "CLASSIFICATION"
    
    # SUMMARIZATION detection
    if {'document', 'summary'}.issubset(columns) or {'text', 'summary'}.issubset(columns):
        return "SUMMARIZATION"
    
    # Default fallback
    return "QA"


def csv_to_tasks_data(df: pd.DataFrame, task_type: str, task_settings: TaskConfig) -> List[Dict]:
    """
    Convert CSV DataFrame to tasks data based on task type.
    """
    tasks_data = []
    
    if task_type == "STATUTORY_RULE_QA":
        for _, row in df.iterrows():
            input_data = {}
            
            # Map all columns from the dataset to the expected schema
            column_mapping = {
                'id': 'id',
                'question': 'question', 
                'rule_id': 'rule_id',
                'context_full': 'context_full',
                'context_count': 'context_count',
                'relevant_articles': 'relevant_articles',
                'tags': 'tags',
                'category': 'category',
                'metadata_full': 'metadata_full',
                'answer_text': 'answer_text'  # This will be moved to ground truth
            }
            
            # Add all available columns with proper type conversion
            for csv_col, schema_col in column_mapping.items():
                if csv_col in row and pd.notna(row[csv_col]):
                    value = row[csv_col]
                    # Convert context_count to int if possible
                    if schema_col == 'context_count':
                        try:
                            input_data[schema_col] = int(value) if pd.notna(value) else 0
                        except (ValueError, TypeError):
                            input_data[schema_col] = 0
                    else:
                        input_data[schema_col] = str(value).strip()
                
            # Set defaults for missing required fields
            if 'id' not in input_data:
                input_data['id'] = f"generated_{len(tasks_data)}"
            if 'rule_id' not in input_data:
                input_data['rule_id'] = ""
            if 'context_full' not in input_data:
                input_data['context_full'] = ""
            if 'context_count' not in input_data:
                input_data['context_count'] = 1
            if 'relevant_articles' not in input_data:
                input_data['relevant_articles'] = ""
            if 'tags' not in input_data:
                input_data['tags'] = ""
            if 'category' not in input_data:
                input_data['category'] = ""
            if 'metadata_full' not in input_data:
                input_data['metadata_full'] = ""
            
            # Ensure we have minimum required fields
            if 'question' in input_data and input_data['question']:
                tasks_data.append({
                    "task_type": task_type,
                    "input_data": input_data
                })
    
    elif task_type == "QA":
        for _, row in df.iterrows():
            input_data = {}
            
            # Map common column names
            if 'question' in row and pd.notna(row['question']):
                input_data['question'] = str(row['question']).strip()
            
            if 'context' in row and pd.notna(row['context']):
                input_data['context'] = str(row['context']).strip()
            elif 'context_full' in row and pd.notna(row['context_full']):
                input_data['context'] = str(row['context_full']).strip()
            
            # Add answer as ground truth
            for answer_col in ['answer', 'answers', 'answer_text']:
                if answer_col in row and pd.notna(row[answer_col]):
                    input_data['answers'] = str(row[answer_col]).strip()
                    break
            
            if 'question' in input_data:
                tasks_data.append({
                    "task_type": task_type,
                    "input_data": input_data
                })
    
    elif task_type == "CLASSIFICATION":
        for _, row in df.iterrows():
            input_data = {}
            
            if 'text' in row and pd.notna(row['text']):
                input_data['text'] = str(row['text']).strip()
            
            # Handle labels
            for label_col in ['labels', 'category', 'categories']:
                if label_col in row and pd.notna(row[label_col]):
                    labels_str = str(row[label_col]).strip()
                    # Split by common separators
                    if ',' in labels_str:
                        input_data['labels'] = [l.strip() for l in labels_str.split(',')]
                    elif ';' in labels_str:
                        input_data['labels'] = [l.strip() for l in labels_str.split(';')]
                    else:
                        input_data['labels'] = [labels_str]
                    break
            
            if 'text' in input_data:
                tasks_data.append({
                    "task_type": task_type,
                    "input_data": input_data
                })
    
    return tasks_data


@app.post("/tasks/upload_csv/", tags=["Tasks"])
async def upload_csv_tasks(
    file: UploadFile = File(...),
    task_type: str = Query(None, description="Override task type detection"),
    db: AsyncSession = Depends(get_db),
    task_settings: TaskConfig = Depends(get_task_settings),
    api_key: str = Depends(get_api_key),
):
    """
    Upload tasks from CSV file with automatic task type detection.
    
    The endpoint will:
    1. Auto-detect task type from CSV columns if not specified
    2. Convert CSV rows to appropriate task format
    3. Separate input_data from ground_truth_data based on task config
    4. Create tasks in the database
    """
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    try:
        logger.info(f"Starting CSV upload for file: {file.filename}")
        
        # Read CSV content
        content = await file.read()
        logger.debug(f"File size: {len(content)} bytes")
        
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        logger.debug(f"CSV loaded with {len(df)} rows and columns: {list(df.columns)}")
        
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        # Auto-detect task type if not provided
        if not task_type:
            task_type = detect_task_type_from_csv(df)
            logger.info(f"Auto-detected task type: {task_type}")
        
        # Validate task type
        try:
            task_type_enum = TaskType(task_type)
            logger.debug(f"Task type enum validated: {task_type_enum}")
        except ValueError:
            logger.error(f"Invalid task type: {task_type}")
            raise HTTPException(status_code=400, detail=f"Invalid task type: {task_type}")
        
        # Convert CSV to tasks data
        logger.debug("Converting CSV to tasks data...")
        tasks_data = csv_to_tasks_data(df, task_type, task_settings)
        logger.info(f"Converted {len(tasks_data)} tasks from CSV")
        
        if not tasks_data:
            raise HTTPException(status_code=400, detail="No valid tasks found in CSV")
        
        # Create tasks using existing logic
        created_tasks = []
        for task_data in tasks_data:
            try:
                # Validate using existing schema
                validated_task_data = schemas.LegalTaskCreate(
                    task_type=TaskType(task_data["task_type"]), 
                    input_data=task_data["input_data"]
                )
                
                # Separate input and ground truth data
                task_type_config = task_settings.task_types.get(task_type_enum.value)
                input_data_for_db = {}
                ground_truth_data_for_db = {}
                
                if task_type_config and task_type_config.ground_truth_keys:
                    for key, value in task_data["input_data"].items():
                        if key in task_type_config.ground_truth_keys:
                            ground_truth_data_for_db[key] = value
                        else:
                            input_data_for_db[key] = value
                else:
                    input_data_for_db = task_data["input_data"]
                
                # Create task with BLIND_EVALUATION status
                db_task = models.LegalTask(
                    task_type=validated_task_data.task_type.value,
                    input_data=input_data_for_db,
                    ground_truth_data=ground_truth_data_for_db if ground_truth_data_for_db else None,
                    status=models.TaskStatus.BLIND_EVALUATION.value,
                )
                db.add(db_task)
                await db.flush()
                
                # Generate AI response or fallback to placeholder
                try:
                    default_model_config = AIModelConfig(
                        name="openai/gpt-3.5-turbo",
                        api_key=os.getenv("OPENROUTER_API_KEY", ""),
                        temperature=0.7
                    )
                    
                    if default_model_config.api_key:
                        ai_response_data = await openrouter_service.generate_response(
                            task_data["task_type"], 
                            input_data_for_db, 
                            default_model_config
                        )
                        model_version = ai_response_data.get("model_name", "csv-upload-ai-1.0")
                    else:
                        ai_response_data = {
                            "message": f"AI response placeholder for {db_task.task_type} (no API key configured)",
                            "task_type": db_task.task_type,
                            "is_placeholder": True
                        }
                        model_version = "csv-upload-placeholder-1.0"
                except Exception as e:
                    logger.warning(f"Failed to generate AI response for CSV task: {e}")
                    ai_response_data = {
                        "message": f"AI response placeholder for {db_task.task_type} (generation failed)",
                        "task_type": db_task.task_type,
                        "error": str(e),
                        "is_placeholder": True
                    }
                    model_version = "csv-upload-fallback-1.0"
                
                db_response = models.Response(
                    task_id=db_task.id,
                    output_data=ai_response_data,
                    model_version=model_version,
                )
                db.add(db_response)
                
                await db.refresh(db_task)
                
                # Prepare task data to avoid lazy loading issues
                task_data = {
                    "id": db_task.id,
                    "task_type": db_task.task_type,
                    "input_data": db_task.input_data,
                    "ground_truth_data": db_task.ground_truth_data,
                    "status": db_task.status,
                    "created_at": db_task.created_at,
                    "responses": []  # Empty for now since they are just placeholders
                }
                created_tasks.append(task_data)
                
            except Exception as e:
                logger.error(f"Error processing task data: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                await db.rollback()
                raise HTTPException(status_code=422, detail=f"Error processing row: {str(e)}")
        
        await db.commit()
        logger.info(f"Successfully created {len(created_tasks)} tasks")
        
        return created_tasks
        
    except pd.errors.EmptyDataError:
        logger.error("CSV file is empty or invalid")
        raise HTTPException(status_code=400, detail="CSV file is empty or invalid")
    except pd.errors.ParserError as e:
        logger.error(f"CSV parsing error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"CSV parsing error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected server error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.post("/tasks/csv_to_yaml/", tags=["Tasks"])
async def convert_csv_to_yaml(
    file: UploadFile = File(...),
    task_type: str = Query(None, description="Override task type detection"),
    max_records: int = Query(None, description="Limit number of records to convert"),
    task_settings: TaskConfig = Depends(get_task_settings),
    api_key: str = Depends(get_api_key),
):
    """
    Convert CSV file to YAML format for RLCF framework without creating tasks.
    Useful for preview or offline processing.
    """
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV file")
    
    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        if max_records:
            df = df.head(max_records)
        
        # Auto-detect task type if not provided
        if not task_type:
            task_type = detect_task_type_from_csv(df)
        
        # Convert to tasks data
        tasks_data = csv_to_tasks_data(df, task_type, task_settings)
        
        if not tasks_data:
            raise HTTPException(status_code=400, detail="No valid tasks found in CSV")
        
        # Create YAML structure
        yaml_data = {
            "tasks": tasks_data,
            "metadata": {
                "source": file.filename,
                "total_tasks": len(tasks_data),
                "detected_task_type": task_type,
                "description": f"Converted from {file.filename}"
            }
        }
        
        # Convert to YAML string
        yaml_output = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True, indent=2)
        
        return Response(
            content=yaml_output,
            media_type="application/x-yaml",
            headers={"Content-Disposition": f"attachment; filename={file.filename.replace('.csv', '.yaml')}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")


# --- New GET Endpoints for Database Viewer ---
@app.get(
    "/credentials/all",
    response_model=list[schemas.Credential],
    tags=["Database Viewer"],
)
async def get_all_credentials(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Credential))
    return result.scalars().all()


@app.get("/responses/all", response_model=list[schemas.Response], tags=["Database Viewer"])
async def get_all_responses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Response))
    responses = result.scalars().all()
    # Convert to dict to avoid lazy loading issues
    return [
        {
            "id": response.id,
            "task_id": response.task_id,
            "output_data": response.output_data,
            "model_version": response.model_version,
            "generated_at": response.generated_at,
            "feedback": []  # Empty to avoid async issues
        }
        for response in responses
    ]


@app.get(
    "/feedback/all", response_model=list[schemas.Feedback], tags=["Database Viewer"]
)
async def get_all_feedback(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Feedback))
    return result.scalars().all()


@app.get(
    "/feedback_ratings/all",
    response_model=list[schemas.FeedbackRating],
    tags=["Database Viewer"],
)
async def get_all_feedback_ratings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.FeedbackRating))
    return result.scalars().all()


@app.get(
    "/bias_reports/all",
    response_model=list[schemas.BiasReport],
    tags=["Database Viewer"],
)
async def get_all_bias_reports(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.BiasReport))
    return result.scalars().all()


@app.get(
    "/assignments/all",
    response_model=list[schemas.TaskAssignment],
    tags=["Database Viewer"],
)
async def get_all_assignments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.TaskAssignment))
    return result.scalars().all()


@app.get("/analytics/system", response_model=schemas.SystemMetrics, tags=["Analytics"])
async def get_system_metrics(db: AsyncSession = Depends(get_db)):
    """Calcola e restituisce le metriche di sistema reali."""
    total_tasks_query = select(func.count(models.LegalTask.id))
    total_users_query = select(func.count(models.User.id))
    total_feedback_query = select(func.count(models.Feedback.id))
    
    active_evaluations_query = select(func.count(models.LegalTask.id)).filter(
        models.LegalTask.status == models.TaskStatus.BLIND_EVALUATION.value
    )
    
    completed_tasks_query = select(func.count(models.LegalTask.id)).filter(
        models.LegalTask.status.in_([
            models.TaskStatus.AGGREGATED.value,
            models.TaskStatus.CLOSED.value
        ])
    )

    avg_consistency_query = select(func.avg(models.Feedback.consistency_score)).filter(
        models.Feedback.consistency_score.isnot(None)
    )

    total_tasks = (await db.execute(total_tasks_query)).scalar_one_or_none() or 0
    total_users = (await db.execute(total_users_query)).scalar_one_or_none() or 0
    total_feedback = (await db.execute(total_feedback_query)).scalar_one_or_none() or 0
    active_evaluations = (await db.execute(active_evaluations_query)).scalar_one_or_none() or 0
    completed_tasks = (await db.execute(completed_tasks_query)).scalar_one_or_none() or 0
    avg_consistency = (await db.execute(avg_consistency_query)).scalar_one_or_none() or 0.0

    completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0

    return {
        "totalTasks": total_tasks,
        "totalUsers": total_users,
        "totalFeedback": total_feedback,
        "averageConsensus": avg_consistency,
        "activeEvaluations": active_evaluations,
        "completionRate": completion_rate,
    }

@app.get("/analytics/leaderboard", response_model=List[schemas.User], tags=["Analytics"])
async def get_leaderboard(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Restituisce la classifica degli utenti con il punteggio di autorità più alto."""
    result = await db.execute(
        select(models.User)
        .options(selectinload(models.User.credentials))
        .order_by(models.User.authority_score.desc())
        .limit(limit)
    )
    return result.scalars().all()

@app.get("/analytics/task_distribution", response_model=Dict[str, int], tags=["Analytics"])
async def get_task_distribution(db: AsyncSession = Depends(get_db)):
    """Restituisce la distribuzione dei task per tipo."""
    result = await db.execute(
        select(models.LegalTask.task_type, func.count(models.LegalTask.id))
        .group_by(models.LegalTask.task_type)
    )
    return {task_type: count for task_type, count in result.all()}


@app.post("/export/dataset", tags=["Admin & Config"])
async def export_dataset_endpoint(
    export_request: schemas.ExportRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    """Esporta un dataset in formato JSONL."""
    records = await export_dataset.get_export_data(
        db, export_request.task_type, export_request.export_format
    )

    if not records:
        raise HTTPException(status_code=404, detail="No data found for the given criteria.")

    # Convert records to JSONL format
    jsonl_content = "\n".join(json.dumps(record) for record in records)

    return Response(
        content=jsonl_content,
        media_type="application/jsonl",
        headers={
            "Content-Disposition": f'attachment; filename="{export_request.task_type.value}_{export_request.export_format}.jsonl"'
        },
    )


@app.post(
    "/responses/{response_id}/feedback/",
    response_model=schemas.Feedback,
    tags=["Feedback"],
)
async def submit_feedback(
    response_id: int,
    feedback: schemas.FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    task_settings: TaskConfig = Depends(get_task_settings),
):
    result = await db.execute(
        select(models.Response)
        .options(selectinload(models.Response.task))
        .filter(models.Response.id == response_id)
    )
    db_response = result.scalar_one_or_none()
    if not db_response:
        raise HTTPException(status_code=404, detail="Response not found")

    if db_response.task.status != models.TaskStatus.BLIND_EVALUATION.value:
        raise HTTPException(
            status_code=403,
            detail=f"Feedback can only be submitted during the BLIND_EVALUATION phase. Current status: {db_response.task.status}",
        )

    db_feedback = models.Feedback(
        **feedback.dict(exclude={"feedback_data"}),
        feedback_data=feedback.feedback_data,
        response_id=response_id,
    )
    db.add(db_feedback)
    await db.commit()
    await db.refresh(db_feedback)

    # Dynamic validation of feedback_data based on task_type
    task_type_enum = TaskType(db_response.task.task_type)
    feedback_schema_def = task_settings.task_types.get(task_type_enum.value)

    if feedback_schema_def and feedback_schema_def.feedback_data:
        fields = {
            field_name: (schemas._parse_type_string(type_str), ...)
            for field_name, type_str in feedback_schema_def.feedback_data.items()
        }
        DynamicFeedbackModel = create_model(
            f"{task_type_enum.value}FeedbackData", **fields
        )
        try:
            DynamicFeedbackModel.model_validate(feedback.feedback_data)
        except ValidationError as e:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid feedback_data for task_type {task_type_enum.value}: {e}",
            )

    quality_score = await authority_module.calculate_quality_score(db, db_feedback)
    await authority_module.update_track_record(db, feedback.user_id, quality_score)

    return db_feedback


@app.get("/tasks/{task_id}/result/", tags=["Tasks"])
async def get_task_result(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await aggregation_engine.aggregate_with_uncertainty(db, task_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post(
    "/feedback/{feedback_id}/rate/",
    response_model=schemas.FeedbackRating,
    tags=["Feedback"],
)
async def rate_feedback(
    feedback_id: int,
    rating: schemas.FeedbackRatingCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Feedback).filter(models.Feedback.id == feedback_id)
    )
    db_feedback = result.scalar_one_or_none()
    if not db_feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")

    db_rating = models.FeedbackRating(**rating.dict(), feedback_id=feedback_id)
    db.add(db_rating)
    await db.commit()
    await db.refresh(db_rating)

    result = await db.execute(
        select(models.FeedbackRating.helpfulness_score).filter(
            models.FeedbackRating.feedback_id == feedback_id
        )
    )
    ratings = result.scalars().all()
    avg_rating = numpy.mean([r for r in ratings])
    db_feedback.community_helpfulness_rating = int(round(avg_rating))
    await db.commit()

    return db_rating


@app.put(
    "/tasks/{task_id}/status", response_model=schemas.LegalTask, tags=["Admin & Config"]
)
async def update_task_status(
    task_id: int,
    payload: schemas.TaskStatusUpdate, # Usa un modello Pydantic per il corpo della richiesta
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(get_api_key),
):
    result = await db.execute(
        select(models.LegalTask).filter(models.LegalTask.id == task_id)
    )
    db_task = result.scalar_one_or_none()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    if (
        payload.status == TaskStatus.AGGREGATED
        and db_task.status == TaskStatus.BLIND_EVALUATION.value
    ):
        await services.task_service.orchestrate_task_aggregation(db, task_id)

    db_task.status = payload.status.value
    await db.commit()
    # Ricarica il task con le relazioni per evitare errori di lazy loading nella risposta
    await db.refresh(db_task, attribute_names=["responses"]) 
    for response in db_task.responses:
        await db.refresh(response, attribute_names=["feedback"])
    return db_task


@app.get("/tasks/{task_id}/devils-advocate", tags=["Devil's Advocate"])
async def get_devils_advocate_assignment(task_id: int, db: AsyncSession = Depends(get_db)):
    """Check if there are any Devil's Advocate assignments for this task."""
    result = await db.execute(
        select(models.DevilsAdvocateAssignment)
        .filter(models.DevilsAdvocateAssignment.task_id == task_id)
    )
    assignments = result.scalars().all()
    
    if not assignments:
        return {"assigned": False, "advocates": []}
    
    # Convert to simple dict format
    advocates = []
    for assignment in assignments:
        advocates.append({
            "user_id": assignment.user_id,
            "instructions": assignment.instructions,
            "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None
        })
    
    return {
        "assigned": True,
        "advocates": advocates,
        "count": len(advocates)
    }


@app.get("/devils-advocate/prompts/{task_type}", tags=["Devil's Advocate"])
async def get_devils_advocate_prompts(task_type: str):
    """Get Devil's Advocate prompts for a specific task type."""
    from .devils_advocate import DevilsAdvocateAssigner
    
    assigner = DevilsAdvocateAssigner()
    prompts = assigner.generate_critical_prompts(task_type)
    
    return {
        "task_type": task_type,
        "prompts": prompts,
        "count": len(prompts)
    }


@app.post("/ai/generate_response", tags=["AI Service"])
async def generate_ai_response(
    request: dict,
    api_key: str = Depends(get_api_key),
):
    """
    Generate AI response for a specific task input using OpenRouter.
    
    Request body:
    {
        "task_type": "STATUTORY_RULE_QA",
        "input_data": {...},
        "model_config": {
            "name": "openai/gpt-4",
            "api_key": "sk-...",
            "temperature": 0.7
        }
    }
    """
    try:
        task_type = request.get("task_type")
        input_data = request.get("input_data")
        model_config_data = request.get("model_config")
        
        if not all([task_type, input_data, model_config_data]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        model_config = AIModelConfig(
            name=model_config_data.get("name", "openai/gpt-3.5-turbo"),
            api_key=model_config_data.get("api_key"),
            temperature=model_config_data.get("temperature", 0.7),
            max_tokens=model_config_data.get("max_tokens", 1000)
        )
        
        if not model_config.api_key:
            raise HTTPException(status_code=400, detail="API key is required")
        
        response_data = await openrouter_service.generate_response(
            task_type, input_data, model_config
        )
        
        return {
            "success": True,
            "response_data": response_data,
            "model_used": model_config.name
        }
        
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@app.get("/ai/models", tags=["AI Service"])
async def get_available_models():
    """Get list of available AI models from OpenRouter."""
    return {
        "models": [
            {
                "id": "openai/gpt-4",
                "name": "GPT-4",
                "description": "Most capable OpenAI model",
                "recommended_for": ["complex_legal_analysis", "statutory_interpretation"]
            },
            {
                "id": "openai/gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "description": "Fast and capable for most legal tasks",
                "recommended_for": ["qa", "classification", "summarization"]
            },
            {
                "id": "anthropic/claude-3-sonnet",
                "name": "Claude 3 Sonnet",
                "description": "Excellent for legal reasoning and analysis",
                "recommended_for": ["legal_reasoning", "risk_assessment", "drafting"]
            },
            {
                "id": "anthropic/claude-3-haiku",
                "name": "Claude 3 Haiku",
                "description": "Fast and efficient for simple tasks",
                "recommended_for": ["classification", "quick_qa"]
            },
            {
                "id": "meta-llama/llama-3-70b-instruct",
                "name": "Llama 3 70B Instruct",
                "description": "Open-source alternative with good performance",
                "recommended_for": ["general_legal_tasks"]
            }
        ]
    }
