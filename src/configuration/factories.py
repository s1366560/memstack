import logging
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMConfig, OpenAIClient
from graphiti_core.llm_client.gemini_client import GeminiClient
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.gemini_reranker_client import GeminiRerankerClient
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient

from src.infrastructure.llm.qwen.qwen_client import QwenClient
from src.infrastructure.llm.qwen.qwen_embedder import QwenEmbedder, QwenEmbedderConfig
from src.infrastructure.llm.qwen.qwen_reranker_client import QwenRerankerClient

from src.configuration.config import get_settings

logger = logging.getLogger(__name__)

def create_graphiti_client() -> Graphiti:
    settings = get_settings()
    provider = settings.llm_provider.strip().lower()

    if provider == "qwen":
        logger.info("Initializing Graphiti with Qwen LLM, Embedder and Reranker")
        
        llm_config = LLMConfig(
            api_key=settings.qwen_api_key,
            model=settings.qwen_model,
            small_model=settings.qwen_small_model,
            base_url=settings.qwen_base_url,
        )
        llm_client = QwenClient(config=llm_config)
        
        embedder_config = QwenEmbedderConfig(
            api_key=settings.qwen_api_key,
            embedding_model=settings.qwen_embedding_model,
            base_url=settings.qwen_base_url,
        )
        embedder = QwenEmbedder(config=embedder_config)
        
        reranker_config = LLMConfig(
            api_key=settings.qwen_api_key,
            model="qwen-turbo",
            base_url=settings.qwen_base_url,
        )
        reranker = QwenRerankerClient(config=reranker_config)

    elif provider == "openai":
        logger.info("Initializing Graphiti with OpenAI LLM, Embedder and Reranker")
        
        llm_config = LLMConfig(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            small_model=settings.openai_small_model,
            base_url=settings.openai_base_url,
        )
        llm_client = OpenAIClient(config=llm_config)
        
        embedder_config = OpenAIEmbedderConfig(
            api_key=settings.openai_api_key,
            embedding_model=settings.openai_embedding_model,
            base_url=settings.openai_base_url,
        )
        embedder = OpenAIEmbedder(config=embedder_config)
        
        reranker_config = LLMConfig(
            api_key=settings.openai_api_key,
            model=settings.openai_small_model,
            base_url=settings.openai_base_url,
        )
        reranker = OpenAIRerankerClient(config=reranker_config)
        
    else:
        # Default to Gemini
        logger.info("Initializing Graphiti with Gemini LLM, Embedder and Reranker")
        
        llm_config = LLMConfig(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )
        llm_client = GeminiClient(config=llm_config)
        
        embedder_config = GeminiEmbedderConfig(
            api_key=settings.gemini_api_key,
            embedding_model=settings.gemini_embedding_model,
        )
        embedder = GeminiEmbedder(config=embedder_config)
        
        reranker_config = LLMConfig(
            api_key=settings.gemini_api_key,
            model="gemini-2.0-flash-lite",
        )
        reranker = GeminiRerankerClient(config=reranker_config)

    client = Graphiti(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
        llm_client=llm_client,
        embedder=embedder,
        cross_encoder=reranker,
    )
    
    return client
