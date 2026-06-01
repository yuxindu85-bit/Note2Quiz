import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Loader2, Target } from 'lucide-react';
import { ExamAttempt, listExamAttempts } from '../services/api';

export default function ExamHistory() {
  const [attempts, setAttempts] = useState<ExamAttempt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    listExamAttempts()
      .then((data) => setAttempts(data.attempts))
      .catch((err) => setError(err instanceof Error ? err.message : 'Could not load exam history.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="center-state">
        <Loader2 className="spin" />
        Loading exam history...
      </div>
    );
  }

  return (
    <section className="history-page">
      <div className="page-heading">
        <p className="eyebrow">Practice</p>
        <h1>Exam history</h1>
        <p>Track completed exam attempts and jump back into study packs.</p>
      </div>
      {error && <p className="error">{error}</p>}
      {!error && attempts.length === 0 && (
        <div className="empty-state">
          <Target size={34} />
          <h2>No exams yet</h2>
          <p>Open a study pack and start Exam Mode.</p>
        </div>
      )}
      <div className="history-list">
        {attempts.map((attempt) => (
          <Link className="history-card" to={`/packs/${attempt.pack_id}`} key={attempt.id}>
            <span>{new Date(attempt.created_at).toLocaleString()}</span>
            <h2>{attempt.title}</h2>
            <p>
              Score: {attempt.score}/{attempt.total_questions}
              {attempt.duration_seconds !== null && (
                <>
                  {' '}
                  <Clock size={14} /> {attempt.duration_seconds}s
                </>
              )}
            </p>
          </Link>
        ))}
      </div>
    </section>
  );
}
