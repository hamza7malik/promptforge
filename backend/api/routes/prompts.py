from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.auth import get_current_user_id
from models.models import User, PromptSuggestion
from schemas.schemas import PromptSuggestionRequest, PromptSuggestionResponse
from services.llm.service import prompt_engineering_service
from core.logging import logger

router = APIRouter()


@router.post("/suggest", response_model=PromptSuggestionResponse, status_code=status.HTTP_201_CREATED)
async def suggest_prompt_improvements(
    request: PromptSuggestionRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get AI-powered prompt improvement suggestions"""
    try:
        # Get user
        user_result = await db.execute(select(User).where(User.auth0_id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            user = User(auth0_id=user_id, email=user_id)
            db.add(user)
            await db.flush()
        
        # Generate suggestions
        result = await prompt_engineering_service.suggest_improvements(
            original_prompt=request.prompt,
            context=request.context
        )
        
        # Save suggestion
        suggestion = PromptSuggestion(
            user_id=user.id,
            original_prompt=request.prompt,
            improved_prompt=result["improved_prompt"],
            improvements=result["improvements"],
            category=result["category"]
        )
        db.add(suggestion)
        await db.commit()
        await db.refresh(suggestion)
        
        logger.info(f"Created prompt suggestion: {suggestion.id}")
        
        return suggestion
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error generating prompt suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions"
        )
