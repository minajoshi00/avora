import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles/globals.css';
import App from './App';
import { VisualModeProvider } from './components/ui/VisualModeProvider';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <VisualModeProvider>
      <App />
    </VisualModeProvider>
  </StrictMode>
);
