import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles/globals.css';
import App from './App';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/* Cinematic ambient backdrop — static presentational layer, never remounts */}
    <div className="avora-bg" aria-hidden="true">
      <div className="avora-bg__base" />
      <span className="avora-bg__orb avora-bg__orb--blue" />
      <span className="avora-bg__orb avora-bg__orb--purple" />
      <span className="avora-bg__orb avora-bg__orb--cyan" />
      <div className="avora-bg__grid" />
      <div className="avora-bg__noise" />
    </div>
    <App />
  </StrictMode>
);