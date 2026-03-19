from __future__ import annotations

import io
import re

from langchain_ollama import ChatOllama
from pypdf import PdfReader

from app.core.config import Settings
from app.models.recipe import AnalysisBatch, StructuredRecipe
from app.prompts import RECIPE_SPLIT_PROMPT


RECIPE_SEPARATOR = "---SEPARATE_RECIPE---"


class AgentOneAnalyzer:
    """Agent 1: receives PDF input and returns structured recipes."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._llm = self._create_llm()

    def analyze_pdf(self, pdf_bytes: bytes, source_name: str) -> AnalysisBatch:
        pdf_text = self._extract_pdf_text(pdf_bytes)
        blocks = self._extract_recipe_blocks(pdf_text)

        recipes = [
            self._parse_recipe_block(block, index)
            for index, block in enumerate(blocks, start=1)
        ]
        recipes = [recipe for recipe in recipes if recipe.name]

        if not recipes:
            recipes = [self._fallback_recipe(pdf_text, source_name)]

        return AnalysisBatch(source=source_name, recipes=recipes)

    def _create_llm(self) -> ChatOllama | None:
        if not self._settings.agent1_use_llm:
            return None

        llm_kwargs = {
            "model": self._settings.ollama_model,
            "temperature": 0,
        }
        if self._settings.ollama_base_url:
            llm_kwargs["base_url"] = self._settings.ollama_base_url

        return ChatOllama(**llm_kwargs)

    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        if not pdf_bytes:
            raise ValueError("The uploaded PDF is empty.")

        reader = PdfReader(io.BytesIO(pdf_bytes))
        page_texts = [page.extract_text() or "" for page in reader.pages]
        combined_text = "\n".join(page_texts).strip()

        if not combined_text:
            raise ValueError("The PDF does not contain readable text.")

        return combined_text

    def _extract_recipe_blocks(self, pdf_text: str) -> list[str]:
        if self._llm is None:
            return [pdf_text]

        prompt = RECIPE_SPLIT_PROMPT.format(pdf_text=pdf_text)

        try:
            response = self._llm.invoke(prompt)
            content = getattr(response, "content", "")
            if not isinstance(content, str):
                content = str(content)
            blocks = [chunk.strip() for chunk in content.split(RECIPE_SEPARATOR) if chunk.strip()]
            return blocks or [pdf_text]
        except Exception:
            return [pdf_text]

    def _parse_recipe_block(self, block: str, index: int) -> StructuredRecipe:
        name = ""
        time_minutes: int | None = None
        difficulty: int | None = None

        description_lines: list[str] = []
        ingredients: list[str] = []
        procedure_steps: list[str] = []
        section: str | None = None

        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            upper_line = line.upper()
            if upper_line.startswith("NAME:"):
                section = None
                name = line.split(":", maxsplit=1)[1].strip()
                continue

            if upper_line.startswith("TIME_MINUTES:"):
                section = None
                value = line.split(":", maxsplit=1)[1].strip()
                time_minutes = self._parse_optional_int(value)
                continue

            if upper_line.startswith("DIFFICULTY:"):
                section = None
                value = line.split(":", maxsplit=1)[1].strip()
                difficulty = self._parse_optional_int(value)
                continue

            if upper_line.startswith("INGREDIENTS:"):
                section = "ingredients"
                continue

            if upper_line.startswith("DESCRIPTION:"):
                section = "description"
                text = line.split(":", maxsplit=1)[1].strip()
                if text:
                    description_lines.append(text)
                continue

            if upper_line.startswith("PROCEDURE:"):
                section = "procedure"
                continue

            if section == "ingredients":
                ingredient = line.lstrip("- ").strip()
                if ingredient:
                    ingredients.append(ingredient)
                continue

            if section == "description":
                description_lines.append(line)
                continue

            if section == "procedure":
                step = re.sub(r"^\d+[\)\.-]?\s*", "", line).strip()
                if step:
                    procedure_steps.append(step)

        if not name:
            name = f"Ricetta importata {index}"

        if not ingredients:
            ingredients = self._extract_bullets(block)

        if not procedure_steps:
            procedure_steps = self._extract_numbered_steps(block)

        normalized_difficulty = None
        if difficulty is not None:
            normalized_difficulty = max(1, min(5, difficulty))

        if time_minutes is not None and time_minutes < 0:
            time_minutes = None

        description = " ".join(description_lines).strip() or None

        return StructuredRecipe(
            name=name,
            description=description,
            time_minutes=time_minutes,
            difficulty=normalized_difficulty,
            ingredients=ingredients,
            procedure_steps=procedure_steps,
        )

    def _fallback_recipe(self, pdf_text: str, source_name: str) -> StructuredRecipe:
        lines = [line.strip() for line in pdf_text.splitlines() if line.strip()]
        fallback_name = lines[0] if lines else f"Ricetta da {source_name}"
        fallback_description = " ".join(lines[:4]).strip() if lines else None

        return StructuredRecipe(
            name=fallback_name[:120],
            description=(fallback_description[:500] if fallback_description else None),
            time_minutes=None,
            difficulty=3,
            ingredients=[],
            procedure_steps=[],
        )

    @staticmethod
    def _extract_bullets(text: str) -> list[str]:
        bullets = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line.startswith("-"):
                normalized = line.lstrip("- ").strip()
                if normalized:
                    bullets.append(normalized)
        return bullets

    @staticmethod
    def _extract_numbered_steps(text: str) -> list[str]:
        steps = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if re.match(r"^\d+[\)\.-]?\s+", line):
                step = re.sub(r"^\d+[\)\.-]?\s+", "", line).strip()
                if step:
                    steps.append(step)
        return steps

    @staticmethod
    def _parse_optional_int(value: str) -> int | None:
        normalized = value.strip().upper()
        if not normalized or normalized == "NULL":
            return None

        match = re.search(r"-?\d+", normalized)
        if not match:
            return None

        try:
            return int(match.group())
        except ValueError:
            return None
