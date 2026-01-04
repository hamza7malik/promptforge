from typing import List, Dict, Any, Optional
import asyncio
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from pinecone import Pinecone, ServerlessSpec
import tiktoken
from config.settings import settings
from core.logging import logger
import tempfile
import os


class DocumentProcessor:
    """Process and chunk documents for RAG"""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self.encoding = tiktoken.encoding_for_model("gpt-4")
    
    async def load_document(self, file_path: str, file_type: str) -> str:
        """Load document content based on file type"""
        try:
            if file_type == "pdf":
                loader = PyPDFLoader(file_path)
            elif file_type == "docx":
                loader = Docx2txtLoader(file_path)
            elif file_type in ["txt", "md"]:
                loader = TextLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            documents = loader.load()
            content = "\n\n".join([doc.page_content for doc in documents])
            return content
        except Exception as e:
            logger.error(f"Error loading document: {e}", file_path=file_path)
            raise
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Split text into chunks"""
        try:
            chunks = self.text_splitter.split_text(text)
            
            chunk_dicts = []
            for i, chunk in enumerate(chunks):
                chunk_dict = {
                    "content": chunk,
                    "chunk_index": i,
                    "token_count": len(self.encoding.encode(chunk)),
                    "metadata": metadata or {}
                }
                chunk_dicts.append(chunk_dict)
            
            logger.info(f"Created {len(chunk_dicts)} chunks")
            return chunk_dicts
        except Exception as e:
            logger.error(f"Error chunking text: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))


class EmbeddingService:
    """Generate embeddings using OpenAI"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        try:
            embedding = await self.embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            embeddings = await self.embeddings.aembed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise


class VectorStore:
    """Manage Pinecone vector store"""
    
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX_NAME
        self.dimension = settings.PINECONE_DIMENSION
        self._ensure_index()
    
    def _ensure_index(self):
        """Create index if it doesn't exist"""
        try:
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.PINECONE_ENVIRONMENT
                    )
                )
                logger.info(f"Created Pinecone index: {self.index_name}")
            
            self.index = self.pc.Index(self.index_name)
        except Exception as e:
            logger.error(f"Error ensuring Pinecone index: {e}")
            raise
    
    async def upsert_vectors(
        self,
        vectors: List[tuple],
        namespace: str
    ) -> Dict[str, Any]:
        """Upsert vectors to Pinecone
        
        Args:
            vectors: List of (id, embedding, metadata) tuples
            namespace: Agent ID as namespace
        """
        try:
            # Pinecone upsert is synchronous, run in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.index.upsert(
                    vectors=vectors,
                    namespace=namespace
                )
            )
            logger.info(f"Upserted {len(vectors)} vectors to namespace {namespace}")
            return result
        except Exception as e:
            logger.error(f"Error upserting vectors: {e}")
            raise
    
    async def query_vectors(
        self,
        query_embedding: List[float],
        namespace: str,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Query vectors from Pinecone"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.index.query(
                    vector=query_embedding,
                    namespace=namespace,
                    top_k=top_k,
                    filter=filter_dict,
                    include_metadata=True
                )
            )
            
            matches = []
            for match in result.matches:
                matches.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
            
            return matches
        except Exception as e:
            logger.error(f"Error querying vectors: {e}")
            raise
    
    async def delete_namespace(self, namespace: str):
        """Delete all vectors in a namespace"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.index.delete(delete_all=True, namespace=namespace)
            )
            logger.info(f"Deleted namespace: {namespace}")
        except Exception as e:
            logger.error(f"Error deleting namespace: {e}")
            raise
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(
                None,
                lambda: self.index.describe_index_stats()
            )
            return stats
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            raise


class RAGPipeline:
    """Complete RAG pipeline orchestration"""
    
    def __init__(self):
        self.doc_processor = DocumentProcessor()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
    
    async def process_and_index_document(
        self,
        file_path: str,
        file_type: str,
        agent_id: str,
        document_id: str,
        document_name: str
    ) -> int:
        """Process document and index to vector store
        
        Returns number of chunks created
        """
        try:
            # Load document
            logger.info(f"Loading document: {document_name}")
            content = await self.doc_processor.load_document(file_path, file_type)
            
            # Chunk document
            metadata = {
                "document_id": document_id,
                "document_name": document_name,
                "agent_id": agent_id,
                "file_type": file_type
            }
            chunks = self.doc_processor.chunk_text(content, metadata)
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            chunk_texts = [chunk["content"] for chunk in chunks]
            embeddings = await self.embedding_service.embed_texts(chunk_texts)
            
            # Prepare vectors for upsert
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"{document_id}_chunk_{i}"
                vectors.append((
                    vector_id,
                    embedding,
                    {
                        **chunk["metadata"],
                        "content": chunk["content"],
                        "chunk_index": chunk["chunk_index"],
                        "token_count": chunk["token_count"]
                    }
                ))
            
            # Upsert to Pinecone
            await self.vector_store.upsert_vectors(vectors, namespace=agent_id)
            
            logger.info(f"Successfully indexed document {document_name} with {len(chunks)} chunks")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}", document_id=document_id)
            raise
    
    async def retrieve_context(
        self,
        query: str,
        agent_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context for query"""
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.embed_text(query)
            
            # Query vector store
            matches = await self.vector_store.query_vectors(
                query_embedding=query_embedding,
                namespace=agent_id,
                top_k=top_k
            )
            
            # Format results
            context_chunks = []
            for match in matches:
                context_chunks.append({
                    "content": match["metadata"].get("content", ""),
                    "score": match["score"],
                    "document_id": match["metadata"].get("document_id", ""),
                    "document_name": match["metadata"].get("document_name", ""),
                    "metadata": match["metadata"]
                })
            
            return context_chunks
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            raise
    
    async def delete_document_vectors(self, agent_id: str, document_id: str):
        """Delete all vectors for a document"""
        try:
            # Query to get all vector IDs for this document
            # Then delete them
            # Note: This is a simplified version. In production, you might want
            # to track vector IDs separately or use metadata filtering
            logger.warning("Document vector deletion not fully implemented")
            # await self.vector_store.delete_vectors(...)
        except Exception as e:
            logger.error(f"Error deleting document vectors: {e}")
            raise


# Singleton instances
rag_pipeline = RAGPipeline()
