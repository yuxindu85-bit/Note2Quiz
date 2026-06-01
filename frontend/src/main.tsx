import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';
import { BookOpen, History, Sparkles } from 'lucide-react';
import Home from './pages/Home';
import Result from './pages/Result';
import HistoryPage from './pages/History';
import './styles.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <header className="topbar">
          <Link to="/" className="brand">
            <Sparkles size={22} />
            <span>Note2Quiz</span>
          </Link>
          <nav>
            <Link to="/">
              <BookOpen size={18} />
              Create
            </Link>
            <Link to="/history">
              <History size={18} />
              History
            </Link>
          </nav>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
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
