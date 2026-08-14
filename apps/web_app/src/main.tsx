import React from 'react';
import ReactDOM from 'react-dom/client';
import { AdminPanel } from './AdminPanel';
import { RoutedUserApp } from './RoutedUserApp';
import './admin.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {window.location.pathname.startsWith('/admin') ? <AdminPanel /> : <RoutedUserApp />}
  </React.StrictMode>,
);
