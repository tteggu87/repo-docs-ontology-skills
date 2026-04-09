import { createBrowserRouter, Navigate } from 'react-router-dom';
import App from './App';
import { DashboardPage } from './features/dashboard/DashboardPage';
import { AskPage } from './features/ask/AskPage';
import { PagesView } from './features/pages/PagesView';
import { GraphInspectPage } from './features/graph/GraphInspectPage';
import { DoctorPage } from './features/doctor/DoctorPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'ask', element: <AskPage /> },
      { path: 'pages', element: <PagesView /> },
      { path: 'graph', element: <GraphInspectPage /> },
      { path: 'doctor', element: <DoctorPage /> }
    ]
  }
]);
