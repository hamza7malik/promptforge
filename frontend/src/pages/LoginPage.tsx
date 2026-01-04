import { useAuth0 } from "@auth0/auth0-react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components";

export default function LoginPage() {
  const { loginWithRedirect } = useAuth0();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-3xl font-bold">PromptForge</CardTitle>
          <p className="text-gray-600 text-lg">
            AI Agent Workspace for Prompt Engineers
          </p>
          <CardDescription className="text-lg">
            Build and manage expert AI agents with advanced RAG
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Create specialized AI agents trained on your documents. Get expert
              assistance with:
            </p>
            <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1">
              <li>RAG architecture and implementation</li>
              <li>LangChain and LlamaIndex expertise</li>
              <li>Prompt engineering best practices</li>
              <li>AI system debugging and optimization</li>
            </ul>
          </div>

          <Button
            onClick={() => loginWithRedirect()}
            className="w-full"
            size="lg"
          >
            Sign In with Auth0
          </Button>

          <p className="text-xs text-center text-muted-foreground">
            Production-ready platform for AI developers
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
