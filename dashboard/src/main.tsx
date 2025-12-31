import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles/tailwind.css';      // Tailwind base styles
import './styles/tokens.css';        // Design system tokens
import './styles/touch-targets.css'; // Touch accessibility (44px min targets)
import './index.css';                // Custom styles (overrides Tailwind)
import App from './App';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
