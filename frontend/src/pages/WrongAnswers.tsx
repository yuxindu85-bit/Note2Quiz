import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Loader2, TriangleAlert } from 'lucide-react';
import { listWrongAnswers, WrongAnswer } from '../services/api';

export default function WrongAnswers() {
  const [wrongAnswers, setWrongAnswers] = useState<WrongAnswer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    listWrongAnswers()
      .then((data) => setWrongAnswers(data.wrong_answers))
      .catch((err) => setError(err instanceof Error ? err.message : 'Could not load wrong answers.'))
      .finally(() => setLoading(false));
  }, []);

  const grouped = useMemo(() => {
    return wrongAnswers.reduce<Record<string, WrongAnswer[]>>((groups, item) => {
      const key = item.pack_title;
      groups[key] = groups[key] ? [...groups[key], item] : [item];
      return groups;
    }, {});
  }, [wrongAnswers]);

  if (loading) {
    return (
      <div className="center-state">
        <Loader2 className="spin" />
        Loading wrong answers...
      </div>
    );
  }

  return (
    <section className="history-page">
      <div className="page-heading">
        <p className="eyebrow">Review</p>
        <h1>Wrong answers</h1>
        <p>Practice missed questions grouped by study pack.</p>
      </div>
      {error && <p className="error">{error}</p>}
      {!error && wrongAnswers.length === 0 && (
        <div className="empty-state">
          <TriangleAlert size={34} />
          <h2>No wrong answers saved</h2>
          <p>Complete an exam to build your review list.</p>
        </div>
      )}
      <div className="stack">
        {Object.entries(grouped).map(([title, items]) => (
          <section className="wrong-group" key={title}>
            <div className="group-heading">
              <h2>{title}</h2>
              <Link className="secondary-button" to={`/packs/${items[0].pack_id}/exam`}>
                Practice again
              </Link>
            </div>
            {items.map((item) => (
              <article className="item-card wrong" key={item.id}>
                <h3>{item.question}</h3>
                <p>Your answer: {item.user_answer}</p>
                <p>Correct answer: {item.correct_answer}</p>
                <p>{item.explanation}</p>
              </article>
            ))}
          </section>
        ))}
      </div>
    </section>
  );
}
