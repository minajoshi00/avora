import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles/globals.css';
import App from './App';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/* Cinematic ambient backdrop — pure CSS motion, never remounts, never captures pointer */}
      <div className="avora-bg" aria-hidden="true">
        <div className="avora-bg__base" />
        <div className="avora-bg__aurora" />
        <span className="avora-bg__orb avora-bg__orb--blue" />
        <span className="avora-bg__orb avora-bg__orb--purple" />
        <span className="avora-bg__orb avora-bg__orb--cyan" />
        <div className="avora-bg__grid" />
        <div className="avora-bg__particles" aria-hidden="true">
          <span className="avora-bg__particle" />
          <span className="avora-bg__particle" />
          <span className="avora-bg__particle" />
          <span className="avora-bg__particle" />
        </div>
        <div className="avora-bg__noise" />
      </div>
    <App />
  </StrictMode>
);