import React from 'react';
import ReactDOM from 'react-dom/client';

import { AdminPanel } from './AdminPanel';
import { RoutedUserApp } from './RoutedUserApp';
import './styles.css';
import './ux-polish.css';
import './admin.css';

const isAdminRoute = window.location.pathname.startsWith('/admin');
const rootComponent = isAdminRoute ? <AdminPanel /> : <RoutedUserApp />;

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    {rootComponent}
  </React.StrictMode>,
);
