import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Download, Layers3, Loader2, RefreshCw, Target } from 'lucide-react';
import {
  createStudyPlan,
  exportUrl,
  generatePack,
  getPack,
  QuizOrder,
  StudyLanguage,
  StudyPack,
  StudyPlan,
  TranslationLanguage
} from '../services/api';
import { copy, UiLanguage } from '../i18n';

const tabs = ['summary', 'quiz', 'flashcards', 'keyTerms', 'studyPlan', 'originalText'] as const;
type Tab = (typeof tabs)[number];
const languageLabels: Record<string, string> = {
  english: 'English',
  chinese: '中文',
  french: 'Français',
  russian: 'Русский',
  spanish: 'Español',
  none: 'No translation'
};

export default function Result({ uiLanguage = 'english' }: { uiLanguage?: UiLanguage }) {
  const t = copy[uiLanguage];
  const { packId } = useParams();
  const [pack, setPack] = useState<StudyPack | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('summary');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [planDays, setPlanDays] = useState(3);
  const [studyPlan, setStudyPlan] = useState<StudyPlan | null>(null);
  const [planLoading, setPlanLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!packId) return;
    getPack(packId)
      .then(setPack)
      .catch((err) => setError(err instanceof Error ? err.message : 'Could not load pack.'))
      .finally(() => setLoading(false));
  }, [packId]);

  async function handleRegenerate() {
    if (!pack) return;
    setRegenerating(true);
    setError('');
    try {
      const regenerated = await generatePack(pack.file_id, {
        force: true,
        key_terms_count: pack.key_terms_count,
        quiz_order: pack.quiz_order as QuizOrder,
        language: 'auto' as StudyLanguage,
        translation_language: pack.translation_language as TranslationLanguage
      });
      setPack(regenerated);
      setActiveTab('summary');
      navigate(`/packs/${regenerated.id}`, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not regenerate this pack.');
    } finally {
      setRegenerating(false);
    }
  }

  async function handleCreatePlan(days = planDays) {
    if (!pack) return;
    setPlanLoading(true);
    setError('');
    try {
      setPlanDays(days);
      setStudyPlan(await createStudyPlan(pack.id, days));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create study plan.');
    } finally {
      setPlanLoading(false);
    }
  }

  const content = useMemo(() => {
    if (!pack) return null;
    if (activeTab === 'summary') {
      return <p className="summary-text">{pack.summary}</p>;
    }
    if (activeTab === 'quiz') {
      if (pack.quiz.length === 0) {
        return <EmptyPanel message="No quiz questions were generated for this pack." />;
      }
      return (
        <div className="stack">
          {pack.quiz.map((item, index) => (
            <article className="item-card" key={`${item.question}-${index}`}>
              <h3>{index + 1}. {item.question}</h3>
              <ul>
                {item.choices.map((choice) => (
                  <li key={choice}>{choice}</li>
                ))}
              </ul>
              <p className="answer">{t.answer}: {item.answer}</p>
              {item.explanation && <p className="explanation">{t.explanation}: {item.explanation}</p>}
            </article>
          ))}
        </div>
      );
    }
    if (activeTab === 'flashcards') {
      if (pack.flashcards.length === 0) {
        return <EmptyPanel message="No flashcards were generated for this pack." />;
      }
      return (
        <div className="card-grid">
          {pack.flashcards.map((card, index) => (
            <article className="item-card" key={`${card.front}-${index}`}>
              <h3>{card.front}</h3>
              <p>{card.back}</p>
            </article>
          ))}
        </div>
      );
    }
    if (activeTab === 'keyTerms') {
      if (pack.key_terms.length === 0) {
        return <EmptyPanel message="No key terms were generated for this pack." />;
      }
      return (
        <div className="stack">
          {pack.key_terms.map((term, index) => (
            <article className="term-row" key={`${term.term}-${index}`}>
              <strong>{term.term}</strong>
              <span>{term.definition}</span>
            </article>
          ))}
        </div>
      );
    }
    if (activeTab === 'studyPlan') {
      return (
        <div className="stack">
          <div className="plan-toolbar">
            <div className="segmented">
              {[3, 5, 7].map((days) => (
                <button
                  className={planDays === days ? 'active' : ''}
                  key={days}
                  type="button"
                  onClick={() => void handleCreatePlan(days)}
                >
                  {days} days
                </button>
              ))}
            </div>
            <button className="secondary-button" type="button" disabled={planLoading} onClick={() => void handleCreatePlan()}>
              {planLoading ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
              Generate plan
            </button>
          </div>
          {!studyPlan && (
            <EmptyPanel message="Choose a 3-day, 5-day, or 7-day plan to generate a study schedule." />
          )}
          {studyPlan?.plan.map((day) => (
            <article className="item-card" key={day.day}>
              <h3>Day {day.day}: {day.focus}</h3>
              <ul>
                {day.tasks.map((task) => (
                  <li key={task}>{task}</li>
                ))}
              </ul>
              <p className="answer">Goal: {day.goal}</p>
            </article>
          ))}
        </div>
      );
    }
    return (
      <div className="source-stack">
        <section>
          <h2>{t.originalText}</h2>
          <pre className="original-text">{pack.original_text || 'No original text was stored.'}</pre>
        </section>
        {pack.translation_text && (
          <section className="translation-panel">
            <h2>{t.translation} · {languageLabels[pack.translation_language] ?? pack.translation_language}</h2>
            <pre className="original-text">{pack.translation_text}</pre>
          </section>
        )}
      </div>
    );
  }, [activeTab, pack, planDays, planLoading, studyPlan, t]);

  if (loading) {
    return (
      <div className="center-state">
        <Loader2 className="spin" />
        Loading study pack...
      </div>
    );
  }

  if (error || !pack) {
    return (
      <div className="center-state">
        <h2>Study pack not found</h2>
        <p>{error || 'This pack may have been deleted.'}</p>
        <Link to="/">Create a new pack</Link>
      </div>
    );
  }

  return (
    <section className="result-page">
      <div className="result-header">
        <div>
          <p className="eyebrow">{t.studyPack}</p>
          <h1>{pack.title}</h1>
          <p className="subtle-line">
            {new Date(pack.created_at).toLocaleString()} ·{' '}
            {t.generatedWith.replace('{quiz}', String(pack.quiz.length)).replace('{flashcards}', String(pack.flashcards.length))}
          </p>
          <div className="metadata-row">
            <span>{pack.key_terms.length} {t.keyTerms}</span>
            <span>{pack.quiz.length} {t.quiz}</span>
            <span>{pack.quiz_order === 'random' ? t.random : t.ranked}</span>
            <span>{t.analysis}: {languageLabels[pack.language] ?? pack.language}</span>
            <span>{t.translation}: {languageLabels[pack.translation_language] ?? pack.translation_language}</span>
          </div>
        </div>
        <div className="result-actions">
          <Link className="primary-button" to={`/packs/${pack.id}/exam`}>
            <Target size={18} />
            {t.startExam}
          </Link>
          <button className="secondary-button" type="button" disabled={regenerating} onClick={handleRegenerate}>
            {regenerating ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
            {regenerating ? `${t.regenerate}...` : t.regenerate}
          </button>
          <a className="secondary-button" href={exportUrl(pack.id)}>
            <Download size={18} />
            {t.exportMarkdown}
          </a>
        </div>
      </div>
      {error && <p className="error">{error}</p>}
      <div className="tabs">
        {tabs.map((tab) => (
          <button
            key={tab}
            className={activeTab === tab ? 'active' : ''}
            type="button"
            onClick={() => setActiveTab(tab)}
          >
            {t[tab]}
          </button>
        ))}
      </div>
      <div className="tab-panel">{content}</div>
    </section>
  );
}

function EmptyPanel({ message }: { message: string }) {
  return (
    <div className="empty-state compact">
      <Layers3 size={30} />
      <h2>Nothing here yet</h2>
      <p>{message}</p>
    </div>
  );
}
