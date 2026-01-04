from typing import List, Dict, Any, AsyncGenerator, Optional
import asyncio
import time
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from config.settings import settings
from core.logging import logger
import tiktoken


class LLMService:
    """Service for LLM interactions"""
    
    def __init__(self):
        self.model = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            openai_api_key=settings.OPENAI_API_KEY,
            streaming=True
        )
        self.encoding = tiktoken.encoding_for_model("gpt-4")
    
    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into context string"""
        if not chunks:
            return ""
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            doc_name = chunk.get("document_name", "Unknown")
            content = chunk.get("content", "")
            score = chunk.get("score", 0)
            context_parts.append(
                f"[Document {i}: {doc_name} (Relevance: {score:.2f})]\n{content}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _truncate_context(self, context: str, max_tokens: int = 100000) -> str:
        """Truncate context to fit within token limit"""
        tokens = self.encoding.encode(context)
        if len(tokens) > max_tokens:
            logger.warning(f"Truncating context from {len(tokens)} to {max_tokens} tokens")
            truncated_tokens = tokens[:max_tokens]
            return self.encoding.decode(truncated_tokens)
        return context
    
    def _create_prompt(
        self,
        system_prompt: str,
        context: str,
        query: str,
        conversation_history: List[Dict[str, str]]
    ) -> List:
        """Create prompt with context and history"""
        messages = []
        
        # System message with instructions
        system_content = f"""{system_prompt}

You are an expert AI assistant with access to a specialized knowledge base. When answering questions:

1. ONLY use information from the provided context below
2. If the context doesn't contain enough information, acknowledge this limitation
3. Cite which documents you're referencing when making claims
4. Be precise and technical when appropriate
5. If asked about topics outside your knowledge base, politely decline

---CONTEXT---
{context}
---END CONTEXT---
"""
        messages.append(SystemMessage(content=system_content))
        
        # Add conversation history
        for msg in conversation_history[-10:]:  # Last 10 messages
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current query
        messages.append(HumanMessage(content=query))
        
        return messages
    
    async def generate_response(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        system_prompt: str,
        conversation_history: List[Dict[str, str]] = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response"""
        try:
            start_time = time.time()
            
            # Format and truncate context
            context = self._format_context(context_chunks)
            context = self._truncate_context(context)
            
            # Create prompt
            messages = self._create_prompt(
                system_prompt=system_prompt,
                context=context,
                query=query,
                conversation_history=conversation_history or []
            )
            
            # Configure model
            if temperature is not None:
                self.model.temperature = temperature
            if max_tokens is not None:
                self.model.max_tokens = max_tokens
            
            # Stream response
            full_response = ""
            async for chunk in self.model.astream(messages):
                if hasattr(chunk, "content"):
                    content = chunk.content
                    if content:
                        full_response += content
                        yield content
            
            # Log metrics
            elapsed_ms = (time.time() - start_time) * 1000
            token_count = len(self.encoding.encode(full_response))
            
            logger.info(
                "Generated LLM response",
                tokens=token_count,
                latency_ms=elapsed_ms,
                chunks_used=len(context_chunks)
            )
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    async def generate_response_non_streaming(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        system_prompt: str,
        conversation_history: List[Dict[str, str]] = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> tuple[str, int, float]:
        """Generate non-streaming response
        
        Returns: (response_text, token_count, latency_ms)
        """
        try:
            start_time = time.time()
            
            # Format and truncate context
            context = self._format_context(context_chunks)
            context = self._truncate_context(context)
            
            # Create prompt
            messages = self._create_prompt(
                system_prompt=system_prompt,
                context=context,
                query=query,
                conversation_history=conversation_history or []
            )
            
            # Configure model
            non_streaming_model = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=temperature or settings.OPENAI_TEMPERATURE,
                max_tokens=max_tokens or settings.OPENAI_MAX_TOKENS,
                openai_api_key=settings.OPENAI_API_KEY,
                streaming=False
            )
            
            # Generate response
            response = await non_streaming_model.ainvoke(messages)
            response_text = response.content
            
            # Calculate metrics
            elapsed_ms = (time.time() - start_time) * 1000
            token_count = len(self.encoding.encode(response_text))
            
            logger.info(
                "Generated LLM response (non-streaming)",
                tokens=token_count,
                latency_ms=elapsed_ms
            )
            
            return response_text, token_count, elapsed_ms
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise


class PromptEngineeringService:
    """Service for prompt improvement suggestions"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY
        )
    
    async def suggest_improvements(
        self,
        original_prompt: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate prompt improvement suggestions"""
        try:
            system_prompt = """You are an expert prompt engineer. Analyze the given prompt and suggest improvements.

Focus on:
1. Clarity - Is the prompt clear and unambiguous?
2. Specificity - Does it provide enough context and constraints?
3. Structure - Is it well-organized with clear sections?
4. Examples - Would examples help guide the AI?
5. Output format - Is the desired output format specified?

Provide:
- An improved version of the prompt
- A list of specific improvements made
- The category of the main issue (clarity, specificity, structure, examples, format)
"""
            
            user_prompt = f"""Original Prompt:
{original_prompt}

{f'Additional Context: {context}' if context else ''}

Please provide your analysis in this JSON format:
{{
    "improved_prompt": "The improved version of the prompt",
    "improvements": [
        {{"type": "clarity|specificity|structure|examples|format", "description": "What was improved", "example": "Optional example"}},
    ],
    "category": "primary category of improvement"
}}
"""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # Parse JSON response
            import json
            result = json.loads(response.content)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating prompt suggestions: {e}")
            raise


# Singleton instances
llm_service = LLMService()
prompt_engineering_service = PromptEngineeringService()
