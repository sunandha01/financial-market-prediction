import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Asset from "./pages/Asset";
import Home from "./pages/Home";
import { Learn, LearnTopic } from "./pages/Learn";
import Status from "./pages/Status";

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
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="assets/:ticker" element={<Asset />} />
          <Route path="learn" element={<Learn />} />
          <Route path="learn/:slug" element={<LearnTopic />} />
          <Route path="status" element={<Status />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
