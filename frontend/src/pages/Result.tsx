import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { BookmarkPlus, Download, Layers3, Loader2, RefreshCw, Star, Target } from 'lucide-react';
import {
  addFavorite,
  createStudyPlan,
  deleteFavorite,
  exportAnkiUrl,
  exportJsonUrl,
  exportUrl,
  FavoriteItem,
  generatePack,
  getPack,
  listFavorites,
  QuizOrder,
  StudyLanguage,
  StudyPack,
  StudyPlan,
  TranslationLanguage,
  reviewFlashcard
} from '../services/api';
import { copy, UiLanguage } from '../i18n';

const tabs = ['summary', 'quiz', 'flashcards', 'keyTerms', 'studyPlan', 'favorites', 'originalText', 'export'] as const;
type Tab = (typeof tabs)[number];
const languageLabels: Record<string, string> = {
  english: 'English',
  chinese: '中文',
  french: 'Français',
  russian: 'Русский',
  spanish: 'Español',
  none: 'No translation'
};
type FlashcardStatus = 'known' | 'review';

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
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);
  const [currentCard, setCurrentCard] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [flashcardProgress, setFlashcardProgress] = useState<Record<number, FlashcardStatus>>({});
  const [reviewOnly, setReviewOnly] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!packId) return;
    getPack(packId)
      .then(setPack)
      .catch((err) => setError(err instanceof Error ? err.message : 'Could not load pack.'))
      .finally(() => setLoading(false));
    listFavorites(packId)
      .then((data) => setFavorites(data.favorites))
      .catch(() => setFavorites([]));
    try {
      const saved = window.localStorage.getItem(`note2quiz-flashcards-${packId}`);
      setFlashcardProgress(saved ? JSON.parse(saved) : {});
    } catch {
      setFlashcardProgress({});
    }
    setCurrentCard(0);
    setFlipped(false);
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

  async function handleFavorite(item: { item_type: string; item_index: number; title: string; content: string; source?: string }) {
    if (!pack) return;
    try {
      const data = await addFavorite(pack.id, item);
      setFavorites(data.favorites);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save favorite.');
    }
  }

  async function handleDeleteFavorite(favoriteId: string) {
    await deleteFavorite(favoriteId);
    setFavorites((items) => items.filter((item) => item.id !== favoriteId));
  }

  async function handleFlashcardReview(status: 'known' | 'review') {
    if (!pack) return;
    const targetIndex = visibleCardIndexes[Math.min(currentCard, Math.max(visibleCardIndexes.length - 1, 0))] ?? 0;
    await reviewFlashcard(pack.id, targetIndex, status);
    const nextProgress = { ...flashcardProgress, [targetIndex]: status };
    setFlashcardProgress(nextProgress);
    window.localStorage.setItem(`note2quiz-flashcards-${pack.id}`, JSON.stringify(nextProgress));
    setFlipped(false);
    setCurrentCard((index) => Math.min(Math.max(visibleCardIndexes.length - 1, 0), index + 1));
  }

  const visibleCardIndexes = useMemo(() => {
    if (!pack) return [];
    const indexes = pack.flashcards.map((_, index) => index);
    return reviewOnly ? indexes.filter((index) => flashcardProgress[index] === 'review') : indexes;
  }, [flashcardProgress, pack, reviewOnly]);

  const flashcardMetrics = useMemo(() => {
    const total = pack?.flashcards.length ?? 0;
    const statuses = Object.values(flashcardProgress);
    const reviewed = Math.min(statuses.length, total);
    const known = statuses.filter((status) => status === 'known').length;
    const review = statuses.filter((status) => status === 'review').length;
    return {
      total,
      reviewed,
      known,
      review,
      unseen: Math.max(total - reviewed, 0),
      percentage: total ? Math.round((reviewed / total) * 100) : 0
    };
  }, [flashcardProgress, pack]);

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
              <div className="metadata-row compact">
                <span>Topic: {item.topic ?? 'General'}</span>
                <span>Difficulty: {item.difficulty ?? 'medium'}</span>
              </div>
              {item.explanation && <p className="explanation">{t.explanation}: {item.explanation}</p>}
              <button
                className="secondary-button inline-action"
                type="button"
                onClick={() => void handleFavorite({
                  item_type: 'quiz',
                  item_index: index,
                  title: item.question,
                  content: `${t.answer}: ${item.answer}\n${t.explanation}: ${item.explanation ?? ''}`,
                  source: item.topic ?? 'Quiz'
                })}
              >
                <BookmarkPlus size={16} />
                Favorite
              </button>
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
        <div className="stack">
          <div className="practice-panel">
            <div>
              <p className="eyebrow">Flashcard practice</p>
              <h2>{flashcardMetrics.reviewed} / {flashcardMetrics.total} reviewed</h2>
              <p className="subtle-line">
                Known: {flashcardMetrics.known} · Need review: {flashcardMetrics.review} · Unseen: {flashcardMetrics.unseen}
              </p>
              <div className="progress-track labeled" aria-label="Flashcard progress">
                <div style={{ width: `${flashcardMetrics.percentage}%` }} />
              </div>
              <div className="progress-labels">
                <span>{flashcardMetrics.percentage}% complete</span>
                <span>{reviewOnly ? 'Need review queue' : 'All cards queue'}</span>
              </div>
            </div>
            {visibleCardIndexes.length > 0 ? (
              <article className="flashcard-practice" onClick={() => setFlipped((value) => !value)}>
                <span>{pack.flashcards[visibleCardIndexes[currentCard] ?? 0]?.topic ?? 'General'}</span>
                <h3>
                  {flipped
                    ? pack.flashcards[visibleCardIndexes[currentCard] ?? 0]?.back
                    : pack.flashcards[visibleCardIndexes[currentCard] ?? 0]?.front}
                </h3>
                <p>
                  Card {Math.min(currentCard + 1, visibleCardIndexes.length)} of {visibleCardIndexes.length} ·{' '}
                  {flipped ? 'Back' : 'Front'} · click to flip
                </p>
              </article>
            ) : (
              <div className="empty-state compact">
                <Layers3 size={28} />
                <h2>No review cards</h2>
                <p>Mark some cards as Need review, then switch back to this queue.</p>
              </div>
            )}
            <div className="button-row">
              <button
                className="secondary-button"
                type="button"
                onClick={() => {
                  setReviewOnly((value) => !value);
                  setCurrentCard(0);
                  setFlipped(false);
                }}
              >
                {reviewOnly ? 'Practice all cards' : 'Practice Need review'}
              </button>
              <button
                className="secondary-button"
                type="button"
                disabled={visibleCardIndexes.length === 0}
                onClick={() => void handleFlashcardReview('review')}
              >
                Need review
              </button>
              <button
                className="primary-button"
                type="button"
                disabled={visibleCardIndexes.length === 0}
                onClick={() => void handleFlashcardReview('known')}
              >
                I know this
              </button>
            </div>
          </div>
          <div className="card-grid">
            {pack.flashcards.map((card, index) => (
              <article className="item-card" key={`${card.front}-${index}`}>
                <h3>{card.front}</h3>
                <p>{card.back}</p>
                <div className="metadata-row compact">
                  <span>{card.topic ?? 'General'}</span>
                  <span>Status: {flashcardProgress[index] ?? 'unseen'}</span>
                </div>
                <button
                  className="secondary-button inline-action"
                  type="button"
                  onClick={() => void handleFavorite({
                    item_type: 'flashcard',
                    item_index: index,
                    title: card.front,
                    content: card.back,
                    source: card.topic ?? 'Flashcard'
                  })}
                >
                  <BookmarkPlus size={16} />
                  Favorite
                </button>
              </article>
            ))}
          </div>
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
              <small>Importance: {term.importance ?? 'medium'}</small>
              <button
                className="secondary-button inline-action"
                type="button"
                onClick={() => void handleFavorite({
                  item_type: 'key_term',
                  item_index: index,
                  title: term.term,
                  content: term.definition,
                  source: term.importance ?? 'Key term'
                })}
              >
                <BookmarkPlus size={16} />
                Favorite
              </button>
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
              {[1, 3, 5, 7].map((days) => (
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
          {!studyPlan && <EmptyPanel message="Choose a 1-day, 3-day, 5-day, or 7-day plan to generate a study schedule." />}
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
    if (activeTab === 'favorites') {
      if (favorites.length === 0) {
        return <EmptyPanel message="Favorite quiz explanations, flashcards, and key terms to build a focused review box." />;
      }
      return (
        <div className="stack">
          {favorites.map((item) => (
            <article className="item-card" key={item.id}>
              <div className="group-heading">
                <div>
                  <span className="mini-label">{item.item_type}</span>
                  <h3>{item.title}</h3>
                </div>
                <button className="secondary-button" type="button" onClick={() => void handleDeleteFavorite(item.id)}>
                  Remove
                </button>
              </div>
              <p>{item.content}</p>
              {item.source && <p className="answer">Source: {item.source}</p>}
            </article>
          ))}
        </div>
      );
    }
    if (activeTab === 'export') {
      return (
        <div className="card-grid">
          <a className="item-card export-card" href={exportUrl(pack.id)}>
            <Download size={20} />
            <h3>Markdown</h3>
            <p>Summary, quiz answers, explanations, flashcards, key terms, and generated plans.</p>
          </a>
          <a className="item-card export-card" href={exportJsonUrl(pack.id)}>
            <Download size={20} />
            <h3>JSON</h3>
            <p>Raw structured study pack data for developers and integrations.</p>
          </a>
          <a className="item-card export-card" href={exportAnkiUrl(pack.id)}>
            <Download size={20} />
            <h3>Anki CSV</h3>
            <p>Flashcards exported as Front, Back, and Topic columns.</p>
          </a>
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
  }, [
    activeTab,
    pack,
    planDays,
    planLoading,
    studyPlan,
    t,
    favorites,
    currentCard,
    flipped,
    flashcardProgress,
    flashcardMetrics,
    reviewOnly,
    visibleCardIndexes
  ]);

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
            <span><Star size={14} /> {favorites.length} Favorites</span>
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
