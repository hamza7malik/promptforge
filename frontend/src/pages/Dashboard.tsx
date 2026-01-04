import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import { useAgentStore, useConversationStore } from "@/stores";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components";
import { Bot, FileText, MessageSquare, Plus, Settings } from "lucide-react";

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth0();
  const { agents, fetchAgents } = useAgentStore();
  const { conversations, fetchConversations } = useConversationStore();

  useEffect(() => {
    fetchAgents();
    fetchConversations();
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Bot className="h-6 w-6 text-primary" />
            <div>
              <h1 className="text-2xl font-bold">PromptForge</h1>
              <p className="text-xs text-gray-600">
                AI Agent Workspace for Prompt Engineers
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">{user?.email}</span>
            <Button variant="outline" onClick={() => logout()}>
              Sign Out
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8">
          {/* Welcome Section */}
          <div>
            <h2 className="text-3xl font-bold mb-2">Welcome back!</h2>
            <p className="text-muted-foreground">
              Manage your AI agents, upload documents, and get expert
              assistance.
            </p>
          </div>

          {/* Stats Cards */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Your Agents
                </CardTitle>
                <Bot className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{agents.length}</div>
                <p className="text-xs text-muted-foreground">
                  Active AI agents
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  Conversations
                </CardTitle>
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{conversations.length}</div>
                <p className="text-xs text-muted-foreground">
                  Total conversations
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Documents</CardTitle>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {agents.reduce(
                    (sum, agent) => sum + (agent.document_count || 0),
                    0
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  Training documents
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <div>
            <h3 className="text-xl font-semibold mb-4">Quick Actions</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <Card
                className="cursor-pointer hover:border-primary transition-colors"
                onClick={() => navigate("/agents")}
              >
                <CardHeader>
                  <Bot className="h-8 w-8 mb-2 text-primary" />
                  <CardTitle>Create New Agent</CardTitle>
                  <CardDescription>
                    Build a specialized AI agent trained on your documents
                  </CardDescription>
                </CardHeader>
              </Card>

              <Card
                className="cursor-pointer hover:border-primary transition-colors"
                onClick={() => navigate("/prompts")}
              >
                <CardHeader>
                  <Settings className="h-8 w-8 mb-2 text-primary" />
                  <CardTitle>Prompt Engineering</CardTitle>
                  <CardDescription>
                    Get AI-powered suggestions to improve your prompts
                  </CardDescription>
                </CardHeader>
              </Card>
            </div>
          </div>

          {/* Recent Agents */}
          {agents.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold">Your Agents</h3>
                <Button onClick={() => navigate("/agents")}>
                  <Plus className="h-4 w-4 mr-2" />
                  New Agent
                </Button>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {agents.slice(0, 6).map((agent) => (
                  <Card
                    key={agent.id}
                    className="cursor-pointer hover:border-primary transition-colors"
                    onClick={() => navigate(`/chat/${agent.id}`)}
                  >
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Bot className="h-5 w-5" />
                        {agent.name}
                      </CardTitle>
                      <CardDescription className="line-clamp-2">
                        {agent.description || "No description"}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between text-sm text-muted-foreground">
                        <span>{agent.document_count || 0} documents</span>
                        <span className="capitalize">{agent.personality}</span>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
