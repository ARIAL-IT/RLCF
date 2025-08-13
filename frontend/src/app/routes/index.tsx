import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Layout } from '../../components/layouts/Layout';
import { AuthGuard } from '../../components/shared/AuthGuard';
import { ErrorBoundary } from '../../components/shared/ErrorBoundary';
import { Dashboard } from '../../features/dashboard/Dashboard';
import { TaskEvaluation } from '../../features/evaluation/TaskEvaluation';
import { Analytics } from '../../features/analytics/Analytics';
import { Settings } from '../../features/admin/Settings';
import { AdminDashboard } from '../../features/admin/AdminDashboard';
import { UserProfile } from '../../features/auth/UserProfile';
import { Login } from '../../features/auth/Login';
import { TaskDetails } from '../../features/tasks/TaskDetails';
import { Leaderboard } from '../../features/analytics/Leaderboard';
import { UserRole } from '@/types';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: (
      <ErrorBoundary>
        <AuthGuard>
          <Layout />
        </AuthGuard>
      </ErrorBoundary>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <Dashboard />,
      },
      {
        path: 'evaluation',
        children: [
          {
            index: true,
            element: <TaskEvaluation />,
          },
          {
            path: 'task/:taskId',
            element: <TaskDetails />,
          },
        ],
      },
      {
        path: 'analytics',
        children: [
          {
            index: true,
            element: <Analytics />,
          },
          {
            path: 'leaderboard',
            element: <Leaderboard />,
          },
        ],
      },
      {
        path: 'admin',
        element: (
          <AuthGuard requiredRole={UserRole.ADMIN}>
            <AdminDashboard />
          </AuthGuard>
        ),
        children: [
          {
            path: 'settings',
            element: (
              <AuthGuard requiredRole={UserRole.ADMIN}>
                <Settings />
              </AuthGuard>
            ),
          },
        ],
      },
      {
        path: 'profile',
        element: <UserProfile />,
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
]);
