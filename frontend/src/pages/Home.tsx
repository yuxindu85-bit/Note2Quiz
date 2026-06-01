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
          <h2>{t.aiReady}</h2>
          <p>{t.aiReadyText}</p>
        </article>
        <article className="metric-card">
          <FileText size={22} />
          <h2>{t.structuredOutputs}</h2>
          <p>{t.structuredOutputsText}</p>
        </article>
        <article className="metric-card">
          <Library size={22} />
          <h2>{t.savedHistory}</h2>
          <p>{t.savedHistoryText}</p>
        </article>
        <article className="metric-card">
          <ShieldCheck size={22} />
          <h2>{t.localFirst}</h2>
          <p>{t.localFirstText}</p>
        </article>
      </section>
    </div>
  );
}
