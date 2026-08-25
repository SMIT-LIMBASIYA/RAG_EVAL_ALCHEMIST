"""
LLM Generator engine for RAG answering.
Supports OpenAI (gpt-4o, gpt-4o-mini), Google Gemini (gemini-1.5-pro, gemini-1.5-flash), Groq (llama-3.3-70b-versatile), Anthropic, and local/mock fallback.
"""

from typing import List, Optional
from config import config
from utils.logger import logger

# OpenAI
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Google Gemini
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Groq
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False


class LLMGenerator:
    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        self.provider = (provider or config.LLM_PROVIDER).lower()
        self.model_name = model_name or config.LLM_MODEL_NAME
        self.temperature = temperature if temperature is not None else config.LLM_TEMPERATURE
        self.openai_client = None
        self.groq_client = None
        self._setup()

    def _setup(self):
        if self.provider == "openai" and HAS_OPENAI and config.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        elif self.provider == "gemini" and HAS_GEMINI and config.GEMINI_API_KEY:
            genai.configure(api_key=config.GEMINI_API_KEY)
        elif self.provider == "groq" and HAS_GROQ and config.GROQ_API_KEY:
            self.groq_client = Groq(api_key=config.GROQ_API_KEY)

    def generate_response(self, query: str, contexts: List[str]) -> str:
        """
        Generates grounded response using the retrieved contexts.
        """
        context_block = "\n\n---\n\n".join(contexts) if contexts else "No relevant context found."
        system_prompt = (
            "You are an expert factual assistant specializing in answering questions about The Alchemist by Paulo Coelho.\n"
            "Answer the user question directly, accurately, and concisely using ONLY the facts present in the provided context.\n"
            "Maintain high faithfulness by using the context's exact details. Avoid conversational fluff or markdown formatting."
        )
        user_prompt = f"Context:\n{context_block}\n\nQuestion:\n{query}\n\nAnswer:"

        # 1. OpenAI Generation (gpt-4o / gpt-4o-mini)
        if self.provider == "openai" and self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.temperature
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"OpenAI Generation failed: {e}")

        # 2. Google Gemini Generation (gemini-1.5-pro / gemini-1.5-flash)
        elif self.provider == "gemini" and HAS_GEMINI and config.GEMINI_API_KEY:
            try:
                model = genai.GenerativeModel(self.model_name)
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                response = model.generate_content(full_prompt)
                return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini Generation failed: {e}")

        # 3. Groq Generation
        elif self.provider == "groq" and self.groq_client:
            available_models = []
            try:
                model_list = self.groq_client.models.list()
                available_models = [m.id for m in model_list.data if not any(x in m.id.lower() for x in ["whisper", "guard", "embedding", "tts"])]
            except Exception as e:
                logger.debug(f"Could not list Groq models: {e}")

            models_to_try = [self.model_name] + available_models + [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "llama-3.2-3b-preview",
                "llama-3.2-1b-preview",
                "llama-3.2-11b-vision-preview",
                "qwen-2.5-32b",
                "deepseek-r1-distill-llama-70b",
                "gemma2-9b-it"
            ]
            seen = set()
            unique_models = [m for m in models_to_try if m and not (m in seen or seen.add(m))]

            for m in unique_models:
                try:
                    response = self.groq_client.chat.completions.create(
                        model=m,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=self.temperature
                    )
                    return response.choices[0].message.content.strip()
                except Exception as e:
                    logger.debug(f"Groq model '{m}' failed: {e}. Trying alternative...")
            logger.error("All Groq model attempts failed.")

        # 4. Fallback Synthesizer
        logger.info("Using baseline context extraction generator.")
        if contexts:
            return f"Based on the text: {contexts[0][:300]}..."
        return "I could not find sufficient information in the provided context to answer the question."


_generator_instance: Optional[LLMGenerator] = None


def get_llm_generator() -> LLMGenerator:
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = LLMGenerator()
    return _generator_instance
