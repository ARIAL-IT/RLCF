from fastapi import FastAPI, Depends, HTTPException, Security, Query, Response
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
        task_type=task.task_type.value, input_data=task.input_data
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)

    # Create a dummy response with flexible output_data
    # In a real scenario, this would come from an AI model
    dummy_output_data = {
        "message": "AI response placeholder for " + task.task_type.value
    }
    db_response = models.Response(
        task_id=db_task.id, output_data=dummy_output_data, model_version="dummy-0.1"
    )
    db.add(db_response)
    db_task.status = (
        models.TaskStatus.BLIND_EVALUATION.value
    )  # Imposta lo stato iniziale per la valutazione
    await db.commit()
    await db.refresh(db_task, attribute_names=["responses"])
    for response in db_task.responses:
        await db.refresh(response, attribute_names=["feedback"])

    return db_task


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
            db_task.status = (
                models.TaskStatus.BLIND_EVALUATION.value
            )  # Imposta lo stato iniziale per la valutazione

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


# --- New GET Endpoints for Database Viewer ---
@app.get(
    "/credentials/all",
    response_model=list[schemas.Credential],
    tags=["Database Viewer"],
)
async def get_all_credentials(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Credential))
    return result.scalars().all()


@app.get("/tasks/all", response_model=list[schemas.LegalTask], tags=["Database Viewer"])
async def get_all_tasks(
    limit: int = Query(None, description="Limit number of results"),
    status: str = Query(None, description="Filter by task status"),
    db: AsyncSession = Depends(get_db)
):
    query = select(models.LegalTask)
    if status:
        query = query.filter(models.LegalTask.status == status)
    if limit:
        query = query.limit(limit)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    # Convert to dict to avoid lazy loading issues
    return [
        {
            "id": task.id,
            "task_type": task.task_type,
            "input_data": task.input_data,
            "ground_truth_data": task.ground_truth_data,
            "status": task.status,
            "created_at": task.created_at,
            "responses": []  # Empty to avoid async issues
        }
        for task in tasks
    ]


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
