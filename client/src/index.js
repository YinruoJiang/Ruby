import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App';

// Base URL for API requests
const API_BASE_URL = process.env.NODE_ENV === 'development' ? 'http://localhost:3001' : '';

const container = document.getElementById('root');
const root = createRoot(container);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
); 