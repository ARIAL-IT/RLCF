#!/usr/bin/env python3
"""
Script di test per il nuovo task type STATUTORY_RULE_QA.

Questo script dimostra come:
1. Convertire un campione di qa_dataset_004.xlsx
2. Caricare i task nel framework RLCF
3. Testare la valutazione e aggregazione
"""

import asyncio
import pandas as pd
import yaml
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

# Importa componenti RLCF
from rlcf_framework.database import SessionLocal
from rlcf_framework import models
from rlcf_framework.task_handlers import get_handler
from rlcf_framework.aggregation_engine import aggregate_with_uncertainty

async def create_test_task(db: AsyncSession):
    """Crea un task di test STATUTORY_RULE_QA."""
    
    # Task di esempio dal dataset
    task_data = {
        "task_type": "STATUTORY_RULE_QA",
        "input_data": {
            "question": "È possibile esprimere dissenso rispetto a una lite tra condominio e singolo condomino?",
            "context_full": "Art. 1132. (Dissenso dei condomini rispetto alle liti). Qualora l'assemblea dei condomini abbia deliberato di promuovere una lite o di resistere a una domanda, il condomino dissenziente, con atto notificato all'amministratore, può separare la propria responsabilità in ordine alle conseguenze della lite per il caso di soccombenza.",
            "relevant_articles": "Articolo 1132 Codice Civile - Dissenso dei condomini rispetto alle liti",
            "category": "Condominio e Comunione"
        },
        "ground_truth_data": {
            "answer_text": "Sì, secondo la giurisprudenza attuale, l'art. 1132 c.c. si applica anche alle liti tra condominio e condomini, purché non si tratti di questioni demandate direttamente all'amministratore."
        }
    }
    
    # Crea il task
    db_task = models.LegalTask(
        task_type=task_data["task_type"],
        input_data=task_data["input_data"],
        ground_truth_data=task_data["ground_truth_data"],
        status=models.TaskStatus.BLIND_EVALUATION
    )
    db.add(db_task)
    await db.flush()
    
    # Crea response di test
    db_response = models.Response(
        task_id=db_task.id,
        output_data={"message": "Test AI response for statutory rule QA"},
        model_version="test-1.0"
    )
    db.add(db_response)
    await db.flush()
    
    return db_task, db_response

async def create_test_users_and_feedback(db: AsyncSession, response: models.Response):
    """Crea utenti di test e feedback per simulare valutazioni."""
    
    # Crea utenti di test con authority diverse
    users_data = [
        {"username": "legal_expert_1", "authority_score": 0.9},
        {"username": "legal_expert_2", "authority_score": 0.8},
        {"username": "junior_lawyer", "authority_score": 0.6},
        {"username": "law_student", "authority_score": 0.4}
    ]
    
    users = []
    for user_data in users_data:
        # Cerca se l'utente esiste già
        from sqlalchemy import select
        result = await db.execute(
            select(models.User).filter(models.User.username == user_data["username"])
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            users.append(existing_user)
        else:
            db_user = models.User(**user_data)
            db.add(db_user)
            await db.flush()
            users.append(db_user)
    
    # Crea feedback di test
    feedback_data = [
        {
            "user": users[0],
            "validated_answer": "Sì, l'art. 1132 si applica anche alle liti interne secondo la giurisprudenza recente.",
            "confidence": "high",
            "position": "correct",
            "reasoning": "La Corte di Appello di Napoli ha stabilito che il dissenso si applica anche ai rapporti interni condominiali.",
            "sources_verified": True
        },
        {
            "user": users[1],
            "validated_answer": "Sì, è possibile esprimere dissenso purché non si tratti di competenze dell'amministratore.",
            "confidence": "high",
            "position": "correct",
            "reasoning": "L'orientamento giurisprudenziale attuale estende l'applicabilità dell'art. 1132.",
            "sources_verified": True
        },
        {
            "user": users[2],
            "validated_answer": "Probabilmente sì, ma ci sono delle limitazioni specifiche.",
            "confidence": "medium",
            "position": "partially_correct",
            "reasoning": "La giurisprudenza non è completamente uniforme su questo punto.",
            "sources_verified": False
        },
        {
            "user": users[3],
            "validated_answer": "Non sono sicuro, la norma parla di liti con terzi.",
            "confidence": "low",
            "position": "incorrect",
            "reasoning": "Il testo dell'articolo sembra riferirsi solo ai rapporti esterni.",
            "sources_verified": False
        }
    ]
    
    feedbacks = []
    for fb_data in feedback_data:
        db_feedback = models.Feedback(
            user_id=fb_data["user"].id,
            response_id=response.id,
            feedback_data={
                "validated_answer": fb_data["validated_answer"],
                "confidence": fb_data["confidence"],
                "position": fb_data["position"],
                "reasoning": fb_data["reasoning"],
                "sources_verified": fb_data["sources_verified"]
            },
            is_blind_phase=True
        )
        db.add(db_feedback)
        feedbacks.append(db_feedback)
    
    await db.flush()
    return users, feedbacks

async def test_aggregation(db: AsyncSession, task: models.LegalTask):
    """Testa l'aggregazione per il task STATUTORY_RULE_QA."""
    
    print("\n🔄 Testing aggregation for STATUTORY_RULE_QA...")
    
    # Ottieni handler
    handler = await get_handler(db, task)
    print(f"✅ Handler obtained: {type(handler).__name__}")
    
    # Testa aggregazione
    result = await handler.aggregate_feedback()
    
    print("\n📊 Aggregation Results:")
    print(f"Consensus Answer: {result.get('consensus_answer', 'N/A')}")
    print(f"Confidence: {result.get('confidence', 'N/A')}")
    print(f"Support Percentage: {result.get('support_percentage', 'N/A')}%")
    print(f"Total Evaluators: {result.get('total_evaluators', 'N/A')}")
    
    if 'confidence_distribution' in result:
        print(f"Confidence Distribution: {result['confidence_distribution']}")
    
    if 'position_distribution' in result:
        print(f"Position Distribution: {result['position_distribution']}")
    
    if 'alternative_answers' in result:
        print(f"Alternative Answers: {len(result['alternative_answers'])}")
        for i, alt in enumerate(result['alternative_answers']):
            print(f"  {i+1}. {alt['answer']} ({alt['support_percentage']}%)")
    
    return result

async def test_consistency_and_correctness(db: AsyncSession, task: models.LegalTask, feedbacks: list):
    """Testa il calcolo di consistency e correctness."""
    
    print("\n🎯 Testing consistency and correctness calculations...")
    
    handler = await get_handler(db, task)
    aggregated_result = await handler.aggregate_feedback()
    
    for feedback in feedbacks:
        # Test consistency
        consistency = handler.calculate_consistency(feedback, aggregated_result)
        
        # Test correctness
        ground_truth = task.ground_truth_data or {}
        correctness = handler.calculate_correctness(feedback, ground_truth)
        
        print(f"\n👤 User: {feedback.author.username}")
        print(f"   Authority: {feedback.author.authority_score}")
        print(f"   Answer: {feedback.feedback_data.get('validated_answer', 'N/A')[:100]}...")
        print(f"   Confidence: {feedback.feedback_data.get('confidence', 'N/A')}")
        print(f"   Position: {feedback.feedback_data.get('position', 'N/A')}")
        print(f"   Consistency Score: {consistency:.3f}")
        print(f"   Correctness Score: {correctness:.3f}")

async def main():
    """Funzione principale di test."""
    
    print("🚀 Starting STATUTORY_RULE_QA Test Suite")
    print("=" * 50)
    
    async with SessionLocal() as db:
        try:
            # 1. Crea task di test
            print("\n1️⃣ Creating test task...")
            task, response = await create_test_task(db)
            print(f"✅ Task created with ID: {task.id}")
            
            # 2. Crea utenti e feedback
            print("\n2️⃣ Creating test users and feedback...")
            users, feedbacks = await create_test_users_and_feedback(db, response)
            print(f"✅ Created {len(users)} users and {len(feedbacks)} feedback entries")
            
            # 3. Commit delle modifiche
            await db.commit()
            
            # Refresh per caricare le relazioni
            await db.refresh(task)
            await db.refresh(response)
            for feedback in feedbacks:
                await db.refresh(feedback, ['author'])
            
            # 4. Testa aggregazione
            aggregation_result = await test_aggregation(db, task)
            
            # 5. Testa consistency e correctness
            await test_consistency_and_correctness(db, task, feedbacks)
            
            # 6. Testa uncertainty preservation
            print("\n🔀 Testing uncertainty preservation...")
            uncertainty_result = await aggregate_with_uncertainty(db, task.id)
            print(f"Uncertainty-aware aggregation completed: {uncertainty_result.get('aggregation_result', {}).get('confidence', 'N/A')}")
            
            print("\n✅ All tests completed successfully!")
            print("🎉 STATUTORY_RULE_QA implementation is working correctly!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(main())