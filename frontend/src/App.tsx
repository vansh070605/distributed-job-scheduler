import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./context/AuthContext";
import { Layout } from "./components/Layout";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { Queues } from "./pages/Queues";
import { Jobs } from "./pages/Jobs";
import { Workers } from "./pages/Workers";
import { DLQ } from "./pages/DLQ";

const queryClient = new QueryClient();

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Auth screen */}
            <Route path="/login" element={<Login />} />

            {/* Main Application Layout Protected Screens */}
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="queues" element={<Queues />} />
              <Route path="jobs" element={<Jobs />} />
              <Route path="workers" element={<Workers />} />
              <Route path="dlq" element={<DLQ />} />
            </Route>

            {/* Catch all fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
