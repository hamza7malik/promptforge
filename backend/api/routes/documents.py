from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import tempfile
import os

from core.database import get_db
from core.auth import get_current_user_id
from models.models import User, Agent, Document
from schemas.schemas import (
    DocumentCreate, 
    DocumentResponse, 
    PresignedUploadRequest,
    PresignedUploadResponse
)
from services.storage.s3_service import s3_service
from services.rag.pipeline import rag_pipeline
from core.logging import logger

router = APIRouter()


async def process_document_task(
    document_id: str,
    s3_key: str,
    file_type: str,
    agent_id: str,
    document_name: str,
    db_url: str
):
    """Background task to process and index document"""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    
    # Create new DB session for background task
    engine = create_async_engine(db_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            # Update document status to processing
            doc_result = await db.execute(select(Document).where(Document.id == document_id))
            document = doc_result.scalar_one_or_none()
            
            if not document:
                logger.error(f"Document not found: {document_id}")
                return
            
            document.status = "processing"
            await db.commit()
            
            # Download file from S3
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp_file:
                tmp_path = tmp_file.name
            
            await s3_service.download_file(s3_key, tmp_path)
            
            # Process and index document
            num_chunks = await rag_pipeline.process_and_index_document(
                file_path=tmp_path,
                file_type=file_type,
                agent_id=agent_id,
                document_id=document_id,
                document_name=document_name
            )
            
            # Update document status
            document.status = "completed"
            document.num_chunks = num_chunks
            await db.commit()
            
            # Cleanup
            os.unlink(tmp_path)
            
            logger.info(f"Successfully processed document: {document_id}")
            
    except Exception as e:
        logger.error(f"Error processing document: {e}", document_id=document_id)
        
        async with async_session() as db:
            doc_result = await db.execute(select(Document).where(Document.id == document_id))
            document = doc_result.scalar_one_or_none()
            if document:
                document.status = "failed"
                document.error_message = str(e)
                await db.commit()
    finally:
        await engine.dispose()


@router.post("/presigned-upload", response_model=PresignedUploadResponse)
async def get_presigned_upload_url(
    request: PresignedUploadRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get presigned URL for direct S3 upload"""
    try:
        # Validate file size
        if request.file_size > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 50MB limit"
            )
        
        # Generate S3 key
        # We'll use a temporary location until we associate with an agent
        s3_key = f"temp/{user_id}/{request.filename}"
        
        # Generate presigned URL
        presigned_data = s3_service.generate_presigned_upload_url(
            s3_key=s3_key,
            file_type=request.file_type
        )
        
        return PresignedUploadResponse(**presigned_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating presigned URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload URL"
        )


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_data: DocumentCreate,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create document record and trigger processing"""
    try:
        # Verify agent exists and user owns it
        user_result = await db.execute(select(User).where(User.auth0_id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        agent_result = await db.execute(
            select(Agent).where(Agent.id == document_data.agent_id, Agent.user_id == user.id)
        )
        agent = agent_result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        
        # Create document record
        document = Document(
            **document_data.model_dump()
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        # Trigger background processing
        from config.settings import settings
        background_tasks.add_task(
            process_document_task,
            document_id=document.id,
            s3_key=document.s3_key,
            file_type=document.file_type or "pdf",
            agent_id=document.agent_id,
            document_name=document.filename,
            db_url=settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        )
        
        logger.info(f"Created document: {document.id}", filename=document.filename)
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create document"
        )


@router.get("/agent/{agent_id}", response_model=List[DocumentResponse])
async def list_agent_documents(
    agent_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List all documents for an agent"""
    try:
        # Verify agent exists and user owns it
        user_result = await db.execute(select(User).where(User.auth0_id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        agent_result = await db.execute(
            select(Agent).where(Agent.id == agent_id, Agent.user_id == user.id)
        )
        agent = agent_result.scalar_one_or_none()
        
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        
        # Get documents
        docs_result = await db.execute(
            select(Document).where(Document.agent_id == agent_id).order_by(Document.created_at.desc())
        )
        documents = docs_result.scalars().all()
        
        return documents
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete document"""
    try:
        # Get user
        user_result = await db.execute(select(User).where(User.auth0_id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Get document with agent
        doc_result = await db.execute(
            select(Document).join(Agent).where(
                Document.id == document_id,
                Agent.user_id == user.id
            )
        )
        document = doc_result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        
        # Delete from S3
        try:
            await s3_service.delete_file(document.s3_key)
        except Exception as e:
            logger.warning(f"Failed to delete S3 file: {e}")
        
        # Delete from database
        await db.delete(document)
        await db.commit()
        
        # TODO: Delete vectors from Pinecone
        
        logger.info(f"Deleted document: {document_id}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )
