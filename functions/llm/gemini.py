import os
import json
from typing import Any, Dict, List
import google.generativeai as genai

from llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    """Gemini API implementation of LLMProvider."""
    
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-pro")
    
    def extract_recipe_metadata(self, url: str = None, text: str = None) -> Dict[str, Any]:
        """Extract recipe metadata using Gemini."""
        if not url and not text:
            raise ValueError("Either url or text must be provided")
        
        if url:
            prompt = f"""
            Extract recipe metadata from this URL: {url}
            
            Return a JSON object with these fields:
            - title: string
            - prep_time: number (minutes, 0 if unknown)
            - cook_time: number (minutes, 0 if unknown)
            - servings: number
            - ingredients: string (comma-separated list)
            - instructions: string
            - cuisine_type: array of strings
            - meal_type: "breakfast" | "lunch" | "dinner"
            - complexity: "quick" | "moderate" | "involved"
            - dietary_flags: array of strings (vegetarian, vegan, dairy-free, keto, etc.)
            - seasonal_relevance: "spring" | "summer" | "fall" | "winter" | "any"
            
            Return ONLY valid JSON, no other text.
            """
        else:
            prompt = f"""
            Extract recipe metadata from this text:
            
            {text}
            
            Return a JSON object with these fields:
            - title: string
            - prep_time: number (minutes, 0 if unknown)
            - cook_time: number (minutes, 0 if unknown)
            - servings: number
            - ingredients: string (comma-separated list)
            - instructions: string
            - cuisine_type: array of strings
            - meal_type: "breakfast" | "lunch" | "dinner"
            - complexity: "quick" | "moderate" | "involved"
            - dietary_flags: array of strings (vegetarian, vegan, dairy-free, keto, etc.)
            - seasonal_relevance: "spring" | "summer" | "fall" | "winter" | "any"
            
            Return ONLY valid JSON, no other text.
            """
        
        response = self.model.generate_content(prompt)
        result = json.loads(response.text)
        return result
    
    def generate_meal_plans(
        self,
        recipes: List[Dict[str, Any]],
        preferences: Dict[str, Any],
        calendar_constraints: Dict[str, Any],
        num_plans: int = 4
    ) -> List[Dict[str, Any]]:
        """Generate meal plans using Gemini."""
        recipes_json = json.dumps(recipes, indent=2)
        preferences_json = json.dumps(preferences, indent=2)
        constraints_json = json.dumps(calendar_constraints, indent=2)
        
        prompt = f"""
        Generate {num_plans} diverse meal plans for the week (Monday-Sunday).
        
        Available recipes:
        {recipes_json}
        
        User preferences:
        {preferences_json}
        
        Calendar constraints (busy days needing quick meals):
        {constraints_json}
        
        For each plan, return a JSON object mapping day names to recipe selections:
        {{
          "Monday": {{"recipe_id": "uuid", "recipe_name": "name", "notes": "optional"}},
          "Tuesday": {{"recipe_id": "uuid", "recipe_name": "name", "notes": "optional"}},
          ...
        }}
        
        Return {num_plans} complete meal plans (one per line, valid JSON only).
        """
        
        response = self.model.generate_content(prompt)
        lines = response.text.strip().split('\n')
        plans = []
        for line in lines:
            if line.strip():
                try:
                    plan = json.loads(line)
                    plans.append(plan)
                except json.JSONDecodeError:
                    continue
        
        return plans[:num_plans]
    
    def rank_recipes(
        self,
        recipes: List[Dict[str, Any]],
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Rank recipes by fit to preferences using Gemini."""
        recipes_json = json.dumps(recipes, indent=2)
        preferences_json = json.dumps(preferences, indent=2)
        
        prompt = f"""
        Rank these recipes by how well they fit the user preferences.
        
        Recipes:
        {recipes_json}
        
        Preferences:
        {preferences_json}
        
        Return the recipes sorted by relevance (best first), as a valid JSON array.
        Include all original fields plus a "score" field (0-100).
        """
        
        response = self.model.generate_content(prompt)
        ranked = json.loads(response.text)
        return ranked
