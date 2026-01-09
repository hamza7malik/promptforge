from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List

from core.database import get_db
from core.auth import get_current_user_id
from models.models import User, Agent, GeneratedPrompt, PromptRating
from schemas.schemas import (
    PromptGenerationRequest,
    PromptGenerationResponse,
    SavePromptRequest,
    SavedPrompt,
    PromptRatingRequest,
    PromptRatingResponse,
    PromptListItem
)
from services.prompt_generator.service import prompt_generator
from core.logging import logger

router = APIRouter()


@router.post("/generate", response_model=PromptGenerationResponse)
async def generate_prompt(
    request: PromptGenerationRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a production-ready prompt using RAG
    """
    try:
        # Verify user exists
        user_result = await db.execute(select(User).where(User.auth0_id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Verify agent exists and user owns it
        agent_result = await db.execute(
            select(Agent).where(Agent.id == request.agent_id, Agent.user_id == user.id)
        )
        agent = agent_result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        
        logger.info(f"Generating prompt for feature: {request.feature_name}", agent_id=request.agent_id)
        
        # Generate the prompt
        result = await prompt_generator.generate_prompt(
            agent_id=request.agent_id,
            feature_name=request.feature_name,
            user_story=request.user_story,
            tech_stack=request.tech_stack,
            requirements=request.requirements,
            constraints=request.constraints,
            existing_code_context=request.existing_code_context,
            architecture_style=request.architecture_style,
            include_tests=request.include_tests,
            include_documentation=request.include_documentation,
            include_error_handling=request.include_error_handling
        )
        
        # Create database record
        generated_prompt = GeneratedPrompt(
            user_id=user.id,
            agent_id=request.agent_id,
            title=request.feature_name,
            feature_name=request.feature_name,
            user_story=request.user_story,
            tech_stack=request.tech_stack,
            requirements=request.requirements,
            constraints=request.constraints,
            architecture_style=request.architecture_style,
            existing_code_context=request.existing_code_context,
            generated_prompt=result["generated_prompt"],
            contexts_used=result["contexts_used"],
            confidence_score=result["confidence_score"],
            tokens_count=result["tokens_count"],
            generation_time_ms=result["generation_time_ms"],
            is_saved=False
        )
        
        db.add(generated_prompt)
        await db.commit()
        await db.refresh(generated_prompt)
        
        logger.info(f"Prompt generated successfully", prompt_id=generated_prompt.id)
        
        return PromptGenerationResponse(
            id=generated_prompt.id,
            generated_prompt=generated_prompt.generated_prompt,
            confidence_score=generated_prompt.confidence_score,
            tokens_count=generated_prompt.tokens_count,
            generation_time_ms=generated_prompt.generation_time_ms,
            contexts_used=[
                {
                    "content": ctx["content"],
                    "score": ctx["score"],
                    "document_name": ctx["document_name"]
                }
                for ctx in generated_prompt.contexts_used
            ],
            created_at=generated_prompt.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate prompt"
        )


@router.post("/save", response_model=SavedPrompt)
async def save_prompt(
    request: SavePromptRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Save a generated prompt to library
    """
    try:
        # Get user
        user_result = await db.execute(select(User).where(User.auth0_id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Get prompt and verify ownership
        prompt_result = await db.execute(
            select(GeneratedPrompt).where(
                GeneratedPrompt.id == request.prompt_id,
                GeneratedPrompt.user_id == user.id
            )
        )
        prompt = prompt_result.scalar_one_or_none()
        
        if not prompt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
        
        # Update prompt
        prompt.is_saved = True
        prompt.is_public = request.is_public
        
        if request.title:
            prompt.title = request.title
        
        if request.tags:
            prompt.tags = request.tags
        
        await db.commit()
        await db.refresh(prompt)
        
        # Get rating stats
        rating_stats = await db.execute(
            select(
                func.count(PromptRating.id).label("rating_count"),
                func.avg(PromptRating.rating).label("avg_rating")
            ).where(PromptRating.prompt_id == prompt.id)
        )
        stats = rating_stats.one()
        
        logger.info(f"Prompt saved to library", prompt_id=prompt.id)
        
        return SavedPrompt(
            id=prompt.id,
            title=prompt.title,
            feature_name=prompt.feature_name,
            user_story=prompt.user_story,
            tech_stack=prompt.tech_stack,
            requirements=prompt.requirements,
            constraints=prompt.constraints,
            generated_prompt=prompt.generated_prompt,
            confidence_score=prompt.confidence_score,
            is_public=prompt.is_public,
            tags=prompt.tags,
            rating_count=stats.rating_count or 0,
            avg_rating=float(stats.avg_rating) if stats.avg_rating else None,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save prompt"
        )


@router.post("/rate", response_model=PromptRatingResponse, status_code=status.HTTP_201_CREATED)
async def rate_prompt(
    request: PromptRatingRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Rate a generated prompt (thumbs up/down)
    """
    try:
        # Get user
        user_result = await db.execute(select(User).where(User.auth0_id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Verify prompt exists
        prompt_result = await db.execute(
            select(GeneratedPrompt).where(GeneratedPrompt.id == request.prompt_id)
        )
        prompt = prompt_result.scalar_one_or_none()
        
        if not prompt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
        
        # Check if user already rated this prompt
        existing_rating = await db.execute(
            select(PromptRating).where(
                PromptRating.prompt_id == request.prompt_id,
                PromptRating.user_id == user.id
            )
        )
        existing = existing_rating.scalar_one_or_none()
        
        if existing:
            # Update existing rating
            existing.rating = request.rating
            existing.feedback = request.feedback
            existing.was_successful = request.was_successful
            existing.code_quality_score = request.code_quality_score
            existing.notes = request.notes
            rating = existing
        else:
            # Create new rating
            rating = PromptRating(
                prompt_id=request.prompt_id,
                user_id=user.id,
                rating=request.rating,
                feedback=request.feedback,
                was_successful=request.was_successful,
                code_quality_score=request.code_quality_score,
                notes=request.notes
            )
            db.add(rating)
        
        await db.commit()
        await db.refresh(rating)
        
        logger.info(f"Prompt rated", prompt_id=request.prompt_id, rating=request.rating)
        
        return PromptRatingResponse(
            id=rating.id,
            prompt_id=rating.prompt_id,
            rating=rating.rating,
            feedback=rating.feedback,
            was_successful=rating.was_successful,
            code_quality_score=rating.code_quality_score,
            created_at=rating.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rating prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rate prompt"
        )


@router.get("/", response_model=List[PromptListItem])
async def list_prompts(
    agent_id: str = None,
    is_saved: bool = None,
    skip: int = 0,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    List user's generated prompts
    """
    try:
        # Get user
        user_result = await db.execute(select(User).where(User.auth0_id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Build query
        query = select(GeneratedPrompt).where(GeneratedPrompt.user_id == user.id)
        
        if agent_id:
            query = query.where(GeneratedPrompt.agent_id == agent_id)
        
        if is_saved is not None:
            query = query.where(GeneratedPrompt.is_saved == is_saved)
        
        query = query.order_by(desc(GeneratedPrompt.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        prompts = result.scalars().all()
        
        return [
            PromptListItem(
                id=p.id,
                title=p.title,
                feature_name=p.feature_name,
                tech_stack=p.tech_stack,
                confidence_score=p.confidence_score,
                is_saved=p.is_saved,
                tags=p.tags,
                created_at=p.created_at
            )
            for p in prompts
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list prompts"
        )


@router.get("/{prompt_id}", response_model=SavedPrompt)
async def get_prompt(
    prompt_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific prompt by ID
    """
    try:
        # Get user
        user_result = await db.execute(select(User).where(User.auth0_id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Get prompt
        prompt_result = await db.execute(
            select(GeneratedPrompt).where(
                GeneratedPrompt.id == prompt_id,
                GeneratedPrompt.user_id == user.id
            )
        )
        prompt = prompt_result.scalar_one_or_none()
        
        if not prompt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
        
        # Get rating stats
        rating_stats = await db.execute(
            select(
                func.count(PromptRating.id).label("rating_count"),
                func.avg(PromptRating.rating).label("avg_rating")
            ).where(PromptRating.prompt_id == prompt.id)
        )
        stats = rating_stats.one()
        
        return SavedPrompt(
            id=prompt.id,
            title=prompt.title,
            feature_name=prompt.feature_name,
            user_story=prompt.user_story,
            tech_stack=prompt.tech_stack,
            requirements=prompt.requirements,
            constraints=prompt.constraints,
            generated_prompt=prompt.generated_prompt,
            confidence_score=prompt.confidence_score,
            is_public=prompt.is_public,
            tags=prompt.tags,
            rating_count=stats.rating_count or 0,
            avg_rating=float(stats.avg_rating) if stats.avg_rating else None,
            created_at=prompt.created_at,
            updated_at=prompt.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get prompt"
        )


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a generated prompt
    """
    try:
        # Get user
        user_result = await db.execute(select(User).where(User.auth0_id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Get and delete prompt
        prompt_result = await db.execute(
            select(GeneratedPrompt).where(
                GeneratedPrompt.id == prompt_id,
                GeneratedPrompt.user_id == user.id
            )
        )
        prompt = prompt_result.scalar_one_or_none()
        
        if not prompt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
        
        await db.delete(prompt)
        await db.commit()
        
        logger.info(f"Prompt deleted", prompt_id=prompt_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting prompt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete prompt"
        )
