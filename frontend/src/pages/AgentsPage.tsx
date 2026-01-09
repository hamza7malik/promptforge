import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAgentStore } from "@/stores";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Textarea,
} from "@/components";
import {
  Bot,
  Plus,
  Edit2,
  Trash2,
  MessageSquare,
  FileText,
  X,
  Wand2,
} from "lucide-react";
import type { Agent, AgentCreate } from "@/types";

const DEFAULT_FORM_DATA: AgentCreate = {
  name: "",
  description: "",
  system_prompt: "",
  personality: "professional",
  expertise: "",
  model: "gpt-4-1106-preview",
  temperature: 0.7,
  max_tokens: 4096,
  top_k_retrieval: 5,
};

export default function AgentsPage() {
  const navigate = useNavigate();
  const {
    agents,
    loading,
    error,
    fetchAgents,
    createAgent,
    updateAgent,
    deleteAgent,
  } = useAgentStore();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<string | null>(null);
  const [formData, setFormData] = useState<AgentCreate>(DEFAULT_FORM_DATA);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    fetchAgents();
  }, []);

  const handleOpenModal = (agent?: Agent) => {
    if (agent) {
      setEditingAgent(agent.id);
      setFormData({
        name: agent.name,
        description: agent.description || "",
        system_prompt: agent.system_prompt || "",
        personality: agent.personality || "professional",
        expertise: agent.expertise || "",
        model: agent.model,
        temperature: agent.temperature,
        max_tokens: agent.max_tokens,
        top_k_retrieval: agent.top_k_retrieval,
      });
    } else {
      setEditingAgent(null);
      setFormData(DEFAULT_FORM_DATA);
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingAgent(null);
    setFormData(DEFAULT_FORM_DATA);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      if (editingAgent) {
        await updateAgent(editingAgent, formData);
      } else {
        await createAgent(formData);
      }
      handleCloseModal();
      await fetchAgents();
    } catch (err) {
      console.error("Failed to save agent:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (agentId: string) => {
    if (window.confirm("Are you sure you want to delete this agent?")) {
      try {
        await deleteAgent(agentId);
        fetchAgents();
      } catch (err) {
        console.error("Failed to delete agent:", err);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">AI Agents</h1>
            <p className="text-gray-600">Create and manage your AI agents</p>
          </div>
          <Button
            onClick={() => handleOpenModal()}
            className="flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Create New Agent
          </Button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading agents...</p>
          </div>
        )}

        {/* Agents Grid */}
        {!loading && agents.length === 0 && (
          <Card className="text-center py-12">
            <CardContent>
              <Bot className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">No agents yet</h3>
              <p className="text-gray-600 mb-4">
                Create your first AI agent to get started
              </p>
              <Button onClick={() => handleOpenModal()}>
                <Plus className="w-4 h-4 mr-2" />
                Create Agent
              </Button>
            </CardContent>
          </Card>
        )}

        {!loading && agents.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agents.map((agent) => (
              <Card
                key={agent.id}
                className="hover:shadow-lg transition-shadow"
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        <Bot className="w-6 h-6 text-blue-600" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{agent.name}</CardTitle>
                        <CardDescription className="text-sm">
                          {agent.model}
                        </CardDescription>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                    {agent.description || "No description"}
                  </p>

                  <div className="flex flex-wrap gap-2 mb-4">
                    {agent.personality && (
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs capitalize">
                        {agent.personality}
                      </span>
                    )}
                    <span className="px-2 py-1 bg-gray-100 rounded text-xs">
                      Temp: {agent.temperature}
                    </span>
                    <span className="px-2 py-1 bg-gray-100 rounded text-xs">
                      Top-K: {agent.top_k_retrieval}
                    </span>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1"
                      onClick={() => navigate(`/chat/${agent.id}`)}
                    >
                      <MessageSquare className="w-4 h-4 mr-1" />
                      Chat
                    </Button>
                    <Button
                      size="sm"
                      variant="default"
                      onClick={() => navigate(`/generate/${agent.id}`)}
                    >
                      <Wand2 className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => navigate(`/documents/${agent.id}`)}
                    >
                      <FileText className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleOpenModal(agent)}
                    >
                      <Edit2 className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDelete(agent.id)}
                      className="text-red-600 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Create/Edit Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
                <h2 className="text-2xl font-bold">
                  {editingAgent ? "Edit Agent" : "Create New Agent"}
                </h2>
                <button
                  onClick={handleCloseModal}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                {/* Name */}
                <div>
                  <Label htmlFor="name">Agent Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    placeholder="e.g., Research Assistant"
                    required
                  />
                </div>

                {/* Description */}
                <div>
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) =>
                      setFormData({ ...formData, description: e.target.value })
                    }
                    placeholder="Brief description of what this agent does"
                  />
                </div>

                {/* System Prompt */}
                <div>
                  <Label htmlFor="system_prompt">
                    System Prompt / Instructions *
                  </Label>
                  <Textarea
                    id="system_prompt"
                    value={formData.system_prompt}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        system_prompt: e.target.value,
                      })
                    }
                    placeholder="You are a helpful AI assistant that..."
                    rows={6}
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Define the agent's behavior, personality, and expertise
                  </p>
                </div>

                {/* Model Selection */}
                <div>
                  <Label htmlFor="model">Model</Label>
                  <select
                    id="model"
                    value={formData.model}
                    onChange={(e) =>
                      setFormData({ ...formData, model: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="gpt-4-1106-preview">
                      GPT-4 Turbo (Recommended)
                    </option>
                    <option value="gpt-4">GPT-4</option>
                    <option value="gpt-3.5-turbo">
                      GPT-3.5 Turbo (Faster)
                    </option>
                  </select>
                </div>

                {/* Temperature */}
                <div>
                  <Label htmlFor="temperature">
                    Temperature: {formData.temperature}
                  </Label>
                  <input
                    type="range"
                    id="temperature"
                    min="0"
                    max="2"
                    step="0.1"
                    value={formData.temperature}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        temperature: parseFloat(e.target.value),
                      })
                    }
                    className="w-full"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Lower = more focused, Higher = more creative
                  </p>
                </div>

                {/* Max Tokens */}
                <div>
                  <Label htmlFor="max_tokens">Max Tokens</Label>
                  <Input
                    type="number"
                    id="max_tokens"
                    value={formData.max_tokens}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        max_tokens: parseInt(e.target.value),
                      })
                    }
                    min="100"
                    max="128000"
                    step="100"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Maximum response length (GPT-4 Turbo: up to 128k)
                  </p>
                </div>

                {/* Personality */}
                <div>
                  <Label htmlFor="personality">Personality</Label>
                  <select
                    id="personality"
                    value={formData.personality}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        personality: e.target.value as any,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="professional">Professional</option>
                    <option value="friendly">Friendly</option>
                    <option value="technical">Technical</option>
                    <option value="creative">Creative</option>
                    <option value="analytical">Analytical</option>
                  </select>
                </div>

                {/* Expertise */}
                <div>
                  <Label htmlFor="expertise">Expertise / Domain</Label>
                  <Input
                    id="expertise"
                    value={formData.expertise}
                    onChange={(e) =>
                      setFormData({ ...formData, expertise: e.target.value })
                    }
                    placeholder="e.g., Software Engineering, Marketing, Finance"
                  />
                </div>

                {/* Top K Retrieval */}
                <div>
                  <Label htmlFor="top_k_retrieval">
                    Document Retrieval (Top-K): {formData.top_k_retrieval}
                  </Label>
                  <input
                    type="range"
                    id="top_k_retrieval"
                    min="1"
                    max="20"
                    step="1"
                    value={formData.top_k_retrieval}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        top_k_retrieval: parseInt(e.target.value),
                      })
                    }
                    className="w-full"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Number of relevant document chunks to retrieve for context
                  </p>
                </div>

                {/* Actions */}
                <div className="flex gap-3 pt-4">
                  <Button
                    type="submit"
                    className="flex-1"
                    disabled={isSubmitting}
                  >
                    {isSubmitting
                      ? "Saving..."
                      : editingAgent
                      ? "Update Agent"
                      : "Create Agent"}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCloseModal}
                    disabled={isSubmitting}
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
