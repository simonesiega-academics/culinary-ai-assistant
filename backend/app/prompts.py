"""Prompt templates used by backend agents."""

from __future__ import annotations


RECIPE_SPLIT_PROMPT = """You extract structured recipes from PDF/OCR text.

Goal:
- Identify REAL recipes only.
- Keep each recipe separate.
- Ignore document titles, chapter titles, page headers, page footers, indexes, and generic cookbook text.

Very important:
- A document title is NOT a recipe name.
- If the text contains exactly one recipe, output exactly one recipe block.
- Do not create extra recipes from introductory text.
- A valid recipe usually has a title plus ingredients and/or procedure steps.

When present in the source, preserve these fields:
- recipe name
- cooking time
- difficulty
- ingredients
- short description
- procedure steps

Output EXACTLY this structure for each recipe:

---SEPARATE_RECIPE---
NAME: <recipe name>
TIME_MINUTES: <integer minutes or NULL>
DIFFICULTY: <1-5 or NULL>

INGREDIENTS:
- <ingredient line 1>
- <ingredient line 2>

DESCRIPTION: <short summary, max 2 sentences>

PROCEDURE:
1. <step 1>
2. <step 2>
---SEPARATE_RECIPE---

Rules:
- Use the actual dish name, not the document title.
- If the source has labels like "Cooking Time:" or "Difficulty:", use those values.
- Convert time to integer minutes only.
- Convert difficulty to:
  1 = very easy
  2 = easy
  3 = medium
  4 = hard
  5 = very hard
- If time or difficulty are not clearly present, output NULL.
- Keep ingredient quantities and units inside the ingredient line when present.
- Do not drop any ingredient line from the source list.
- If the source ingredient list has 7 ingredients, output 7 ingredient bullet lines.
- Keep ingredient order and procedure order from the source.
- Do not invent missing ingredients, steps, time, or difficulty.
- DESCRIPTION must be short and factual.
- PROCEDURE must contain only numbered preparation steps.
- No markdown fences.
- No commentary.
- No text before the first separator.
- No text after the last separator.

Text:
{pdf_text}
"""
