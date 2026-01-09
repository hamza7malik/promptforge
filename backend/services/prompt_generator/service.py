from typing import List, Dict, Any
import time
import tiktoken
from services.rag.pipeline import rag_pipeline
from services.llm.service import llm_service
from core.logging import logger


class PromptGeneratorService:
    """Service for generating expert-level prompts using RAG"""
    
    def __init__(self):
        self.encoding = tiktoken.encoding_for_model("gpt-4")
    
    async def generate_prompt(
        self,
        agent_id: str,
        feature_name: str,
        user_story: str = None,
        tech_stack: List[str] = None,
        requirements: List[str] = None,
        constraints: List[str] = None,
        existing_code_context: str = None,
        architecture_style: str = None,
        include_tests: bool = True,
        include_documentation: bool = True,
        include_error_handling: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive, production-ready prompt using RAG
        
        Returns:
            Dict with generated_prompt, contexts_used, confidence_score, etc.
        """
        start_time = time.time()
        
        try:
            # Build the query for RAG retrieval
            query = self._build_retrieval_query(
                feature_name=feature_name,
                user_story=user_story,
                tech_stack=tech_stack,
                requirements=requirements
            )
            
            logger.info(f"Retrieving knowledge for prompt generation", query=query[:100])
            
            # Retrieve relevant knowledge from agent's documents
            contexts = await rag_pipeline.retrieve_context(
                query=query,
                agent_id=agent_id,
                top_k=15  # Get more contexts for comprehensive prompt
            )
            
            # Calculate confidence score based on retrieval quality
            confidence_score = self._calculate_confidence_score(contexts)
            
            # Extract structured knowledge from contexts
            best_practices = self._extract_best_practices(contexts)
            patterns = self._extract_patterns(contexts)
            examples = self._extract_examples(contexts)
            
            # Generate the prompt using GPT-4
            generated_prompt = await self._generate_structured_prompt(
                feature_name=feature_name,
                user_story=user_story,
                tech_stack=tech_stack or [],
                requirements=requirements or [],
                constraints=constraints or [],
                existing_code_context=existing_code_context,
                architecture_style=architecture_style,
                contexts=contexts,
                best_practices=best_practices,
                patterns=patterns,
                examples=examples,
                include_tests=include_tests,
                include_documentation=include_documentation,
                include_error_handling=include_error_handling
            )
            
            # Calculate metrics
            elapsed_ms = int((time.time() - start_time) * 1000)
            token_count = len(self.encoding.encode(generated_prompt))
            
            logger.info(
                f"Generated prompt successfully",
                tokens=token_count,
                time_ms=elapsed_ms,
                confidence=confidence_score
            )
            
            return {
                "generated_prompt": generated_prompt,
                "contexts_used": [
                    {
                        "content": ctx["content"][:500],  # Truncate for storage
                        "score": ctx["score"],
                        "document_name": ctx["document_name"]
                    }
                    for ctx in contexts[:10]  # Store top 10
                ],
                "confidence_score": confidence_score,
                "tokens_count": token_count,
                "generation_time_ms": elapsed_ms
            }
            
        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            raise
    
    def _build_retrieval_query(
        self,
        feature_name: str,
        user_story: str = None,
        tech_stack: List[str] = None,
        requirements: List[str] = None
    ) -> str:
        """Build optimized query for RAG retrieval"""
        query_parts = [feature_name]
        
        if user_story:
            query_parts.append(user_story)
        
        if tech_stack:
            query_parts.append(f"Technologies: {', '.join(tech_stack)}")
        
        if requirements:
            query_parts.append(f"Requirements: {', '.join(requirements[:3])}")  # Top 3
        
        # Add key terms for better retrieval
        query_parts.extend([
            "best practices",
            "production patterns",
            "implementation guide",
            "architecture"
        ])
        
        return " ".join(query_parts)
    
    def _calculate_confidence_score(self, contexts: List[Dict]) -> float:
        """
        Calculate confidence score based on retrieval quality
        
        Returns: float between 0.0 and 1.0
        """
        if not contexts:
            return 0.0
        
        # Average of top 5 scores
        top_scores = [ctx["score"] for ctx in contexts[:5]]
        avg_score = sum(top_scores) / len(top_scores)
        
        # Adjust based on number of high-quality contexts
        high_quality_count = sum(1 for ctx in contexts if ctx["score"] > 0.7)
        quality_factor = min(high_quality_count / 5, 1.0)
        
        # Combined confidence: 70% retrieval score + 30% quality factor
        confidence = (avg_score * 0.7) + (quality_factor * 0.3)
        
        return round(confidence, 3)
    
    def _extract_best_practices(self, contexts: List[Dict]) -> str:
        """Extract best practices from retrieved contexts"""
        relevant_parts = []
        
        for ctx in contexts[:5]:
            content = ctx["content"].lower()
            
            # Look for best practice indicators
            if any(keyword in content for keyword in ["best practice", "should", "must", "recommended"]):
                # Extract relevant sentences
                sentences = ctx["content"].split(".")
                for sentence in sentences:
                    if any(keyword in sentence.lower() for keyword in ["best practice", "should", "recommended"]):
                        relevant_parts.append(sentence.strip())
        
        return "\n".join(relevant_parts[:10]) if relevant_parts else "No specific best practices found in documents."
    
    def _extract_patterns(self, contexts: List[Dict]) -> str:
        """Extract implementation patterns from contexts"""
        patterns = []
        
        for ctx in contexts[:5]:
            content = ctx["content"].lower()
            
            # Look for pattern indicators
            if any(keyword in content for keyword in ["pattern", "approach", "design", "architecture"]):
                patterns.append(ctx["content"][:300])  # First 300 chars
        
        return "\n\n".join(patterns[:5]) if patterns else "No specific patterns found in documents."
    
    def _extract_examples(self, contexts: List[Dict]) -> str:
        """Extract code examples from contexts"""
        examples = []
        
        for ctx in contexts[:8]:
            content = ctx["content"]
            
            # Look for code indicators
            if any(indicator in content for indicator in ["```", "def ", "class ", "function", "import"]):
                examples.append(content[:400])  # First 400 chars
        
        return "\n\n".join(examples[:3]) if examples else "No code examples found in documents."
    
    async def _generate_structured_prompt(
        self,
        feature_name: str,
        user_story: str,
        tech_stack: List[str],
        requirements: List[str],
        constraints: List[str],
        existing_code_context: str,
        architecture_style: str,
        contexts: List[Dict],
        best_practices: str,
        patterns: str,
        examples: str,
        include_tests: bool,
        include_documentation: bool,
        include_error_handling: bool
    ) -> str:
        """Generate the final structured prompt using GPT-4"""
        
        # Format contexts for injection
        formatted_contexts = "\n\n".join([
            f"[Source: {ctx['document_name']} | Relevance: {ctx['score']:.2f}]\n{ctx['content']}"
            for ctx in contexts[:8]
        ])
        
        # Build the meta-prompt for GPT-4
        newline = '\n'
        user_story_section = f"USER STORY:\n{user_story}\n\n" if user_story else ""
        arch_line = f"- Architecture: {architecture_style}\n" if architecture_style else ""
        
        req_section = ""
        if requirements:
            req_lines = '\n'.join(f"  • {req}" for req in requirements)
            req_section = f"- Functional Requirements:\n{req_lines}\n"
        
        const_section = ""
        if constraints:
            const_lines = '\n'.join(f"  • {con}" for con in constraints)
            const_section = f"- Constraints:\n{const_lines}\n"
        
        code_context_section = f"EXISTING CODE CONTEXT:\n{existing_code_context}\n\n" if existing_code_context else ""
        
        error_section = "7. **Error Handling**: Comprehensive error handling strategy\n" if include_error_handling else ""
        test_section = "8. **Testing Requirements**: Test cases and testing strategy\n" if include_tests else ""
        doc_section = "9. **Documentation**: Required documentation and comments\n" if include_documentation else ""
        
        meta_prompt = f"""You are an expert at crafting comprehensive, production-ready prompts for AI coding assistants (like GitHub Copilot, Cursor, etc.).

Your task is to generate a detailed, structured prompt that will help an AI coding assistant implement the following feature with high quality.

FEATURE TO IMPLEMENT:
{feature_name}

{user_story_section}TECHNICAL CONTEXT:
- Tech Stack: {', '.join(tech_stack) if tech_stack else 'Not specified'}
{arch_line}{req_section}{const_section}
{code_context_section}EXPERT KNOWLEDGE (Retrieved from domain documents):

BEST PRACTICES:
{best_practices}

IMPLEMENTATION PATTERNS:
{patterns}

RELEVANT EXAMPLES:
{examples}

DETAILED CONTEXT FROM EXPERT DOCUMENTS:
{formatted_contexts}

---

Now generate a comprehensive, production-ready prompt that includes:

1. **Feature Overview**: Clear description of what needs to be built
2. **Technical Requirements**: Specific technical specs based on the tech stack
3. **Architecture Guidance**: How to structure the implementation (informed by retrieved knowledge)
4. **Implementation Steps**: Step-by-step breakdown with specific details
5. **Best Practices**: Key practices to follow (from retrieved documents)
6. **Code Patterns**: Specific patterns to use (from retrieved examples)
{error_section}{test_section}{doc_section}10. **Code Style**: Conventions to follow

The prompt should be:
- Copy-paste ready for AI coding assistants
- Specific and actionable (no vague instructions)
- Informed by the expert knowledge retrieved
- Production-quality focused
- Include concrete examples where relevant

Generate the prompt now:"""

        # Generate using GPT-4 - collect all streamed chunks
        response_chunks = []
        async for chunk in llm_service.generate_response(
            query=meta_prompt,
            context_chunks=[],  # Already included in meta_prompt
            system_prompt="You are an expert prompt engineer specializing in creating high-quality prompts for AI coding assistants. Your prompts are detailed, structured, and lead to production-ready code.",
            temperature=0.7,
            max_tokens=4096
        ):
            response_chunks.append(chunk)
        
        generated_prompt = "".join(response_chunks)
        return generated_prompt


# Singleton instance
prompt_generator = PromptGeneratorService()
