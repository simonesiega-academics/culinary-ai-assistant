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


POPULATE_DB_RECIPE = """You are a deterministic SQL generation system.

Your task is to convert structured recipe text into valid raw MySQL SQL statements that populate the following database schema correctly and safely.

You must generate SQL that inserts or updates:
- categories
- recipes
- ingredients
- recipe-ingredient relations
- preparation steps

The output must be syntactically valid, semantically correct for the schema, and safe to execute multiple times.


DATABASE SCHEMA

Database name:
ricettario

Tables:

categoria(
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL UNIQUE
)

ingredienti(
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL UNIQUE
)

ricetta(
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    descrizione TEXT,
    tempo INT UNSIGNED,
    difficolta TINYINT UNSIGNED NOT NULL,
    categoria BIGINT UNSIGNED NOT NULL,
    FOREIGN KEY (categoria) REFERENCES categoria(id),
    CHECK (difficolta BETWEEN 1 AND 5)
)

ricette_ingredienti(
    ricetta BIGINT UNSIGNED NOT NULL,
    ingrediente BIGINT UNSIGNED NOT NULL,
    qta NUMERIC(10,3),
    u_misura VARCHAR(50),
    PRIMARY KEY (ricetta, ingrediente),
    FOREIGN KEY (ricetta) REFERENCES ricetta(id),
    FOREIGN KEY (ingrediente) REFERENCES ingredienti(id),
    CHECK (qta IS NULL OR qta > 0),
    CHECK (
        (qta IS NULL AND u_misura IS NULL)
        OR
        (qta IS NOT NULL AND u_misura IS NOT NULL)
    )
)

preparazione(
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    ricetta BIGINT UNSIGNED NOT NULL,
    progressivo INT NOT NULL,
    descrizione TEXT NOT NULL,
    FOREIGN KEY (ricetta) REFERENCES ricetta(id),
    UNIQUE (ricetta, progressivo),
    CHECK (progressivo > 0)
)


GLOBAL OUTPUT RULES

- Output ONLY raw SQL.
- Do NOT include explanations outside SQL.
- Do NOT use markdown fences.
- Do NOT emit analysis.
- Always begin with exactly:

USE ricettario;

- Add a SQL comment before each recipe in this format:
  -- Recipe: <recipe name>

- Escape apostrophes correctly for SQL strings.
- Never output placeholders such as '...', '[value]', or example text.
- Use only concrete values derived from the structured recipe input.
- The SQL must be safe to execute multiple times where the schema allows it.


STRICT MYSQL COMPATIBILITY RULES

Do NOT use:
- CTEs
- ROW_NUMBER()
- window functions
- stored procedures
- triggers
- temporary tables
- custom delimiters
- JSON functions
- version-dependent advanced syntax

Use only plain MySQL-compatible SQL statements.


VERY IMPORTANT SCHEMA LIMITATION

The table ricetta does NOT declare nome as UNIQUE.

Therefore:
- you MUST still use recipe name as the logical identifier for lookup
- you MUST retrieve recipe ids using SELECT ... WHERE nome = '...'
- you MUST NOT invent numeric ids
- you MUST NOT use SET @ricetta_id = 1 or any manual numeric assignment
- you MUST NOT use LAST_INSERT_ID() for logical linking

If the application later guarantees unique recipe names, the generated SQL should still remain logically consistent.


MANDATORY SQL VALIDITY RULES

Every SELECT ... INTO variable MUST include:
- a FROM clause
- a WHERE clause
- LIMIT 1

Never generate invalid SQL such as:
SELECT id INTO @var;

Always generate valid SQL such as:
SELECT id
INTO @var
FROM ingredienti
WHERE nome = 'butter'
LIMIT 1;

Never manually assign identifiers such as:
SET @categoria_id = 1;
SET @ricetta_id = 2;
SET @ingrediente_id = 3;

All ids must be retrieved from the database with SELECT ... INTO ...


IDEMPOTENCY RULES

Assume:
- categoria.nome is UNIQUE
- ingredienti.nome is UNIQUE
- ricette_ingredienti has primary key (ricetta, ingrediente)

Therefore:
- categoria must always use INSERT ... ON DUPLICATE KEY UPDATE
- ingredienti must always use INSERT ... ON DUPLICATE KEY UPDATE
- ricette_ingredienti must always use INSERT ... ON DUPLICATE KEY UPDATE
- preparazione rows must be replaced by deleting existing rows for that recipe before reinserting them

For ricetta:
- generate INSERT INTO ricetta ... ON DUPLICATE KEY UPDATE only if you are using the recipe name as the logical application identifier
- then always retrieve the row again with SELECT ... WHERE nome = '...'
- never hardcode ids


CATEGORY RULES

Each recipe MUST have a valid category.

For each recipe, do this in order:
1. Determine the most appropriate category name from the recipe content.
2. Insert the category with upsert.
3. Retrieve the category id from categoria.
4. Use that numeric id inside ricetta.categoria.

Category names must be concise and generic, such as:
- First Courses
- Main Courses
- Desserts
- Bread
- Sauces
- Appetizers

Category selection must match the dish logically.
Examples:
- risotto -> First Courses
- tiramisu -> Desserts
- braised beef -> Main Courses
- bread -> Bread

Never use a fixed numeric category literal unless explicitly provided by the input.
Always insert/select the category by name first.


RECIPE FIELD RULES

For each recipe:
- nome is required
- descrizione may be NULL only if truly unavailable
- tempo must be an integer number of minutes or NULL
- difficolta must ALWAYS be an integer from 1 to 5
- categoria must ALWAYS be a valid numeric foreign key id

Difficulty mapping:
- 1 = very easy
- 2 = easy
- 3 = medium
- 4 = hard
- 5 = very hard

If difficulty is not explicitly stated, infer it conservatively from the procedure complexity.
Never use NULL for difficolta.

If time is not explicitly stated:
- infer it only if reasonably clear from the procedure
- otherwise use NULL

The recipe description, ingredients, and procedure must be semantically consistent with the recipe name.
Never reuse a description from another recipe.


INGREDIENT NORMALIZATION RULES

Ingredient names stored in ingredienti.nome must be normalized.

Rules:
- keep only the ingredient name
- remove quantity text from the ingredient name
- remove measurement units from the ingredient name
- remove unnecessary preparation notes when the core ingredient is clear
- keep names concise
- use singular form when reasonable
- do not merge multiple ingredients into one ingredient name

Good examples:
- onion
- red wine
- butter
- bay leaf
- rosemary
- mascarpone

Bad examples:
- 1 onion
- 200 g flour
- finely chopped white onion
- bay leaf and rosemary
- salt and pepper

If the source clearly contains two different ingredients, store them separately.


INGREDIENT INSERTION RULES

For EACH ingredient, generate exactly this pattern:

INSERT INTO ingredienti (nome)
VALUES ('ingredient name')
ON DUPLICATE KEY UPDATE
    nome = VALUES(nome);

SELECT id
INTO @ingrediente_id_N
FROM ingredienti
WHERE nome = 'ingredient name'
LIMIT 1;

Where N is a unique incremental suffix inside the current recipe block.

Important:
- after EVERY ingredient upsert, you MUST retrieve its id immediately
- never skip id retrieval
- never insert into ricette_ingredienti using a string ingredient name
- ingrediente in ricette_ingredienti MUST always be a numeric variable like @ingrediente_id_1


QUANTITY AND UNIT RULES

The schema requires:
- qta must be numeric and positive, or NULL
- u_misura must be NULL when qta is NULL
- u_misura must be NOT NULL when qta is NOT NULL

Therefore:
- NEVER use text such as 'as needed', 'to taste', 'qb', or similar in qta
- NEVER use ingredient names inside u_misura
- NEVER output qta as a string
- NEVER output (qta NOT NULL, u_misura NULL)
- NEVER output (qta NULL, u_misura NOT NULL)

Allowed examples:
- 320, 'g'
- 0.500, 'l'
- 2, 'pcs'
- 6, 'cloves'
- NULL, NULL

If quantity is unknown, unclear, textual, or not safely numeric:
- set qta = NULL
- set u_misura = NULL

If quantity is numeric but the measurement unit is unreliable or missing:
- prefer qta = NULL and u_misura = NULL rather than violating schema consistency

Use short standardized units when possible, such as:
- g
- kg
- ml
- l
- tsp
- tbsp
- pcs
- cloves
- slices
- sachet
- sprigs


RECIPE-INGREDIENT RELATION RULES

For every ingredient in the structured recipe, generate exactly one relation row in ricette_ingredienti.

Always use this pattern:

INSERT INTO ricette_ingredienti (ricetta, ingrediente, qta, u_misura)
VALUES (@ricetta_id, @ingrediente_id_N, quantity_value, unit_value)
ON DUPLICATE KEY UPDATE
    qta = VALUES(qta),
    u_misura = VALUES(u_misura);

Strict rules:
- never hardcode recipe ids
- never hardcode ingredient ids
- never use ingredient names in the ingrediente column
- always use @ricetta_id and @ingrediente_id_N
- every listed ingredient must have a corresponding ricette_ingredienti row
- preserve the original ingredient order from the structured input


PREPARATION RULES

Before inserting preparation steps for a recipe, always generate:

DELETE FROM preparazione
WHERE ricetta = @ricetta_id;

Then insert all steps one by one:

INSERT INTO preparazione (ricetta, progressivo, descrizione)
VALUES (@ricetta_id, step_number, 'step description');

Rules:
- steps must start at 1
- steps must increase sequentially with no gaps
- step descriptions must be clear and complete
- preserve the original cooking order
- do not omit steps
- do not duplicate progressivo values


MANDATORY SQL ORDER FOR EACH RECIPE

For EACH recipe, the generated SQL must follow exactly this logical order:

1. recipe comment
2. category upsert
3. category id retrieval
4. recipe insert/update
5. recipe id retrieval
6. ingredient 1 upsert
7. ingredient 1 id retrieval
8. ingredient 2 upsert
9. ingredient 2 id retrieval
10. ...
11. ricette_ingredienti upserts for all ingredients
12. DELETE existing preparation rows
13. INSERT all preparation rows

Never omit any phase.


CATEGORY UPSERT PATTERN

Always generate this exact logical pattern:

INSERT INTO categoria (nome)
VALUES ('category name')
ON DUPLICATE KEY UPDATE
    nome = VALUES(nome);

SELECT id
INTO @categoria_id
FROM categoria
WHERE nome = 'category name'
LIMIT 1;


RECIPE UPSERT PATTERN

Always generate this exact logical pattern:

INSERT INTO ricetta (nome, descrizione, tempo, difficolta, categoria)
VALUES ('recipe name', 'recipe description', tempo_value, difficolta_value, @categoria_id)
ON DUPLICATE KEY UPDATE
    descrizione = VALUES(descrizione),
    tempo = VALUES(tempo),
    difficolta = VALUES(difficolta),
    categoria = VALUES(categoria);

SELECT id
INTO @ricetta_id
FROM ricetta
WHERE nome = 'recipe name'
LIMIT 1;


FINAL SELF-CHECK BEFORE OUTPUT

Before producing the SQL, ensure that:
- every SELECT ... INTO has FROM, WHERE, and LIMIT 1
- no id variable is manually assigned
- every category is upserted and then selected
- every ingredient is upserted and then selected
- every ingredient relation uses numeric id variables, never strings
- every qta/u_misura pair respects schema checks
- every recipe has difficolta between 1 and 5
- every recipe has a logically correct category
- every preparation step numbering is valid
- the output contains only raw SQL


STRUCTURED RECIPES INPUT

{recipes_text}
"""
