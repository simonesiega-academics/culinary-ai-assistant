"""
Prompt templates for recipe extraction and SQL generation.
"""

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

Strict rules:
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

Example for a single recipe document:
---SEPARATE_RECIPE---
NAME: Saffron Risotto
TIME_MINUTES: 60
DIFFICULTY: 3

INGREDIENTS:
- 320 g Carnaroli rice
- 1 sachet saffron
- 1 liter hot broth
- 1 white onion
- 0.5 glass white wine
- 50 g butter
- 60 g Parmigiano Reggiano

DESCRIPTION: Traditional saffron risotto with a creamy texture obtained by gradual broth addition and final mantecatura.

PROCEDURE:
1. Prepare the broth and keep it hot.
2. Sweat the onion gently.
---SEPARATE_RECIPE---

Text:
{pdf_text}
"""


SQL_RECIPE_BLOCK_PROMPT = """You generate MySQL SQL for ONE recipe only.

You will receive:
1. the real database schema
2. one already-structured recipe

Output rules:
- Output ONLY raw SQL.
- Do NOT use markdown fences.
- Do NOT output USE ricettario; because it is added elsewhere.
- Do NOT add explanations.
- Generate SQL for exactly one recipe.
- The SQL must be idempotent.
- Follow the schema constraints exactly.
- It is better to output fewer assumptions than invalid SQL.

Schema:
{schema_sql}

Recipe:
{recipe_text}

The recipe text contains these fields when available:
- NAME
- TIME_MINUTES
- DIFFICULTY
- INGREDIENTS
- DESCRIPTION
- PROCEDURE

Required SQL order for this recipe:
1. -- Recipe: <name>
2. upsert category
3. select @categoria_id
4. upsert recipe into ricetta using nome as unique key
5. select @ricetta_id
6. for each ingredient: upsert ingredient, then select its id into @ingrediente_id_N
7. insert/update ricette_ingredienti for all ingredients
8. delete old preparation rows for @ricetta_id
9. insert preparation rows with progressivo 1..N

Critical ingredient coverage rule:
- Every bullet under INGREDIENTS must appear in SQL exactly once in `ricette_ingredienti`.
- Do not omit any ingredient from the structured recipe.
- If INGREDIENTS contains 7 bullets, the SQL must create 7 ingredient rows and 7 `ricette_ingredienti` rows.
- Ingredients mentioned in the procedure do NOT replace the ingredient list; the ingredient list is the source of truth.
- For the test recipe `Saffron Risotto`, if the ingredient bullets include `1 sachet saffron` and `1 liter hot broth`, both MUST appear in SQL.

Rules:
- Use table and column names exactly as in the schema.
- Escape apostrophes correctly.
- Choose one sensible category name in Italian.
- If TIME_MINUTES is present and numeric, use it directly for ricetta.tempo.
- If DIFFICULTY is present and numeric, use it directly for ricetta.difficolta.
- difficolta must always be an integer 1..5.
- tempo must be an integer minutes value or NULL.
- ingredienti.nome must contain only the normalized ingredient name, without quantity/unit.
- IMPORTANT CHECK CONSTRAINT:
  - if qta is NULL, u_misura must be NULL
  - if qta is NOT NULL, u_misura must be NOT NULL
  - therefore these are INVALID and must never appear:
    - (320, NULL)
    - (1, NULL)
    - (0.5, NULL)
- In ricette_ingredienti, if quantity is unclear, use qta = NULL and u_misura = NULL.
- If qta is numeric, you must also provide a unit string.
- Extract quantity and unit from each ingredient line whenever present.
- Examples:
  - `320 g Carnaroli rice` -> normalized ingredient `Carnaroli rice`, qta 320, u_misura 'g'
  - `1 sachet saffron` -> normalized ingredient `saffron`, qta 1, u_misura 'sachet'
  - `1 liter hot broth` -> normalized ingredient `broth`, qta 1, u_misura 'l'
  - `1 white onion` -> normalized ingredient `white onion`, qta 1, u_misura 'pcs'
  - `0.5 glass white wine` -> normalized ingredient `white wine`, qta 0.5, u_misura 'glass'
  - `50 g butter` -> normalized ingredient `butter`, qta 50, u_misura 'g'
- Normalize common units to these values when possible: 'g', 'kg', 'ml', 'l', 'tsp', 'tbsp', 'pcs', 'cloves', 'slices', 'sachet', 'sprigs', 'glass'.
- Preserve all ingredients from the structured recipe.
- Preserve procedure order.
- Use INSERT ... ON DUPLICATE KEY UPDATE where the schema allows idempotency.
- Never invent numeric ids.
- Always retrieve ids with SELECT ... INTO ... FROM ... WHERE ... LIMIT 1.
- In `ricette_ingredienti.ingrediente` never write literal numbers like `1`, `2`, `3`; always use variables such as `@ingrediente_id_1`.
- After each ingredient upsert, immediately fetch its id into a variable before the next ingredient.

Mandatory SQL patterns:
- categoria must use:
  INSERT INTO categoria (nome)
  VALUES ('...')
  ON DUPLICATE KEY UPDATE
      nome = VALUES(nome);
- ingredienti must use the same upsert pattern.
- ricetta must use ON DUPLICATE KEY UPDATE because `ricetta.nome` is unique in the real schema.
- ricette_ingredienti must use ON DUPLICATE KEY UPDATE on `(ricetta, ingrediente)`.
- Before inserting preparation steps always run:
  DELETE FROM preparazione
  WHERE ricetta = @ricetta_id;

Exact ingredient pattern to imitate:
INSERT INTO ingredienti (nome)
VALUES ('saffron')
ON DUPLICATE KEY UPDATE
    nome = VALUES(nome);

SELECT id
INTO @ingrediente_id_2
FROM ingredienti
WHERE nome = 'saffron'
LIMIT 1;

INSERT INTO ricette_ingredienti (ricetta, ingrediente, qta, u_misura)
VALUES (@ricetta_id, @ingrediente_id_2, 1, 'sachet')
ON DUPLICATE KEY UPDATE
    qta = VALUES(qta),
    u_misura = VALUES(u_misura);

Another exact pattern to imitate:
INSERT INTO ingredienti (nome)
VALUES ('broth')
ON DUPLICATE KEY UPDATE
    nome = VALUES(nome);

SELECT id
INTO @ingrediente_id_3
FROM ingredienti
WHERE nome = 'broth'
LIMIT 1;

INSERT INTO ricette_ingredienti (ricetta, ingrediente, qta, u_misura)
VALUES (@ricetta_id, @ingrediente_id_3, 1, 'l')
ON DUPLICATE KEY UPDATE
    qta = VALUES(qta),
    u_misura = VALUES(u_misura);

Before output, check again:
- every ingredient bullet is present in SQL
- no ingredient from the bullet list is missing
- no `(numeric_qta, NULL)` pair exists
- no `ricette_ingredienti.ingrediente` value is a hardcoded integer
- all needed `ON DUPLICATE KEY UPDATE` clauses are present
- SQL starts with `-- Recipe: <name>` and contains only one recipe block

Return only the SQL block for this recipe.
"""
