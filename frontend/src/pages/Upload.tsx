import UploadBox from '../components/UploadBox';
import { copy, UiLanguage } from '../i18n';

export default function Upload({ uiLanguage }: { uiLanguage: UiLanguage }) {
  const t = copy[uiLanguage];
  return (
    <section className="upload-page">
      <div className="page-heading">
        <p className="eyebrow">{t.settings}</p>
        <h1>{t.createTitle}</h1>
        <p>{t.createSubtitle}</p>
      </div>
      <UploadBox uiLanguage={uiLanguage} />
    </section>
  );
}
