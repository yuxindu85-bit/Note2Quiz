import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom';
import { BookOpen, FileUp, History, Sparkles, Target, TriangleAlert } from 'lucide-react';
import Home from './pages/Home';
import Result from './pages/Result';
import HistoryPage from './pages/History';
import Upload from './pages/Upload';
import ApiStatus from './components/ApiStatus';
import Exam from './pages/Exam';
import ExamHistory from './pages/ExamHistory';
import WrongAnswers from './pages/WrongAnswers';
import { copy, UiLanguage, uiLanguages } from './i18n';
import './styles.css';

function App() {
  const [uiLanguage, setUiLanguage] = useState<UiLanguage>(() => {
    const saved = localStorage.getItem('note2quiz-ui-language');
    return uiLanguages.some((item) => item.value === saved) ? (saved as UiLanguage) : 'english';
  });
  const t = copy[uiLanguage];

  useEffect(() => {
    localStorage.setItem('note2quiz-ui-language', uiLanguage);
  }, [uiLanguage]);

  return (
    <BrowserRouter>
      <div className="app-shell">
        <header className="topbar">
          <NavLink to="/" className="brand">
            <Sparkles size={22} />
            <span>Note2Quiz</span>
          </NavLink>
          <nav>
            <NavLink to="/">
              <BookOpen size={18} />
              {t.home}
            </NavLink>
            <NavLink to="/upload">
              <FileUp size={18} />
              {t.upload}
            </NavLink>
            <NavLink to="/history">
              <History size={18} />
              {t.history}
            </NavLink>
            <NavLink to="/exam-history">
              <Target size={18} />
              {t.examHistory}
            </NavLink>
            <NavLink to="/wrong-answers">
              <TriangleAlert size={18} />
              {t.wrongAnswers}
            </NavLink>
          </nav>
          <label className="language-picker">
            <span>{t.language}</span>
            <select value={uiLanguage} onChange={(event) => setUiLanguage(event.target.value as UiLanguage)}>
              {uiLanguages.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <ApiStatus />
        </header>
        <main>
          <Routes>
            <Route path="/" element={<Home uiLanguage={uiLanguage} />} />
            <Route path="/upload" element={<Upload uiLanguage={uiLanguage} />} />
            <Route path="/packs/:packId" element={<Result />} />
            <Route path="/packs/:packId/exam" element={<Exam />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/exam-history" element={<ExamHistory />} />
            <Route path="/wrong-answers" element={<WrongAnswers />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
