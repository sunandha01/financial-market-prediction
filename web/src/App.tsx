import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { AuthProvider, useAuth } from "./auth";
import Layout from "./components/Layout";
import Admin from "./pages/Admin";
import Asset from "./pages/Asset";
import Home from "./pages/Home";
import { Learn, LearnTopic } from "./pages/Learn";
import Login from "./pages/Login";
import Status from "./pages/Status";

/** /admin is only reachable with a token in this tab; otherwise go to /login. */
function RequireAdmin({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  const location = useLocation();
  return token ? <>{children}</> : <Navigate to="/login" replace state={{ from: location.pathname }} />;
}

function NotFound() {
  return (
    <p className="text-slate-600">
      Page not found. <Link to="/" className="font-semibold text-indigo-600 underline">Back to the markets</Link>.
    </p>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="assets/:ticker" element={<Asset />} />
          <Route path="learn" element={<Learn />} />
          <Route path="learn/:slug" element={<LearnTopic />} />
          <Route path="status" element={<Status />} />
          <Route path="login" element={<Login />} />
          <Route path="admin" element={<RequireAdmin><Admin /></RequireAdmin>} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
