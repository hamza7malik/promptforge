import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import { useEffect } from "react";
import { apiClient } from "./api";
import {
  Dashboard,
  AgentsPage,
  ChatPage,
  DocumentsPage,
  PromptsPage,
  AdminPage,
  LoginPage,
  PromptGeneratorPage,
} from "./pages";

function App() {
  const { isAuthenticated, isLoading, getAccessTokenSilently } = useAuth0();

  useEffect(() => {
    // Set token provider for API client
    apiClient.setTokenProvider(async () => {
      if (isAuthenticated) {
        return await getAccessTokenSilently();
      }
      return "";
    });
  }, [isAuthenticated, getAccessTokenSilently]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        {/* Protected routes */}
        <Route
          path="/"
          element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />}
        />
        <Route
          path="/agents"
          element={isAuthenticated ? <AgentsPage /> : <Navigate to="/login" />}
        />
        <Route
          path="/chat/:agentId"
          element={isAuthenticated ? <ChatPage /> : <Navigate to="/login" />}
        />
        <Route
          path="/documents/:agentId"
          element={
            isAuthenticated ? <DocumentsPage /> : <Navigate to="/login" />
          }
        />
        <Route
          path="/generate/:agentId"
          element={
            isAuthenticated ? <PromptGeneratorPage /> : <Navigate to="/login" />
          }
        />
        <Route
          path="/prompts"
          element={isAuthenticated ? <PromptsPage /> : <Navigate to="/login" />}
        />
        <Route
          path="/admin"
          element={isAuthenticated ? <AdminPage /> : <Navigate to="/login" />}
        />
      </Routes>
    </Router>
  );
}

export default App;
