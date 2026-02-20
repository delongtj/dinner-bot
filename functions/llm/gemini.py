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
            - ingredients: array of objects, each with:
              - name: string (ingredient name, e.g. "chicken breast")
              - quantity: string (amount, e.g. "2", "1/2", "1.5")
              - unit: string (e.g. "lb", "cup", "tbsp", "oz", "" for count items)
              - category: string (one of: "produce", "meat", "dairy", "pantry", "frozen", "bakery", "spices", "other")
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
            - ingredients: array of objects, each with:
              - name: string (ingredient name, e.g. "chicken breast")
              - quantity: string (amount, e.g. "2", "1/2", "1.5")
              - unit: string (e.g. "lb", "cup", "tbsp", "oz", "" for count items)
              - category: string (one of: "produce", "meat", "dairy", "pantry", "frozen", "bakery", "spices", "other")
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
    
    def chat_plan(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
    ) -> str:
        """Conversational meal-planning turn using Gemini chat."""
        # Build Gemini chat history: prepend system prompt to the first user message
        history = []
        first_user = True
        for msg in messages[:-1]:  # all but the latest message
            role = "user" if msg["role"] == "user" else "model"
            content = msg["content"]
            if first_user and role == "user":
                content = f"{system_prompt}\n\n{content}"
                first_user = False
            history.append({"role": role, "parts": [content]})

        chat = self.model.start_chat(history=history)

        # Send the latest message
        last = messages[-1]
        content = last["content"]
        if first_user:
            content = f"{system_prompt}\n\n{content}"

        response = chat.send_message(content)
        return response.text

    def extract_plan_from_conversation(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        recipes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Extract a structured meal plan from the planning conversation."""
        conversation_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in messages
        )
        recipes_json = json.dumps(
            [{"id": str(r["id"]), "title": r["title"]} for r in recipes],
            indent=2,
        )

        prompt = f"""
        {system_prompt}

        Below is a meal-planning conversation and the family's recipe library.
        Extract the FINAL agreed-upon meal plan from the conversation.

        CONVERSATION:
        {conversation_text}

        AVAILABLE RECIPES (use these IDs):
        {recipes_json}

        Return a JSON object mapping each day to the chosen recipe:
        {{
          "Monday": {{"recipe_id": "<uuid>", "recipe_name": "<title>", "notes": ""}},
          "Tuesday": {{"recipe_id": "<uuid>", "recipe_name": "<title>", "notes": ""}},
          "Wednesday": {{"recipe_id": "<uuid>", "recipe_name": "<title>", "notes": ""}},
          "Thursday": {{"recipe_id": "<uuid>", "recipe_name": "<title>", "notes": ""}},
          "Friday": {{"recipe_id": "<uuid>", "recipe_name": "<title>", "notes": ""}},
          "Saturday": {{"recipe_id": "<uuid>", "recipe_name": "<title>", "notes": ""}},
          "Sunday": {{"recipe_id": "<uuid>", "recipe_name": "<title>", "notes": ""}}
        }}

        Return ONLY valid JSON, no other text.
        """

        response = self.model.generate_content(prompt)
        return json.loads(response.text)
