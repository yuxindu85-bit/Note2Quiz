const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

export type QuizItem = {
  question: string;
  choices: string[];
  answer: string;
};

export type Flashcard = {
  front: string;
  back: string;
};

export type KeyTerm = {
  term: string;
  definition: string;
};

export type StudyPack = {
  id: string;
  file_id: string;
  title: string;
  summary: string;
  quiz: QuizItem[];
  flashcards: Flashcard[];
  key_terms: KeyTerm[];
  original_text: string;
  created_at: string;
};

export type PackListItem = {
  id: string;
  file_id: string;
  title: string;
  summary: string;
  created_at: string;
};

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: 'Request failed.' }));
    throw new Error(data.detail ?? 'Request failed.');
  }
  return response.json();
}

export async function uploadFile(file: File): Promise<{ file_id: string; filename: string }> {
  const formData = new FormData();
  formData.append('file', file);
  return parseResponse(await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: formData }));
}

export async function generatePack(fileId: string): Promise<StudyPack> {
  return parseResponse(await fetch(`${API_BASE}/api/generate/${fileId}`, { method: 'POST' }));
}

export async function getPack(packId: string): Promise<StudyPack> {
  return parseResponse(await fetch(`${API_BASE}/api/packs/${packId}`));
}

export async function listPacks(): Promise<{ packs: PackListItem[] }> {
  return parseResponse(await fetch(`${API_BASE}/api/packs`));
}

export function exportUrl(packId: string): string {
  return `${API_BASE}/api/export/${packId}`;
}
