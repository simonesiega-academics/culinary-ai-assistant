import type { AnalysisBatch, FullIngestionResponse, PersistenceResult } from "@/lib/types";

const DEFAULT_BACKEND_URL = "http://localhost:8000";

function backendUrl(): string {
  return process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/$/, "") ?? DEFAULT_BACKEND_URL;
}

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { error?: string };
    if (body?.error) {
      return body.error;
    }
  } catch {
    // Ignore JSON parse errors and fallback to status text.
  }
  return `HTTP ${response.status} - ${response.statusText || "unknown error"}`;
}

export async function analyzePdf(file: File): Promise<AnalysisBatch> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${backendUrl()}/api/v1/agent-1/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as AnalysisBatch;
}

export async function persistAnalysis(batch: AnalysisBatch): Promise<PersistenceResult> {
  const response = await fetch(`${backendUrl()}/api/v1/agent-2/persist`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(batch),
  });

  if (!response.ok && response.status !== 207) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as PersistenceResult;
}

export async function runFullIngestion(file: File): Promise<FullIngestionResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${backendUrl()}/api/v1/agent-1/ingest`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok && response.status !== 207) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as FullIngestionResponse;
}
