import React from 'react';
import ReactDOM from 'react-dom/client';
import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom';
import { CapturePage } from './pages/CapturePage';
import { ApplicationDetailPage } from './pages/ApplicationDetailPage';
import { ApplicationListPage } from './pages/ApplicationListPage';
import { ProfilePage } from './pages/ProfilePage';
import { ResumeVersionDetailPage } from './pages/ResumeVersionDetailPage';
import './styles.css';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/applications" replace />,
  },
  {
    path: '/applications',
    element: <ApplicationListPage />,
  },
  {
    path: '/capture',
    element: <CapturePage />,
  },
  {
    path: '/applications/:applicationId',
    element: <ApplicationDetailPage />,
  },
  {
    path: '/applications/:applicationId/resume-versions/:resumeVersionId',
    element: <ResumeVersionDetailPage />,
  },
  {
    path: '/profile',
    element: <ProfilePage />,
  },
]);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
