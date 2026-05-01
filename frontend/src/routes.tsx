import { Suspense, lazy } from "react";
import { Routes, Route } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { Skeleton } from "./components/common/Skeleton";

// Lazy-loaded routes for code-splitting
const HomePage = lazy(() => import("./pages/HomePage"));
const PredictPage = lazy(() => import("./pages/PredictPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const AboutPage = lazy(() => import("./pages/AboutPage"));
const AudioPage = lazy(() => import("./pages/AudioPage"));
const NotFoundPage = lazy(() => import("./pages/NotFoundPage"));

// Global fallback for lazy routes
const PageFallback = () => (
  <div className="flex-1 flex flex-col items-center justify-center min-h-[50vh] p-8 space-y-4">
    <Skeleton className="h-8 w-64" />
    <Skeleton className="h-4 w-96" />
    <Skeleton className="h-4 w-80" />
  </div>
);

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route
          path="/"
          element={
            <Suspense fallback={<PageFallback />}>
              <HomePage />
            </Suspense>
          }
        />
        <Route
          path="/predict"
          element={
            <Suspense fallback={<PageFallback />}>
              <PredictPage />
            </Suspense>
          }
        />
        <Route
          path="/dashboard"
          element={
            <Suspense fallback={<PageFallback />}>
              <DashboardPage />
            </Suspense>
          }
        />
        <Route
          path="/about"
          element={
            <Suspense fallback={<PageFallback />}>
              <AboutPage />
            </Suspense>
          }
        />
        <Route
          path="/audio"
          element={
            <Suspense fallback={<PageFallback />}>
              <AudioPage />
            </Suspense>
          }
        />
        {/* 404 Route */}
        <Route
          path="*"
          element={
            <Suspense fallback={<PageFallback />}>
              <NotFoundPage />
            </Suspense>
          }
        />
      </Route>
    </Routes>
  );
}
