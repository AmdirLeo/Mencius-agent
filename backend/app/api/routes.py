from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import logging
import os
from typing import Optional

from app.llm.client import glm_client
from app.rag.retriever import retriever
from app.data.loader import load_mencius_text, parse_mencius_sections
from app.data.chunker import chunk_by_sentences
from app.data.embedder import embedder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["mencius"])

# Global state for initialization
_is_initialized = False
_initialization_error = None

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(3, ge=1, le=10)

class AskResponse(BaseModel):
    answer: str
    sources: list = []
    status: str = "success"

@router.on_event("startup")
async def initialize_data():
    """Initialize vector database with Mencius texts on startup"""
    global _is_initialized, _initialization_error
    
    try:
        logger.info("Starting data initialization on app startup...")
        
        # Use absolute path from project root
        mencius_file = os.path.join(os.path.dirname(__file__), "../../..", "data/raw/孟子译注.txt")
        mencius_file = os.path.abspath(mencius_file)
        
        if not os.path.exists(mencius_file):
            logger.warning(f"Mencius file not found: {mencius_file}")
            _initialization_error = f"Mencius file not found: {mencius_file}"
            return
        
        # Load mencius text
        logger.info("Loading Mencius texts...")
        text = load_mencius_text(mencius_file)
        
        # Parse into sections
        logger.info("Parsing Mencius sections...")
        sections = parse_mencius_sections(text)
        
        # Chunk into smaller pieces
        logger.info("Chunking texts...")
        documents = []
        for section in sections[:100]:  # Limit to first 100 sections for demo
            chunks = chunk_by_sentences(section.get("content", ""), target_chars=300)
            for chunk in chunks:
                documents.append({
                    'text': chunk['text'],
                    'metadata': {
                        'section_title': section.get('title', ''),
                        'section_type': section.get('type', ''),
                        'length': chunk.get('length', 0)
                    }
                })
        
        logger.info(f"Total documents after chunking: {len(documents)}")
        
        # Initialize Qdrant collection and add documents
        if len(documents) > 0:
            try:
                retriever.init_collection()
                retriever.add_documents(documents)
                logger.info("Successfully initialized vector database")
                _is_initialized = True
            except Exception as e:
                logger.error(f"Failed to add documents to vector DB: {str(e)}")
                _initialization_error = str(e)
        else:
            logger.warning("No documents to add to vector database")
            
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        _initialization_error = str(e)

@router.get("/status")
async def get_status():
    """Get initialization status"""
    collection_info = retriever.get_collection_info()
    return {
        "status": "ready" if _is_initialized else "initializing",
        "initialized": _is_initialized,
        "error": _initialization_error,
        "collection": collection_info
    }

@router.post("/ask", response_model=AskResponse)
async def ask_mencius(request: AskRequest):
    """
    Ask Mencius a question and get a response based on his teachings.
    
    Retrieves relevant passages from Mencius texts using RAG,
    then generates a response using GLM-4 LLM with Mencius character.
    Falls back to RAG-only response if LLM API fails.
    """
    try:
        if _initialization_error:
            raise HTTPException(
                status_code=503,
                detail=f"System not ready: {_initialization_error}"
            )
        
        if not _is_initialized:
            raise HTTPException(
                status_code=503,
                detail="System still initializing, please try again in a moment"
            )
        
        logger.info(f"Processing question: {request.question}")
        
        # Step 1: Retrieve relevant documents from Mencius texts
        try:
            context_docs = await retriever.retrieve(request.question, top_k=request.top_k)
            logger.info(f"Retrieved {len(context_docs)} relevant documents")
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {str(e)}")
            context_docs = []
        
        # Step 2: Generate response using GLM-4 with Mencius character
        response_text = None
        llm_error = None
        try:
            response_text = await glm_client.generate_response(
                user_question=request.question,
                context=context_docs
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            llm_error = str(e)
            response_text = None
        
        # Step 3A: If LLM succeeds, format and return response
        if response_text:
            sources = [
                {
                    "text": doc.get("text", "")[:200],
                    "metadata": doc.get("metadata", {}),
                    "score": doc.get("score", 0)
                }
                for doc in context_docs
            ]
            
            return AskResponse(
                answer=response_text,
                sources=sources,
                status="success"
            )
        
        # Step 3B: Fallback - Return RAG-only response if LLM fails
        if context_docs:
            # Construct a response from retrieved documents
            fallback_answer = f"孟子曰：\n\n"
            for i, doc in enumerate(context_docs, 1):
                text = doc.get("text", "").strip()
                if text:
                    fallback_answer += f"其一：{text}\n\n"
            
            sources = [
                {
                    "text": doc.get("text", "")[:200],
                    "metadata": doc.get("metadata", {}),
                    "score": doc.get("score", 0)
                }
                for doc in context_docs
            ]
            
            logger.warning(f"Using RAG-only fallback response due to LLM error: {llm_error}")
            return AskResponse(
                answer=fallback_answer,
                sources=sources,
                status="fallback_rag_only"
            )
        
        # If no context documents and LLM failed
        raise HTTPException(
            status_code=500,
            detail=f"LLM API error and no context available: {llm_error}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
