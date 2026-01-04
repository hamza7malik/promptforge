from typing import Dict, Any, List, Optional
import asyncio
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from config.settings import settings
from core.logging import logger


class RAGASEvaluator:
    """Evaluate RAG responses using RAGAS metrics"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
    
    async def evaluate_response(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate a single RAG response
        
        Args:
            question: User's question
            answer: Generated answer
            contexts: List of retrieved context strings
            ground_truth: Optional ground truth answer for comparison
        
        Returns:
            Dictionary of evaluation metrics
        """
        try:
            # Prepare dataset
            data = {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts],
            }
            
            if ground_truth:
                data["ground_truth"] = [ground_truth]
            
            dataset = Dataset.from_dict(data)
            
            # Select metrics based on available data
            metrics = [
                faithfulness,
                answer_relevancy,
                context_precision,
            ]
            
            if ground_truth:
                metrics.extend([answer_correctness, context_recall])
            
            # Run evaluation in executor (RAGAS is synchronous)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: evaluate(
                    dataset,
                    metrics=metrics,
                    llm=self.llm,
                    embeddings=self.embeddings
                )
            )
            
            # Extract scores
            scores = {
                "faithfulness_score": result.get("faithfulness"),
                "answer_relevancy_score": result.get("answer_relevancy"),
                "context_precision_score": result.get("context_precision"),
            }
            
            if ground_truth:
                scores["answer_correctness_score"] = result.get("answer_correctness")
                scores["context_recall_score"] = result.get("context_recall")
            
            # Calculate overall score (average of available metrics)
            available_scores = [v for v in scores.values() if v is not None]
            overall_score = sum(available_scores) / len(available_scores) if available_scores else None
            scores["overall_score"] = overall_score
            
            logger.info(
                "Completed RAGAS evaluation",
                overall_score=overall_score,
                metrics=scores
            )
            
            return {
                **scores,
                "evaluation_details": {
                    "num_contexts": len(contexts),
                    "has_ground_truth": ground_truth is not None,
                    "raw_result": dict(result) if result else {}
                }
            }
            
        except Exception as e:
            logger.error(f"Error in RAGAS evaluation: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def batch_evaluate(
        self,
        evaluations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Evaluate multiple responses in batch
        
        Args:
            evaluations: List of dicts with keys: question, answer, contexts, ground_truth (optional)
        
        Returns:
            List of evaluation results
        """
        try:
            tasks = []
            for eval_data in evaluations:
                task = self.evaluate_response(
                    question=eval_data["question"],
                    answer=eval_data["answer"],
                    contexts=eval_data["contexts"],
                    ground_truth=eval_data.get("ground_truth")
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            return [
                result if not isinstance(result, Exception) else {"error": str(result), "status": "failed"}
                for result in results
            ]
            
        except Exception as e:
            logger.error(f"Error in batch evaluation: {e}")
            raise


class GroundednessChecker:
    """Check if answer is grounded in the provided context"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0,
            openai_api_key=settings.OPENAI_API_KEY
        )
    
    async def check_groundedness(
        self,
        answer: str,
        contexts: List[str]
    ) -> Dict[str, Any]:
        """Check if answer claims are supported by contexts
        
        Returns:
            Dictionary with groundedness score and details
        """
        try:
            context_str = "\n\n".join(contexts)
            
            prompt = f"""You are evaluating whether an AI-generated answer is grounded in the provided context.

Context:
{context_str}

Answer:
{answer}

Analyze each claim in the answer and determine if it's supported by the context.
Return a JSON object with:
- score: float between 0-1 (1 = fully grounded, 0 = not grounded)
- grounded_claims: list of claims that ARE supported
- ungrounded_claims: list of claims that are NOT supported
- analysis: brief explanation

Format:
{{
    "score": 0.85,
    "grounded_claims": ["claim 1", "claim 2"],
    "ungrounded_claims": ["claim 3"],
    "analysis": "explanation"
}}
"""
            
            from langchain.schema import HumanMessage, SystemMessage
            messages = [
                SystemMessage(content="You are an expert evaluator of AI-generated content."),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            import json
            result = json.loads(response.content)
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking groundedness: {e}")
            return {
                "score": None,
                "error": str(e)
            }


# Singleton instances
ragas_evaluator = RAGASEvaluator()
groundedness_checker = GroundednessChecker()
