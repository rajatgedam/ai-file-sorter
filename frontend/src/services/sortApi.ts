const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001';

export interface ProposedMove {
  source: string;
  destination: string;
  reason: string;
  approved: boolean;
}

export interface SortProposal {
  moves: ProposedMove[];
}

export interface ExecuteResult {
  moved: string[];
  skipped: string[];
  errors: string[];
  session_id: string | null;
}

export interface HealthResponse {
  status: string;
  ollama_connected: boolean;
  ollama_host: string;
}

export interface OllamaModel {
  name: string;
  size: number | null;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`);
  return handleResponse<HealthResponse>(res);
}

export async function listModels(): Promise<OllamaModel[]> {
  const res = await fetch(`${API_BASE_URL}/api/models`);
  const data = await handleResponse<{ models: OllamaModel[] }>(res);
  return data.models;
}

export async function analyzeFolder(
  folderPath: string,
  includeContent: boolean,
  recursive: boolean,
  model?: string,
): Promise<SortProposal> {
  const res = await fetch(`${API_BASE_URL}/api/sort/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      folder_path: folderPath,
      include_content: includeContent,
      recursive,
      model,
    }),
  });
  return handleResponse<SortProposal>(res);
}

export async function executeSort(
  folderPath: string,
  moves: ProposedMove[]
): Promise<ExecuteResult> {
  const res = await fetch(`${API_BASE_URL}/api/sort/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ folder_path: folderPath, moves }),
  });
  return handleResponse<ExecuteResult>(res);
}

export async function undoSort(sessionId: string): Promise<ExecuteResult> {
  const res = await fetch(`${API_BASE_URL}/api/sort/undo`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  return handleResponse<ExecuteResult>(res);
}
