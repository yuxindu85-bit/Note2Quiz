import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Download, Layers3, Loader2, RefreshCw } from 'lucide-react';
import { exportUrl, generatePack, getPack, StudyPack } from '../services/api';

const tabs = ['Summary', 'Quiz', 'Flashcards', 'Key Terms', 'Original Text'] as const;
type Tab = (typeof tabs)[number];

export default function Result() {
  const { packId } = useParams();
  const [pack, setPack] = useState<StudyPack | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('Summary');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
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
      const regenerated = await generatePack(pack.file_id, true);
      setPack(regenerated);
      setActiveTab('Summary');
      navigate(`/packs/${regenerated.id}`, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not regenerate this pack.');
    } finally {
      setRegenerating(false);
    }
  }

  const content = useMemo(() => {
    if (!pack) return null;
    if (activeTab === 'Summary') {
      return <p className="summary-text">{pack.summary}</p>;
    }
    if (activeTab === 'Quiz') {
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
              <p className="answer">Answer: {item.answer}</p>
            </article>
          ))}
        </div>
      );
    }
    if (activeTab === 'Flashcards') {
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
    if (activeTab === 'Key Terms') {
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
    return <pre className="original-text">{pack.original_text || 'No original text was stored.'}</pre>;
  }, [activeTab, pack]);

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
          <p className="eyebrow">Study pack</p>
          <h1>{pack.title}</h1>
          <p className="subtle-line">
            Generated {new Date(pack.created_at).toLocaleString()} with {pack.quiz.length} quiz
            questions and {pack.flashcards.length} flashcards.
          </p>
        </div>
        <div className="result-actions">
          <button className="secondary-button" type="button" disabled={regenerating} onClick={handleRegenerate}>
            {regenerating ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
            {regenerating ? 'Regenerating...' : 'Regenerate'}
          </button>
          <a className="secondary-button" href={exportUrl(pack.id)}>
            <Download size={18} />
            Export Markdown
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
            {tab}
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
