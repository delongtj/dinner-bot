from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def extract_recipe_metadata(self, url: str = None, text: str = None) -> Dict[str, Any]:
        """
        Extract recipe metadata from URL or raw text.
        
        Returns dict with: title, prep_time, cook_time, servings,
        ingredients (list of {name, quantity, unit, category}), instructions,
        cuisine_type, meal_type, complexity, dietary_flags, seasonal_relevance
        """
        pass
    
    @abstractmethod
    def chat_plan(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
    ) -> str:
        """
        Conversational meal-planning turn.

        Args:
            system_prompt: Full system prompt with family context.
            messages: Conversation history [{role, content}, ...].

        Returns the assistant's reply as a string.
        """
        pass

    @abstractmethod
    def extract_plan_from_conversation(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        recipes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Extract a structured meal plan from a planning conversation.

        Returns dict mapping day names to {recipe_id, recipe_name, notes}.
        """
        pass
