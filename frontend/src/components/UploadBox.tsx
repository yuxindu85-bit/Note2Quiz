import { FormEvent, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, FileText, FileUp, Loader2, Play, Sparkles } from 'lucide-react';
import { generatePack, QuizOrder, StudyLanguage, uploadFile } from '../services/api';

const acceptedTypes = '.pdf,.docx,.pptx,.txt';
const languages: { label: string; value: StudyLanguage }[] = [
  { label: 'English', value: 'english' },
  { label: '中文', value: 'chinese' },
  { label: 'Français', value: 'french' },
  { label: 'Русский', value: 'russian' },
  { label: 'Español', value: 'spanish' }
];

export default function UploadBox() {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [keyTermsCount, setKeyTermsCount] = useState(10);
  const [quizOrder, setQuizOrder] = useState<QuizOrder>('ranked');
  const [language, setLanguage] = useState<StudyLanguage>('english');
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const generationOptions = {
    key_terms_count: keyTermsCount,
    quiz_order: quizOrder,
    language
  };

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
      const pack = await generatePack(upload.file_id, generationOptions);
      navigate(`/packs/${pack.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  }

  async function runDemo() {
    const demoText = [
      'Photosynthesis converts light energy into chemical energy in plants.',
      'Chlorophyll captures light inside chloroplasts and starts the light reactions.',
      'The light reactions produce ATP and NADPH for the Calvin cycle.',
      'The Calvin cycle fixes carbon dioxide into sugars.',
      'Ecosystems depend on photosynthesis because plants form the base of many food webs.'
    ].join(' ');
    const demoFile = new File([demoText], 'demo-photosynthesis-notes.txt', { type: 'text/plain' });

    setFile(demoFile);
    setLoading(true);
    setError('');
    try {
      const upload = await uploadFile(demoFile);
      const pack = await generatePack(upload.file_id, generationOptions);
      navigate(`/packs/${pack.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Demo generation failed.');
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

      <div className="settings-panel" aria-label="Study generation settings">
        <div className="settings-heading">
          <strong>Study settings</strong>
          <span>Control how much material you get before generating.</span>
        </div>
        <label className="field">
          <span>Key terms</span>
          <input
            max={30}
            min={3}
            type="number"
            value={keyTermsCount}
            onChange={(event) => setKeyTermsCount(Number(event.target.value))}
          />
        </label>
        <div className="field">
          <span>Quiz order</span>
          <div className="segmented full-width" role="group" aria-label="Quiz order">
            <button
              className={quizOrder === 'ranked' ? 'active' : ''}
              type="button"
              onClick={() => setQuizOrder('ranked')}
            >
              Most important first
            </button>
            <button
              className={quizOrder === 'random' ? 'active' : ''}
              type="button"
              onClick={() => setQuizOrder('random')}
            >
              Random
            </button>
          </div>
        </div>
        <label className="field">
          <span>Output language</span>
          <select value={language} onChange={(event) => setLanguage(event.target.value as StudyLanguage)}>
            {languages.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="button-row">
        <button className="primary-button" type="submit" disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <FileUp size={18} />}
          {loading ? 'Generating study pack...' : 'Generate study pack'}
        </button>
        <button className="secondary-button" type="button" disabled={loading} onClick={runDemo}>
          <Play size={18} />
          Try demo notes
        </button>
      </div>
    </form>
  );
}
