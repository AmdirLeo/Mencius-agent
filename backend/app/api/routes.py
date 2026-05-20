from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging
import os

from app.llm.client import glm_client
from app.rag.retriever import retriever
from app.data.loader import load_or_parse_mencius_chapters
from app.data.chunker import chunk_by_sentences

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["mencius"])

# Global state for initialization
_is_initialized = False
_initialization_error = None

class ConversationMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=1000)

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(3, ge=1, le=10)
    history: list[ConversationMessage] = Field(default_factory=list, max_length=12)

class AskResponse(BaseModel):
    answer: str
    sources: list = []
    status: str = "success"

def build_retrieval_documents(chapters: list) -> list:
    """Build retrieval documents from structured Mencius chapters."""
    documents = []
    field_labels = {
        "translation": "译文",
        "commentary": "读解",
        "original": "原文",
    }

    for chapter in chapters:
        book = chapter.get("book", "")
        title = chapter.get("chapter_title", "")
        tags = chapter.get("tags", [])
        tags_text = "、".join(tags)
        header = " / ".join(part for part in [book, title] if part)

        for field, label in field_labels.items():
            content = chapter.get(field, "")
            if not content:
                continue

            chunks = chunk_by_sentences(content, target_chars=450)
            for chunk in chunks:
                text_parts = []
                if header:
                    text_parts.append(f"出处：{header}")
                if tags_text:
                    text_parts.append(f"思想标签：{tags_text}")
                text_parts.append(f"{label}：{chunk['text']}")

                documents.append({
                    "text": "\n".join(text_parts),
                    "metadata": {
                        "book": book,
                        "chapter_title": title,
                        "chapter_number": chapter.get("chapter_number", 0),
                        "field": field,
                        "field_label": label,
                        "tags": tags,
                        "length": chunk.get("length", 0),
                    }
                })

    return documents

def should_use_rag(question: str) -> bool:
    """Skip text retrieval for short casual chat and context-only follow-ups."""
    normalized = question.strip()
    if len(normalized) > 40:
        return True

    casual_keywords = [
        "吃", "饭", "晚饭", "午饭", "早饭", "睡", "困", "累", "今天",
        "昨天", "明天", "你呢", "咋样", "怎么样", "在吗", "哈哈",
    ]
    thought_keywords = [
        "仁", "义", "礼", "智", "信", "性善", "人性", "仁政", "民生",
        "王道", "霸道", "浩然", "良知", "恻隐", "道德", "原则", "利益",
        "人生", "意义", "修身", "君子", "小人",
    ]

    if any(keyword in normalized for keyword in thought_keywords):
        return True
    if any(keyword in normalized for keyword in casual_keywords):
        return False

    return True

@router.on_event("startup")
async def initialize_data():
    """Initialize vector database with Mencius texts on startup"""
    global _is_initialized, _initialization_error
    
    try:
        logger.info("Starting data initialization on app startup...")
        
        # Use absolute paths from project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        mencius_file = os.path.join(project_root, "data/raw/孟子译注.txt")
        processed_file = os.path.join(project_root, "data/processed/mencius_chapters.json")
        mencius_file = os.path.abspath(mencius_file)
        
        if not os.path.exists(mencius_file):
            logger.warning(f"Mencius file not found: {mencius_file}")
            _initialization_error = f"Mencius file not found: {mencius_file}"
            return
        
        # Load or parse structured chapters
        logger.info("Loading Mencius chapters...")
        chapters = load_or_parse_mencius_chapters(mencius_file, processed_file)
        
        # Build structured retrieval documents
        logger.info("Building retrieval documents...")
        documents = build_retrieval_documents(chapters)
        
        logger.info(f"Total documents after chunking: {len(documents)}")
        
        # Initialize FAISS index and add documents
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
        
        # Step 1: Retrieve relevant documents from Mencius texts when useful
        context_docs = []
        if should_use_rag(request.question):
            try:
                context_docs = await retriever.retrieve(request.question, top_k=request.top_k)
                logger.info(f"Retrieved {len(context_docs)} relevant documents")
            except Exception as e:
                logger.error(f"Failed to retrieve documents: {str(e)}")
                context_docs = []
        else:
            logger.info("Skipped RAG retrieval for casual/contextual chat")
        
        # Step 2: Generate response using GLM-4 with Mencius character
        response_text = None
        llm_error = None
        try:
            response_text = await glm_client.generate_response(
                user_question=request.question,
                context=context_docs,
                history=[message.model_dump() for message in request.history]
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
            fallback_answer = "我眼下没法细说，只能先把想起的几段话摆出来：\n\n"
            for i, doc in enumerate(context_docs, 1):
                text = doc.get("text", "").strip()
                if text:
                    fallback_answer += f"其{i}：{text}\n\n"
            
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
