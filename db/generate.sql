-- =============================================================================
-- RECIPE DATABASE SCHEMA
-- =============================================================================
-- This schema stores culinary recipes with the following structure:
--   - NAME: Recipe name (recipes.name)
--   - DESCRIPTION: Brief description (recipes.description)
--   - INGREDIENTS: List of ingredients with quantities (ingredients + recipe_ingredients)
--   - PROCEDURE: Step-by-step instructions (recipe_steps)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS recipe_book
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE recipe_book;

-- Main recipes table
-- Stores the core recipe information: name and description
CREATE TABLE IF NOT EXISTS recipes (
  id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name          VARCHAR(255)     NOT NULL,
  description   TEXT            NULL,

  -- Metadata fields for tracking
  created_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  archived_at   TIMESTAMP       NULL,

  PRIMARY KEY (id),
  UNIQUE KEY uq_recipes_name (name),
  KEY idx_recipes_archived_at (archived_at),
  FULLTEXT KEY ft_recipes_name_desc (name, description)
) ENGINE=InnoDB;

-- Ingredient dictionary table
-- Deduplicates ingredients across all recipes (e.g., "flour", "water", "salt")
-- This enables searching and filtering by ingredient
CREATE TABLE IF NOT EXISTS ingredients (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name        VARCHAR(255)     NOT NULL,
  created_at  TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uq_ingredients_name (name)
) ENGINE=InnoDB;

-- Join table: recipe-ingredient relationship
-- Links recipes to their ingredients, storing quantities and units
CREATE TABLE IF NOT EXISTS recipe_ingredients (
  id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  recipe_id       BIGINT UNSIGNED NOT NULL,
  ingredient_id   BIGINT UNSIGNED NOT NULL,

  -- Quantity stored as decimal for precision (e.g., 3.5 g, 350 ml)
  amount         DECIMAL(10,3)    NULL,
  unit           VARCHAR(32)      NULL,     -- e.g., g, ml, tsp, tbsp, cup, piece
  ingredient_note VARCHAR(255)    NULL,     -- e.g., "strong", "very fresh", "room temp"
  sort_order     INT UNSIGNED     NOT NULL DEFAULT 1,

  PRIMARY KEY (id),
  UNIQUE KEY uq_recipe_ingredient_order (recipe_id, sort_order),
  KEY idx_ri_recipe (recipe_id),
  KEY idx_ri_ingredient (ingredient_id),

  CONSTRAINT fk_ri_recipe
    FOREIGN KEY (recipe_id) REFERENCES recipes(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_ri_ingredient
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Procedure steps table
-- Stores ordered step-by-step instructions for each recipe
CREATE TABLE IF NOT EXISTS recipe_steps (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  recipe_id   BIGINT UNSIGNED NOT NULL,
  step_no     INT UNSIGNED    NOT NULL,
  instruction TEXT            NOT NULL,

  PRIMARY KEY (id),
  UNIQUE KEY uq_recipe_step (recipe_id, step_no),
  KEY idx_steps_recipe (recipe_id),

  CONSTRAINT fk_steps_recipe
    FOREIGN KEY (recipe_id) REFERENCES recipes(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Tags table for categorizing recipes
-- Examples: "bread", "fermentation", "rustic", "vegan", "quick"
CREATE TABLE IF NOT EXISTS tags (
  id    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name  VARCHAR(64)     NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_tags_name (name)
) ENGINE=InnoDB;

-- Join table: recipe-tags relationship
CREATE TABLE IF NOT EXISTS recipe_tags (
  recipe_id BIGINT UNSIGNED NOT NULL,
  tag_id    BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (recipe_id, tag_id),
  KEY idx_rt_tag (tag_id),
  CONSTRAINT fk_rt_recipe FOREIGN KEY (recipe_id) REFERENCES recipes(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_rt_tag FOREIGN KEY (tag_id) REFERENCES tags(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Key/value metadata table for recipe parameters
-- Allows storing additional data without schema changes
-- Examples: "fermentation_hours" -> "24", "oven_temp_c" -> "240", "hydration_pct" -> "70"
CREATE TABLE IF NOT EXISTS recipe_meta (
  recipe_id   BIGINT UNSIGNED NOT NULL,
  meta_key    VARCHAR(64)     NOT NULL,
  meta_value  TEXT            NULL,

  PRIMARY KEY (recipe_id, meta_key),
  KEY idx_meta_key (meta_key),

  CONSTRAINT fk_meta_recipe
    FOREIGN KEY (recipe_id) REFERENCES recipes(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;
