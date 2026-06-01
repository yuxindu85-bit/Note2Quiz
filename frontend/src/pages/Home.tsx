import { Link } from 'react-router-dom';
import { ArrowRight, BrainCircuit, FileText, Library, ShieldCheck } from 'lucide-react';
import UploadBox from '../components/UploadBox';
import { copy, UiLanguage } from '../i18n';

export default function Home({ uiLanguage }: { uiLanguage: UiLanguage }) {
  const t = copy[uiLanguage];
  return (
    <div className="home-page">
      <section className="hero-grid">
        <div className="intro">
          <p className="eyebrow">{t.eyebrow}</p>
          <h1>{t.headline}</h1>
          <p>{t.intro}</p>
          <div className="hero-actions">
            <Link className="primary-button" to="/upload">
              {t.start}
              <ArrowRight size={18} />
            </Link>
            <Link className="secondary-button" to="/history">
              {t.viewHistory}
            </Link>
          </div>
          <div className="feature-row">
            <span>PDF</span>
            <span>DOCX</span>
            <span>PPTX</span>
            <span>TXT</span>
          </div>
        </div>
        <UploadBox uiLanguage={uiLanguage} />
      </section>

      <section className="dashboard-grid">
        <article className="metric-card">
          <BrainCircuit size={22} />
          <h2>AI-ready</h2>
          <p>Use OpenAI-compatible providers or run the realistic mock generator for free.</p>
        </article>
        <article className="metric-card">
          <FileText size={22} />
          <h2>Structured outputs</h2>
          <p>Get a summary, 10 quiz questions, 20 flashcards, and key terms.</p>
        </article>
        <article className="metric-card">
          <Library size={22} />
          <h2>Saved history</h2>
          <p>SQLite stores generated packs so students can return to them later.</p>
        </article>
        <article className="metric-card">
          <ShieldCheck size={22} />
          <h2>Local-first</h2>
          <p>Uploads and generated packs stay on the developer's machine by default.</p>
        </article>
      </section>
    </div>
  );
}
