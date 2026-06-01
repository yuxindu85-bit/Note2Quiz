import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom';
import { BookOpen, FileUp, History, Sparkles } from 'lucide-react';
import Home from './pages/Home';
import Result from './pages/Result';
import HistoryPage from './pages/History';
import Upload from './pages/Upload';
import './styles.css';

function App() {
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
              Home
            </NavLink>
            <NavLink to="/upload">
              <FileUp size={18} />
              Upload
            </NavLink>
            <NavLink to="/history">
              <History size={18} />
              History
            </NavLink>
          </nav>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/packs/:packId" element={<Result />} />
            <Route path="/history" element={<HistoryPage />} />
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
