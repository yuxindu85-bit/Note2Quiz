import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Loader2 } from 'lucide-react';
import { listPacks, PackListItem } from '../services/api';

export default function HistoryPage() {
  const [packs, setPacks] = useState<PackListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    listPacks()
      .then((data) => setPacks(data.packs))
      .catch((err) => setError(err instanceof Error ? err.message : 'Could not load history.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="center-state"><Loader2 className="spin" /> Loading history...</div>;
  }

  return (
    <section className="history-page">
      <div className="page-heading">
        <p className="eyebrow">Saved locally</p>
        <h1>Study pack history</h1>
      </div>

      {error && <p className="error">{error}</p>}

      {!error && packs.length === 0 && (
        <div className="empty-state">
          <Clock size={34} />
          <h2>No study packs yet</h2>
          <p>Upload a lecture file to generate your first saved pack.</p>
          <Link className="primary-button" to="/">Create one</Link>
        </div>
      )}

      <div className="history-list">
        {packs.map((pack) => (
          <Link className="history-card" to={`/packs/${pack.id}`} key={pack.id}>
            <span>{new Date(pack.created_at).toLocaleString()}</span>
            <h2>{pack.title}</h2>
            <p>{pack.summary}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
