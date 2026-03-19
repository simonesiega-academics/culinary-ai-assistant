from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _coerce_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


@dataclass
class StructuredRecipe:
    name: str
    description: str | None = None
    time_minutes: int | None = None
    difficulty: int | None = None
    ingredients: list[str] = field(default_factory=list)
    procedure_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "time_minutes": self.time_minutes,
            "difficulty": self.difficulty,
            "ingredients": list(self.ingredients),
            "procedure_steps": list(self.procedure_steps),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StructuredRecipe":
        name = str(data.get("name", "")).strip()
        if not name:
            raise ValueError("Recipe name is required")

        description_value = data.get("description")
        description = str(description_value).strip() if description_value else None

        ingredients_raw = data.get("ingredients") or []
        ingredients = [str(item).strip() for item in ingredients_raw if str(item).strip()]

        steps_raw = data.get("procedure_steps") or []
        steps = [str(item).strip() for item in steps_raw if str(item).strip()]

        return cls(
            name=name,
            description=description,
            time_minutes=_coerce_optional_int(data.get("time_minutes")),
            difficulty=_coerce_optional_int(data.get("difficulty")),
            ingredients=ingredients,
            procedure_steps=steps,
        )


@dataclass
class AnalysisBatch:
    source: str
    recipes: list[StructuredRecipe] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "recipes": [recipe.to_dict() for recipe in self.recipes],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalysisBatch":
        source = str(data.get("source", "api-payload")).strip() or "api-payload"
        recipe_payloads = data.get("recipes")
        if not isinstance(recipe_payloads, list):
            raise ValueError("recipes must be a list")

        recipes = [StructuredRecipe.from_dict(recipe_data) for recipe_data in recipe_payloads]
        return cls(source=source, recipes=recipes)
