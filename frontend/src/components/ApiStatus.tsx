import { useEffect, useState } from 'react';
import { CheckCircle2, CircleAlert, Loader2 } from 'lucide-react';
import { ApiHealth, getHealth } from '../services/api';

export default function ApiStatus() {
  const [health, setHealth] = useState<ApiHealth | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    getHealth()
      .then((data) => {
        setHealth(data);
        setFailed(false);
      })
      .catch(() => {
        setFailed(true);
      });
  }, []);

  if (failed) {
    return (
      <span className="status-pill danger" title="Start the FastAPI backend before generating packs.">
        <CircleAlert size={15} />
        API offline
      </span>
    );
  }

  if (!health) {
    return (
      <span className="status-pill">
        <Loader2 className="spin" size={15} />
        Checking API
      </span>
    );
  }

  return (
    <span className="status-pill" title={`Model: ${health.ai_model}`}>
      <CheckCircle2 size={15} />
      {health.demo_mode ? 'Demo mode' : 'AI connected'}
    </span>
  );
}
