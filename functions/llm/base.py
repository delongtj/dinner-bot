from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def extract_recipe_metadata(self, url: str = None, text: str = None) -> Dict[str, Any]:
        """
        Extract recipe metadata from URL or raw text.
        
        Returns dict with: title, prep_time, cook_time, servings, 
        ingredients, instructions, cuisine_type, meal_type, complexity, 
        dietary_flags, seasonal_relevance
        """
        pass
    
    @abstractmethod
    def generate_meal_plans(
        self,
        recipes: List[Dict[str, Any]],
        preferences: Dict[str, Any],
        calendar_constraints: Dict[str, Any],
        num_plans: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple meal plans.
        
        Returns list of meal plans, each with a dict mapping:
        { "Monday": { "recipe_id": "...", "recipe_name": "...", "notes": "..." }, ... }
        """
        pass
    
    @abstractmethod
    def rank_recipes(
        self,
        recipes: List[Dict[str, Any]],
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Rank recipes by fit to preferences.
        Returns recipes sorted by relevance.
        """
        pass
