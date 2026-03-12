CREATE DATABASE IF NOT EXISTS ricettario
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE ricettario;

CREATE TABLE categoria (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(255) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_categoria_nome UNIQUE (nome)
) ENGINE=InnoDB;

CREATE TABLE ingredienti (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(255) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uq_ingredienti_nome UNIQUE (nome)
) ENGINE=InnoDB;

CREATE TABLE ricetta (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome VARCHAR(255) NOT NULL,
    descrizione TEXT,
    tempo INT UNSIGNED,
    difficolta TINYINT UNSIGNED NOT NULL,
    categoria BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_ricetta_categoria
        FOREIGN KEY (categoria)
        REFERENCES categoria (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_ricetta_difficolta_valida
        CHECK (difficolta BETWEEN 1 AND 5)
) ENGINE=InnoDB;

CREATE TABLE ricette_ingredienti (
    ricetta BIGINT UNSIGNED NOT NULL,
    ingrediente BIGINT UNSIGNED NOT NULL,
    qta NUMERIC(10,3),
    u_misura VARCHAR(50),
    PRIMARY KEY (ricetta, ingrediente),
    CONSTRAINT fk_ricette_ingredienti_ricetta
        FOREIGN KEY (ricetta)
        REFERENCES ricetta (id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_ricette_ingredienti_ingrediente
        FOREIGN KEY (ingrediente)
        REFERENCES ingredienti (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT chk_ricette_ingredienti_qta_positiva
        CHECK (qta IS NULL OR qta > 0),
    CONSTRAINT chk_ricette_ingredienti_qta_umisura_coerenti
        CHECK (
            (qta IS NULL AND u_misura IS NULL)
            OR
            (qta IS NOT NULL AND u_misura IS NOT NULL)
        )
) ENGINE=InnoDB;

CREATE TABLE preparazione (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    ricetta BIGINT UNSIGNED NOT NULL,
    progressivo INT NOT NULL,
    descrizione TEXT NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT fk_preparazione_ricetta
        FOREIGN KEY (ricetta)
        REFERENCES ricetta (id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT uq_preparazione_ricetta_progressivo UNIQUE (ricetta, progressivo),
    CONSTRAINT chk_preparazione_progressivo_positivo CHECK (progressivo > 0)
) ENGINE=InnoDB;
