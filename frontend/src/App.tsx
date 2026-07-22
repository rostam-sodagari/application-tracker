import { Route, Routes } from "react-router-dom";
import { NavBar } from "./components/NavBar";
import { RequireAuth } from "./components/RequireAuth";
import { VerificationBanner } from "./components/VerificationBanner";
import { ApplicationsPage } from "./pages/ApplicationsPage";
import { CvsPage } from "./pages/CvsPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { SettingsPage } from "./pages/SettingsPage";
import { VerifyEmailPage } from "./pages/VerifyEmailPage";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route
        path="/*"
        element={
          <RequireAuth>
            <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
              <NavBar />
              <VerificationBanner />
              <main className="mx-auto max-w-5xl px-4 py-6">
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/applications" element={<ApplicationsPage />} />
                  <Route path="/cvs" element={<CvsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Routes>
              </main>
            </div>
          </RequireAuth>
        }
      />
    </Routes>
  );
}

export default App;
