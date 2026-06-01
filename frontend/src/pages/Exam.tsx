import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, Clock, Loader2 } from 'lucide-react';
import { ExamResult, ExamStart, startExam, submitExam } from '../services/api';

const timerOptions = [
  { label: 'No timer', seconds: null },
  { label: '5 min', seconds: 300 },
  { label: '10 min', seconds: 600 },
  { label: '20 min', seconds: 1200 }
];

export default function Exam() {
  const { packId } = useParams();
  const [exam, setExam] = useState<ExamStart | null>(null);
  const [result, setResult] = useState<ExamResult | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [timerSeconds, setTimerSeconds] = useState<number | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function beginExam() {
    if (!packId) return;
    setLoading(true);
    setError('');
    try {
      const started = await startExam(packId);
      setExam(started);
      setRemainingSeconds(timerSeconds);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start exam.');
    } finally {
      setLoading(false);
    }
  }

  async function finishExam() {
    if (!packId || !exam || result) return;
    setLoading(true);
    setError('');
    const duration =
      timerSeconds === null || remainingSeconds === null ? null : Math.max(0, timerSeconds - remainingSeconds);
    try {
      const submitted = await submitExam(
        packId,
        exam.attempt_id,
        Object.entries(answers).map(([questionIndex, answer]) => ({
          question_index: Number(questionIndex),
          answer
        })),
        duration
      );
      setResult(submitted);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not submit exam.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!exam || remainingSeconds === null || result) return undefined;
    if (remainingSeconds <= 0) {
      void finishExam();
      return undefined;
    }
    const interval = window.setInterval(() => setRemainingSeconds((value) => (value === null ? null : value - 1)), 1000);
    return () => window.clearInterval(interval);
  }, [exam, remainingSeconds, result]);

  const question = exam?.questions[currentIndex];
  const answeredCount = Object.keys(answers).length;
  const progress = exam ? Math.round(((currentIndex + 1) / exam.questions.length) * 100) : 0;
  const formattedTime = useMemo(() => {
    if (remainingSeconds === null) return null;
    const minutes = Math.floor(remainingSeconds / 60);
    const seconds = String(remainingSeconds % 60).padStart(2, '0');
    return `${minutes}:${seconds}`;
  }, [remainingSeconds]);

  if (!exam && !result) {
    return (
      <section className="exam-page">
        <Link className="back-link" to={packId ? `/packs/${packId}` : '/history'}>
          <ArrowLeft size={16} />
          Back to study pack
        </Link>
        <div className="page-heading">
          <p className="eyebrow">Exam mode</p>
          <h1>Practice one question at a time</h1>
          <p>Choose a timer, start the exam, then submit to save your score and wrong answers.</p>
        </div>
        <div className="exam-start-card">
          <div className="segmented">
            {timerOptions.map((option) => (
              <button
                className={timerSeconds === option.seconds ? 'active' : ''}
                key={option.label}
                type="button"
                onClick={() => setTimerSeconds(option.seconds)}
              >
                {option.label}
              </button>
            ))}
          </div>
          {error && <p className="error">{error}</p>}
          <button className="primary-button" type="button" disabled={loading} onClick={beginExam}>
            {loading ? <Loader2 className="spin" size={18} /> : <CheckCircle2 size={18} />}
            Start exam
          </button>
        </div>
      </section>
    );
  }

  if (result) {
    return (
      <section className="exam-page">
        <div className="result-header">
          <div>
            <p className="eyebrow">Exam review</p>
            <h1>
              {result.score}/{result.total_questions} correct
            </h1>
          </div>
          <Link className="secondary-button" to="/wrong-answers">
            Review wrong answers
          </Link>
        </div>
        <div className="stack">
          {result.review.map((item) => (
            <article className={`item-card ${item.is_correct ? 'correct' : 'wrong'}`} key={item.question_index}>
              <h3>{item.question}</h3>
              <p>Your answer: {item.user_answer || 'No answer'}</p>
              <p>Correct answer: {item.correct_answer}</p>
              <p>{item.explanation}</p>
            </article>
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="exam-page">
      <div className="exam-toolbar">
        <span>Question {currentIndex + 1} of {exam!.questions.length}</span>
        {formattedTime && (
          <span className="status-pill">
            <Clock size={15} />
            {formattedTime}
          </span>
        )}
      </div>
      <div className="progress-track">
        <div style={{ width: `${progress}%` }} />
      </div>
      <article className="exam-question">
        <h1>{question?.question}</h1>
        <div className="choice-list">
          {question?.choices.map((choice) => (
            <button
              className={answers[currentIndex] === choice ? 'selected' : ''}
              key={choice}
              type="button"
              onClick={() => setAnswers((current) => ({ ...current, [currentIndex]: choice }))}
            >
              {choice}
            </button>
          ))}
        </div>
      </article>
      <div className="exam-actions">
        <button
          className="secondary-button"
          type="button"
          disabled={currentIndex === 0}
          onClick={() => setCurrentIndex((index) => Math.max(0, index - 1))}
        >
          Previous
        </button>
        {currentIndex < exam!.questions.length - 1 ? (
          <button
            className="primary-button"
            type="button"
            onClick={() => setCurrentIndex((index) => Math.min(exam!.questions.length - 1, index + 1))}
          >
            Next
          </button>
        ) : (
          <button className="primary-button" type="button" disabled={loading} onClick={finishExam}>
            Submit {answeredCount}/{exam!.questions.length}
          </button>
        )}
      </div>
      {error && <p className="error">{error}</p>}
    </section>
  );
}
