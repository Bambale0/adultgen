import React from 'react';
import ReactDOM from 'react-dom/client';
import { AdminPanel } from './AdminPanel';
import { RoutedUserApp } from './RoutedUserApp';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {window.location.pathname.startsWith('/admin') ? <AdminPanel /> : <RoutedUserApp />}
  </React.StrictMode>,
);
