"""
Recipe processing prompts for extracting and formatting culinary recipes from PDF text.

This module contains the prompt templates used to interact with the LLM
for parsing recipe content from raw PDF text.
"""

from __future__ import annotations

# RECIPE SPLITTING PROMPT
# This prompt instructs the LLM to:
# 1. Analyze a PDF text containing one or more recipes
# 2. Split the text into individual recipes
# 3. Extract and format: NAME, DESCRIPTION, and numbered STEPS for each recipe

RECIPE_SPLIT_PROMPT = """Analyze the following text which contains one or more culinary recipes. 
Split the text into individual recipes. For each recipe, extract and format:

1. **NAME**: the recipe name
2. **DESCRIPTION**: a brief description of the recipe (2-3 sentences)
3. **STEPS**: the preparation steps numbered sequentially

Use this exact format for each recipe:

---SEPARATE_RECIPE---
NAME: [recipe name]

DESCRIPTION: [description]

STEPS:
1. [step 1]
2. [step 2]
3. [step 3]
...
---SEPARATE_RECIPE---

Text to analyze:
{pdf_text}
"""
