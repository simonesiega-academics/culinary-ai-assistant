from __future__ import annotations

import re

import mysql.connector

from app.models.recipe import StructuredRecipe


class MariaDBRepository:
    """Low-level data access for recipe persistence in MariaDB/MySQL."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database

    def upsert_recipe(self, recipe: StructuredRecipe, category_name: str) -> None:
        connection = self._connect()
        cursor = connection.cursor()

        try:
            category_id = self._upsert_category(cursor, category_name)
            recipe_id = self._upsert_recipe(cursor, recipe, category_id)

            self._replace_recipe_ingredients(cursor, recipe_id, recipe.ingredients)
            self._replace_recipe_steps(cursor, recipe_id, recipe.procedure_steps)

            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def _connect(self):
        return mysql.connector.connect(
            host=self._host,
            port=self._port,
            user=self._user,
            password=self._password,
            database=self._database,
            autocommit=False,
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
        )

    def _upsert_category(self, cursor, category_name: str) -> int:
        cursor.execute(
            """
            INSERT INTO categoria (nome)
            VALUES (%s)
            ON DUPLICATE KEY UPDATE
                nome = VALUES(nome)
            """,
            (category_name,),
        )

        cursor.execute(
            """
            SELECT id
            FROM categoria
            WHERE nome = %s
            LIMIT 1
            """,
            (category_name,),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Unable to resolve category id")
        return int(row[0])

    def _upsert_recipe(self, cursor, recipe: StructuredRecipe, category_id: int) -> int:
        difficulty = self._sanitize_difficulty(recipe.difficulty)
        time_minutes = recipe.time_minutes if recipe.time_minutes is None or recipe.time_minutes >= 0 else None

        cursor.execute(
            """
            INSERT INTO ricetta (nome, descrizione, tempo, difficolta, categoria)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                descrizione = VALUES(descrizione),
                tempo = VALUES(tempo),
                difficolta = VALUES(difficolta),
                categoria = VALUES(categoria)
            """,
            (recipe.name, recipe.description, time_minutes, difficulty, category_id),
        )

        cursor.execute(
            """
            SELECT id
            FROM ricetta
            WHERE nome = %s
            LIMIT 1
            """,
            (recipe.name,),
        )
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError("Unable to resolve recipe id")
        return int(row[0])

    def _replace_recipe_ingredients(self, cursor, recipe_id: int, ingredients: list[str]) -> None:
        cursor.execute(
            """
            DELETE FROM ricette_ingredienti
            WHERE ricetta = %s
            """,
            (recipe_id,),
        )

        for ingredient_line in ingredients:
            ingredient_name = self._normalize_ingredient_name(ingredient_line)
            if not ingredient_name:
                continue

            cursor.execute(
                """
                INSERT INTO ingredienti (nome)
                VALUES (%s)
                ON DUPLICATE KEY UPDATE
                    nome = VALUES(nome)
                """,
                (ingredient_name,),
            )

            cursor.execute(
                """
                SELECT id
                FROM ingredienti
                WHERE nome = %s
                LIMIT 1
                """,
                (ingredient_name,),
            )
            ingredient_row = cursor.fetchone()
            if ingredient_row is None:
                raise RuntimeError(f"Unable to resolve ingredient id for: {ingredient_name}")

            cursor.execute(
                """
                INSERT INTO ricette_ingredienti (ricetta, ingrediente, qta, u_misura)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    qta = VALUES(qta),
                    u_misura = VALUES(u_misura)
                """,
                (recipe_id, int(ingredient_row[0]), None, None),
            )

    def _replace_recipe_steps(self, cursor, recipe_id: int, steps: list[str]) -> None:
        cursor.execute(
            """
            DELETE FROM preparazione
            WHERE ricetta = %s
            """,
            (recipe_id,),
        )

        for index, step in enumerate(steps, start=1):
            cleaned_step = step.strip()
            if not cleaned_step:
                continue

            cursor.execute(
                """
                INSERT INTO preparazione (ricetta, progressivo, descrizione)
                VALUES (%s, %s, %s)
                """,
                (recipe_id, index, cleaned_step),
            )

    @staticmethod
    def _sanitize_difficulty(difficulty: int | None) -> int:
        if difficulty is None:
            return 3
        return max(1, min(5, int(difficulty)))

    @staticmethod
    def _normalize_ingredient_name(raw_ingredient: str) -> str:
        value = re.sub(r"^\s*[-*]\s*", "", raw_ingredient).strip()
        value = re.sub(r"\s+", " ", value)

        value = re.sub(
            r"^\d+(?:[\.,]\d+)?\s+(?:g|kg|ml|l|tsp|tbsp|pcs|cloves|slices|sachet|sprigs|glass)\s+",
            "",
            value,
            flags=re.IGNORECASE,
        )

        return value[:255]
