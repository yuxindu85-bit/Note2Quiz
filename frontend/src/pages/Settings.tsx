import { useEffect, useState } from 'react';
import { KeyRound, Loader2, ShieldCheck, Server } from 'lucide-react';
import { ApiHealth, getHealth } from '../services/api';
import { copy, UiLanguage } from '../i18n';

export default function Settings({ uiLanguage = 'english' }: { uiLanguage?: UiLanguage }) {
  const t = copy[uiLanguage];
  const [health, setHealth] = useState<ApiHealth | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((err) => setError(err instanceof Error ? err.message : 'Could not load API status.'));
  }, []);

  return (
    <section className="history-page">
      <div className="page-heading">
        <p className="eyebrow">{t.settingsPage}</p>
        <h1>AI provider and privacy</h1>
        <p>Note2Quiz is local-first. Files are stored in <code>backend/uploads</code>, and generated study packs are stored in SQLite.</p>
      </div>

      {error && <p className="error">{error}</p>}
      {!health && !error && (
        <div className="center-state">
          <Loader2 className="spin" />
          Loading settings...
        </div>
      )}

      {health && (
        <div className="dashboard-grid">
          <article className="metric-card">
            <Server size={22} />
            <h2>{health.demo_mode ? 'Mock mode active' : 'AI provider connected'}</h2>
            <p>Model: {health.ai_model}. Database: {health.database}.</p>
          </article>
          <article className="metric-card">
            <KeyRound size={22} />
            <h2>Environment variables</h2>
            <p><code>AI_API_KEY</code>, <code>AI_BASE_URL</code>, <code>AI_MODEL</code>, and <code>FRONTEND_ORIGIN</code>.</p>
          </article>
          <article className="metric-card">
            <ShieldCheck size={22} />
            <h2>No hardcoded keys</h2>
            <p>Users bring their own OpenAI-compatible provider key. The repository does not commit API keys.</p>
          </article>
          <article className="metric-card">
            <ShieldCheck size={22} />
            <h2>Local storage</h2>
            <p>Uploaded files and SQLite data stay on the machine running the backend unless you deploy it elsewhere.</p>
          </article>
        </div>
      )}
    </section>
  );
}
