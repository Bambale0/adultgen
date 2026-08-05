import React from 'react';
import ReactDOM from 'react-dom/client';

import { AdminPanel } from './AdminPanel';
import { App } from './App';
import './styles.css';

const rootComponent = window.location.pathname === '/admin' ? <AdminPanel /> : <App />;

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    {rootComponent}
  </React.StrictMode>,
);
