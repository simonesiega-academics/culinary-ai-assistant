from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.recipe import AnalysisBatch
from app.repositories.mariadb_repository import MariaDBRepository


@dataclass
class PersistenceResult:
    source: str
    persisted: int = 0
    failed: int = 0
    recipe_names: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "persisted": self.persisted,
            "failed": self.failed,
            "recipe_names": list(self.recipe_names),
            "errors": list(self.errors),
        }


class AgentTwoDatabaseBridge:
    """Agent 2: receives structured output and persists it in MariaDB."""

    def __init__(self, repository: MariaDBRepository, default_category: str) -> None:
        self._repository = repository
        self._default_category = default_category

    def persist_analysis(self, batch: AnalysisBatch) -> PersistenceResult:
        result = PersistenceResult(source=batch.source)

        for recipe in batch.recipes:
            try:
                self._repository.upsert_recipe(recipe, self._default_category)
                result.persisted += 1
                result.recipe_names.append(recipe.name)
            except Exception as exc:
                result.failed += 1
                result.errors.append(f"{recipe.name}: {exc}")

        return result
