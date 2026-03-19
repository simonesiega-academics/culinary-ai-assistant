"use client";

import { useMemo, useState } from "react";

import { analyzePdf, persistAnalysis, runFullIngestion } from "@/lib/api";
import type { AnalysisBatch, PersistenceResult } from "@/lib/types";

type BusyAction = "analyze" | "persist" | "ingest" | null;

function statusText(action: BusyAction): string {
  if (action === "analyze") {
    return "Agent 1 sta analizzando il PDF...";
  }
  if (action === "persist") {
    return "Agent 2 sta scrivendo su MariaDB...";
  }
  if (action === "ingest") {
    return "Pipeline completa in esecuzione...";
  }
  return "";
}

export function IngestionConsole() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisBatch | null>(null);
  const [persistence, setPersistence] = useState<PersistenceResult | null>(null);
  const [busyAction, setBusyAction] = useState<BusyAction>(null);
  const [error, setError] = useState<string | null>(null);

  const hasAnalysis = Boolean(analysis && analysis.recipes.length);

  const parsedRecipesCount = useMemo(() => analysis?.recipes.length ?? 0, [analysis]);

  async function onAnalyzeClick() {
    if (!selectedFile) {
      setError("Seleziona un PDF prima di avviare Agent 1.");
      return;
    }

    setBusyAction("analyze");
    setError(null);
    setPersistence(null);

    try {
      const result = await analyzePdf(selectedFile);
      setAnalysis(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Analisi non riuscita.";
      setError(message);
    } finally {
      setBusyAction(null);
    }
  }

  async function onPersistClick() {
    if (!analysis) {
      setError("Esegui prima Agent 1 per ottenere i dati strutturati.");
      return;
    }

    setBusyAction("persist");
    setError(null);

    try {
      const result = await persistAnalysis(analysis);
      setPersistence(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Persistenza non riuscita.";
      setError(message);
    } finally {
      setBusyAction(null);
    }
  }

  async function onRunPipelineClick() {
    if (!selectedFile) {
      setError("Seleziona un PDF prima di avviare la pipeline completa.");
      return;
    }

    setBusyAction("ingest");
    setError(null);

    try {
      const result = await runFullIngestion(selectedFile);
      setAnalysis(result.analysis);
      setPersistence(result.persistence);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Pipeline completa non riuscita.";
      setError(message);
    } finally {
      setBusyAction(null);
    }
  }

  return (
    <section className="console-shell">
      <div className="console-header">
        <p className="eyebrow">Flusso Orchestrato</p>
        <h1>Culinary AI Assistant</h1>
        <p>Frontend Next.js + Agent 1 di analisi PDF + Agent 2 di persistenza verso MariaDB.</p>
      </div>

      <div className="panel-grid">
        <article className="panel panel-input">
          <h2>1. Input PDF</h2>
          <p>Carica un documento ricette da inviare al backend Python.</p>
          <label htmlFor="pdf-upload" className="file-label">
            <span>File PDF</span>
            <input
              id="pdf-upload"
              type="file"
              accept="application/pdf"
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null;
                setSelectedFile(file);
                setAnalysis(null);
                setPersistence(null);
                setError(null);
              }}
            />
          </label>

          <div className="file-state">
            {selectedFile ? (
              <>
                <strong>{selectedFile.name}</strong>
                <span>{(selectedFile.size / 1024).toFixed(1)} KB</span>
              </>
            ) : (
              <span>Nessun file selezionato.</span>
            )}
          </div>

          <div className="actions">
            <button
              type="button"
              onClick={onAnalyzeClick}
              disabled={busyAction !== null || !selectedFile}
            >
              Avvia Agent 1
            </button>
            <button
              type="button"
              className="secondary"
              onClick={onPersistClick}
              disabled={busyAction !== null || !hasAnalysis}
            >
              Invia ad Agent 2
            </button>
            <button
              type="button"
              className="ghost"
              onClick={onRunPipelineClick}
              disabled={busyAction !== null || !selectedFile}
            >
              Pipeline Completa
            </button>
          </div>

          {busyAction && <p className="status-badge">{statusText(busyAction)}</p>}
          {error && <p className="error-badge">{error}</p>}
        </article>

        <article className="panel">
          <h2>2. Output Agent 1</h2>
          <p>Ricette strutturate pronte per essere validate o salvate.</p>
          <div className="metric-strip">
            <div>
              <span>Ricette estratte</span>
              <strong>{parsedRecipesCount}</strong>
            </div>
            <div>
              <span>Sorgente</span>
              <strong>{analysis?.source ?? "-"}</strong>
            </div>
          </div>

          <div className="scroll-area">
            {analysis?.recipes.length ? (
              analysis.recipes.map((recipe, index) => (
                <div key={`${recipe.name}-${index}`} className="recipe-card">
                  <h3>{recipe.name}</h3>
                  <p>{recipe.description || "Nessuna descrizione disponibile."}</p>
                  <div className="recipe-meta">
                    <span>Tempo: {recipe.time_minutes ?? "n/d"}</span>
                    <span>Difficolta: {recipe.difficulty ?? "n/d"}</span>
                    <span>Ingredienti: {recipe.ingredients.length}</span>
                    <span>Passaggi: {recipe.procedure_steps.length}</span>
                  </div>
                </div>
              ))
            ) : (
              <p className="placeholder">
                Nessun dato analizzato. Avvia Agent 1 per vedere il contenuto.
              </p>
            )}
          </div>
        </article>

        <article className="panel panel-wide">
          <h2>3. Esito Agent 2</h2>
          <p>Risultato della persistenza nel database MariaDB.</p>

          <div className="metric-strip">
            <div>
              <span>Persistite</span>
              <strong>{persistence?.persisted ?? 0}</strong>
            </div>
            <div>
              <span>Fallite</span>
              <strong>{persistence?.failed ?? 0}</strong>
            </div>
            <div>
              <span>Sorgente</span>
              <strong>{persistence?.source ?? "-"}</strong>
            </div>
          </div>

          <div className="result-list">
            <h3>Ricette salvate</h3>
            {persistence?.recipe_names.length ? (
              <ul>
                {persistence.recipe_names.map((name) => (
                  <li key={name}>{name}</li>
                ))}
              </ul>
            ) : (
              <p className="placeholder">Nessuna persistenza eseguita.</p>
            )}

            <h3>Errori</h3>
            {persistence?.errors.length ? (
              <ul className="errors">
                {persistence.errors.map((message) => (
                  <li key={message}>{message}</li>
                ))}
              </ul>
            ) : (
              <p className="placeholder">Nessun errore rilevato.</p>
            )}
          </div>
        </article>
      </div>
    </section>
  );
}
