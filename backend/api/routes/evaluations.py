from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.auth import get_current_user_id
from models.models import Message, Evaluation
from schemas.schemas import EvaluationResponse
from services.evaluation.ragas_service import ragas_evaluator
from core.logging import logger

router = APIRouter()


async def evaluate_message_task(message_id: str, db_url: str):
    """Background task to evaluate a message"""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    
    engine = create_async_engine(db_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            # Get message
            msg_result = await db.execute(select(Message).where(Message.id == message_id))
            message = msg_result.scalar_one_or_none()
            
            if not message or message.role != "assistant":
                return
            
            # Get previous user message
            prev_result = await db.execute(
                select(Message)
                .where(
                    Message.conversation_id == message.conversation_id,
                    Message.created_at < message.created_at,
                    Message.role == "user"
                )
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            user_message = prev_result.scalar_one_or_none()
            
            if not user_message:
                return
            
            # Extract contexts
            contexts = [
                chunk["content"]
                for chunk in (message.retrieved_chunks or [])
            ]
            
            if not contexts:
                logger.warning(f"No contexts for message {message_id}, skipping evaluation")
                return
            
            # Run evaluation
            eval_result = await ragas_evaluator.evaluate_response(
                question=user_message.content,
                answer=message.content,
                contexts=contexts
            )
            
            # Save evaluation
            evaluation = Evaluation(
                message_id=message_id,
                groundedness_score=eval_result.get("faithfulness_score"),
                faithfulness_score=eval_result.get("faithfulness_score"),
                answer_correctness_score=eval_result.get("answer_correctness_score"),
                answer_relevancy_score=eval_result.get("answer_relevancy_score"),
                context_precision_score=eval_result.get("context_precision_score"),
                context_recall_score=eval_result.get("context_recall_score"),
                overall_score=eval_result.get("overall_score"),
                evaluation_details=eval_result.get("evaluation_details"),
                status="completed" if not eval_result.get("error") else "failed",
                error_message=eval_result.get("error")
            )
            db.add(evaluation)
            await db.commit()
            
            logger.info(f"Completed evaluation for message: {message_id}")
            
    except Exception as e:
        logger.error(f"Error evaluating message: {e}")
    finally:
        await engine.dispose()


@router.post("/{message_id}", response_model=EvaluationResponse, status_code=status.HTTP_202_ACCEPTED)
async def evaluate_message(
    message_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Trigger evaluation for a message"""
    try:
        # Verify message exists and user has access
        from models.models import User, Conversation
        user_result = await db.execute(select(User).where(User.auth0_id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        msg_result = await db.execute(
            select(Message)
            .join(Conversation)
            .where(Message.id == message_id, Conversation.user_id == user.id)
        )
        message = msg_result.scalar_one_or_none()
        
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        
        # Check if evaluation already exists
        eval_result = await db.execute(
            select(Evaluation).where(Evaluation.message_id == message_id)
        )
        existing_eval = eval_result.scalar_one_or_none()
        
        if existing_eval:
            return existing_eval
        
        # Create pending evaluation
        evaluation = Evaluation(
            message_id=message_id,
            status="pending"
        )
        db.add(evaluation)
        await db.commit()
        await db.refresh(evaluation)
        
        # Trigger background evaluation
        from config.settings import settings
        background_tasks.add_task(
            evaluate_message_task,
            message_id=message_id,
            db_url=settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        )
        
        return evaluation
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error triggering evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger evaluation"
        )


@router.get("/{message_id}", response_model=EvaluationResponse)
async def get_evaluation(
    message_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get evaluation for a message"""
    try:
        from models.models import User, Conversation
        user_result = await db.execute(select(User).where(User.auth0_id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        eval_result = await db.execute(
            select(Evaluation)
            .join(Message)
            .join(Conversation)
            .where(Evaluation.message_id == message_id, Conversation.user_id == user.id)
        )
        evaluation = eval_result.scalar_one_or_none()
        
        if not evaluation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
        
        return evaluation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get evaluation"
        )
