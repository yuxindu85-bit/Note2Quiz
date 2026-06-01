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
  translation_text: string;
  language: string;
  key_terms_count: number;
  quiz_order: string;
  created_at: string;
};

export type PackListItem = {
  id: string;
  file_id: string;
  title: string;
  summary: string;
  created_at: string;
};

export type ApiHealth = {
  status: string;
  database: string;
  demo_mode: boolean;
  ai_model: string;
};

export type ExamStart = {
  attempt_id: string;
  pack_id: string;
  title: string;
  questions: QuizItem[];
};

export type ExamReviewItem = {
  question_index: number;
  question: string;
  choices: string[];
  user_answer: string;
  correct_answer: string;
  is_correct: boolean;
  explanation: string;
};

export type ExamResult = {
  attempt_id: string;
  pack_id: string;
  score: number;
  total_questions: number;
  review: ExamReviewItem[];
};

export type ExamAttempt = {
  id: string;
  pack_id: string;
  title: string;
  score: number;
  total_questions: number;
  duration_seconds: number | null;
  status: string;
  created_at: string;
  completed_at: string | null;
};

export type WrongAnswer = {
  id: string;
  attempt_id: string;
  pack_id: string;
  pack_title: string;
  question: string;
  user_answer: string;
  correct_answer: string;
  explanation: string;
  created_at: string;
};

export type StudyPlanDay = {
  day: number;
  focus: string;
  tasks: string[];
  goal: string;
};

export type StudyPlan = {
  id: string;
  pack_id: string;
  duration_days: number;
  plan: StudyPlanDay[];
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

export async function getHealth(): Promise<ApiHealth> {
  return parseResponse(await fetch(`${API_BASE}/api/health`));
}

export async function generatePack(fileId: string, force = false): Promise<StudyPack> {
  const suffix = force ? '?force=true' : '';
  return parseResponse(await fetch(`${API_BASE}/api/generate/${fileId}${suffix}`, { method: 'POST' }));
}

export async function startExam(packId: string): Promise<ExamStart> {
  return parseResponse(await fetch(`${API_BASE}/api/packs/${packId}/exam/start`, { method: 'POST' }));
}

export async function submitExam(
  packId: string,
  attemptId: string,
  answers: { question_index: number; answer: string }[],
  durationSeconds: number | null
): Promise<ExamResult> {
  return parseResponse(
    await fetch(`${API_BASE}/api/packs/${packId}/exam/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        attempt_id: attemptId,
        answers,
        duration_seconds: durationSeconds
      })
    })
  );
}

export async function listExamAttempts(): Promise<{ attempts: ExamAttempt[] }> {
  return parseResponse(await fetch(`${API_BASE}/api/exam-attempts`));
}

export async function listWrongAnswers(): Promise<{ wrong_answers: WrongAnswer[] }> {
  return parseResponse(await fetch(`${API_BASE}/api/wrong-answers`));
}

export async function createStudyPlan(packId: string, durationDays: number): Promise<StudyPlan> {
  return parseResponse(
    await fetch(`${API_BASE}/api/packs/${packId}/study-plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ duration_days: durationDays })
    })
  );
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
