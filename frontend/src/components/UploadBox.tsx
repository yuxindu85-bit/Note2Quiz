import { FormEvent, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, FileText, FileUp, Loader2, Play, Sparkles } from 'lucide-react';
import { generatePack, QuizOrder, TranslationLanguage, uploadFile } from '../services/api';
import { copy, UiLanguage } from '../i18n';

const acceptedTypes = '.pdf,.docx,.pptx,.txt';
const translationLanguages: { label: string; value: TranslationLanguage }[] = [
  { label: 'No translation', value: 'none' },
  { label: 'English', value: 'english' },
  { label: '中文', value: 'chinese' },
  { label: 'Français', value: 'french' },
  { label: 'Русский', value: 'russian' },
  { label: 'Español', value: 'spanish' }
];

export default function UploadBox({ uiLanguage = 'english' }: { uiLanguage?: UiLanguage }) {
  const t = copy[uiLanguage];
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [keyTermsCount, setKeyTermsCount] = useState(10);
  const [quizOrder, setQuizOrder] = useState<QuizOrder>('ranked');
  const [translationLanguage, setTranslationLanguage] = useState<TranslationLanguage>('none');
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const generationOptions = {
    key_terms_count: keyTermsCount,
    quiz_order: quizOrder,
    language: 'auto' as const,
    translation_language: translationLanguage
  };

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setError(t.noFile);
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
          <h2>{t.createTitle}</h2>
          <p>{t.createSubtitle}</p>
        </div>
      </div>

      <button className="dropzone" type="button" onClick={() => inputRef.current?.click()}>
        {file ? <CheckCircle2 size={34} /> : <FileUp size={34} />}
        <strong>{file ? file.name : t.chooseFile}</strong>
        <span>{file ? `${Math.ceil(file.size / 1024)} KB selected` : t.fileTypes}</span>
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
        <span>{t.storedLocally}</span>
      </div>

      <div className="settings-panel" aria-label="Study generation settings">
        <div className="settings-heading">
          <strong>{t.settings}</strong>
          <span>{t.settingsHint}</span>
        </div>
        <label className="field">
          <span>{t.keyTerms}</span>
          <input
            max={30}
            min={3}
            type="number"
            value={keyTermsCount}
            onChange={(event) => setKeyTermsCount(Number(event.target.value))}
          />
        </label>
        <div className="field">
          <span>{t.quizOrder}</span>
          <div className="segmented full-width" role="group" aria-label="Quiz order">
            <button
              className={quizOrder === 'ranked' ? 'active' : ''}
              type="button"
              onClick={() => setQuizOrder('ranked')}
            >
              {t.ranked}
            </button>
            <button
              className={quizOrder === 'random' ? 'active' : ''}
              type="button"
              onClick={() => setQuizOrder('random')}
            >
              {t.random}
            </button>
          </div>
        </div>
        <label className="field">
          <span>{t.translateOriginal}</span>
          <select
            value={translationLanguage}
            onChange={(event) => setTranslationLanguage(event.target.value as TranslationLanguage)}
          >
            {translationLanguages.map((item) => (
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
          {loading ? t.generating : t.generate}
        </button>
        <button className="secondary-button" type="button" disabled={loading} onClick={runDemo}>
          <Play size={18} />
          {t.demo}
        </button>
      </div>
    </form>
  );
}
