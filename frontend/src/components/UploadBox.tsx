import { FormEvent, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, FileText, FileUp, Loader2, Sparkles } from 'lucide-react';
import { generatePack, uploadFile } from '../services/api';

const acceptedTypes = '.pdf,.docx,.pptx,.txt';

export default function UploadBox() {
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
    <form className="upload-panel" onSubmit={handleSubmit}>
      <div className="upload-panel-header">
        <span className="icon-chip">
          <Sparkles size={18} />
        </span>
        <div>
          <h2>Create a study pack</h2>
          <p>Upload notes and generate study material in one step.</p>
        </div>
      </div>

      <button className="dropzone" type="button" onClick={() => inputRef.current?.click()}>
        {file ? <CheckCircle2 size={34} /> : <FileUp size={34} />}
        <strong>{file ? file.name : 'Choose a lecture file'}</strong>
        <span>{file ? `${Math.ceil(file.size / 1024)} KB selected` : 'PDF, DOCX, PPTX, or TXT'}</span>
      </button>

      <input
        ref={inputRef}
        type="file"
        accept={acceptedTypes}
        onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        hidden
      />

      <div className="file-support">
        <FileText size={16} />
        <span>Readable text is extracted and stored locally in SQLite.</span>
      </div>

      {error && <p className="error">{error}</p>}

      <button className="primary-button" type="submit" disabled={loading}>
        {loading ? <Loader2 className="spin" size={18} /> : <FileUp size={18} />}
        {loading ? 'Generating study pack...' : 'Generate study pack'}
      </button>
    </form>
  );
}
