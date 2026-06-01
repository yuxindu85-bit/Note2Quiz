import { FormEvent, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileUp, Loader2 } from 'lucide-react';
import { generatePack, uploadFile } from '../services/api';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setError('Choose a PDF, DOCX, PPTX, or TXT file first.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const upload = await uploadFile(file);
      const pack = await generatePack(upload.file_id);
      navigate(`/packs/${pack.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="home-grid">
      <div className="intro">
        <p className="eyebrow">Open-source study assistant</p>
        <h1>Turn lecture files into study packs.</h1>
        <p>
          Upload class notes, lecture slides, or handouts. Note2Quiz extracts the text and creates a
          summary, quiz, flashcards, key terms, and a Markdown export.
        </p>
        <div className="feature-row">
          <span>PDF</span>
          <span>DOCX</span>
          <span>PPTX</span>
          <span>TXT</span>
        </div>
      </div>

      <form className="upload-panel" onSubmit={handleSubmit}>
        <button className="dropzone" type="button" onClick={() => inputRef.current?.click()}>
          <FileUp size={34} />
          <strong>{file ? file.name : 'Choose a lecture file'}</strong>
          <span>{file ? `${Math.ceil(file.size / 1024)} KB selected` : 'PDF, DOCX, PPTX, or TXT'}</span>
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.pptx,.txt"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          hidden
        />
        {error && <p className="error">{error}</p>}
        <button className="primary-button" type="submit" disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <FileUp size={18} />}
          {loading ? 'Generating study pack...' : 'Generate study pack'}
        </button>
      </form>
    </section>
  );
}
