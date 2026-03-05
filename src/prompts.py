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
# 3. Extract and format: NAME, DESCRIPTION, INGREDIENTS, and PROCEDURE

RECIPE_SPLIT_PROMPT = """Analyze the following text which contains one or more culinary recipes. 
Split the text into individual recipes. For each recipe, extract and format:

1. **NAME**: the recipe name
2. **DESCRIPTION**: a brief description of the recipe (2-3 sentences)
3. **INGREDIENTS**: list all ingredients required
4. **PROCEDURE**: the preparation steps numbered sequentially

Use this exact format for each recipe:

---SEPARATE_RECIPE---
NAME: [recipe name]

DESCRIPTION: [description]

INGREDIENTS:
- [ingredient 1]
- [ingredient 2]
- [ingredient 3]
...

PROCEDURE:
1. [step 1]
2. [step 2]
3. [step 3]
...
---SEPARATE_RECIPE---

Text to analyze:
{pdf_text}
"""

# SQL INSERT PROMPT
# This prompt instructs the LLM to generate SQL INSERT statements
# from the structured recipe data (NAME, DESCRIPTION, INGREDIENTS, PROCEDURE)

SQL_INSERT_PROMPT = """
Generate MariaDB SQL statements to populate the recipe database.

IMPORTANT RULES:
- Output ONLY SQL. Do NOT include explanations or markdown.
- The SQL must execute in MariaDB without manual edits.
- The script must be idempotent (running it multiple times must not create duplicates).
- Do NOT use window functions (NO ROW_NUMBER, NO OVER).
- Always escape single quotes using doubled quotes (example: it''s).
- Ingredient names must be unique and normalized (no quantities inside ingredient names).
- Recipe steps must be sequentially numbered starting from 1.

For each recipe you MUST:

1. Insert ingredients using:
   INSERT INTO ingredients (name)
   VALUES (...)
   ON DUPLICATE KEY UPDATE name = VALUES(name);

2. Insert the recipe using:
   INSERT INTO recipes (name, description)
   VALUES (...)
   ON DUPLICATE KEY UPDATE
       description = VALUES(description),
       archived_at = NULL;

3. Retrieve the recipe id using:
   SELECT id INTO @recipe_id FROM recipes WHERE name = '<recipe name>' LIMIT 1;

4. Remove existing relations:
   DELETE FROM recipe_ingredients WHERE recipe_id = @recipe_id;
   DELETE FROM recipe_steps WHERE recipe_id = @recipe_id;

5. Insert recipe ingredients using a derived table that explicitly defines sort_order.

6. Insert procedure steps using @recipe_id and sequential step numbers.

Output format MUST be exactly:

---SQL_RECIPE---
-- Recipe: <name>

-- Ingredients
INSERT INTO ingredients (name) VALUES
  ('ingredient1'),
  ('ingredient2')
ON DUPLICATE KEY UPDATE name = VALUES(name);

-- Recipe
INSERT INTO recipes (name, description) VALUES
  ('<name>', '<description>')
ON DUPLICATE KEY UPDATE
  description = VALUES(description),
  archived_at = NULL;

SELECT id INTO @recipe_id FROM recipes WHERE name = '<name>' LIMIT 1;

DELETE FROM recipe_ingredients WHERE recipe_id = @recipe_id;
DELETE FROM recipe_steps WHERE recipe_id = @recipe_id;

-- Ingredient links
INSERT INTO recipe_ingredients (recipe_id, ingredient_id, amount, unit, ingredient_note, sort_order)
SELECT @recipe_id, i.id, v.amount, v.unit, v.note, v.sort_order
FROM (
  SELECT 1 AS sort_order, '<ingredient1>' AS name, NULL AS amount, NULL AS unit, NULL AS note
  UNION ALL SELECT 2, '<ingredient2>', NULL, NULL, NULL
) v
JOIN ingredients i ON i.name = v.name
ORDER BY v.sort_order;

-- Steps
INSERT INTO recipe_steps (recipe_id, step_no, instruction) VALUES
  (@recipe_id, 1, '<step1>'),
  (@recipe_id, 2, '<step2>');
---SQL_RECIPE---

Generate SQL for the following recipes:

{recipes_text}
"""
