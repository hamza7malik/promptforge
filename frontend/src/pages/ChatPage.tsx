import { useEffect, useState, useRef } from "react";
import { useAgentStore } from "@/stores/agentStore";
import { useConversationStore } from "@/stores/conversationStore";
import { apiClient } from "@/api";
import { Button, Card, CardContent, Input } from "@/components";
import {
  Bot,
  Plus,
  Send,
  Trash2,
  MessageSquare,
  User,
  Loader2,
  FileText,
  X,
  Wand2,
} from "lucide-react";
import type { Message } from "@/types";
import PromptGenerationModal from "@/components/PromptGenerationModal";

export default function ChatPage() {
  const { agents, fetchAgents } = useAgentStore();
  const {
    conversations,
    currentConversation,
    messages,
    fetchConversations,
    createConversation,
    deleteConversation,
    setCurrentConversation,
    addMessage,
  } = useConversationStore();

  const [selectedAgentId, setSelectedAgentId] = useState<string>("");
  const [messageText, setMessageText] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [showNewConversationModal, setShowNewConversationModal] =
    useState(false);
  const [newConversationTitle, setNewConversationTitle] = useState("");
  const [showContextModal, setShowContextModal] = useState(false);
  const [selectedChunks, setSelectedChunks] = useState<any[]>([]);
  const [showPromptModal, setShowPromptModal] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchAgents();
    fetchConversations();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleCreateConversation = async () => {
    if (!selectedAgentId) return;

    try {
      const conversation = await createConversation(
        selectedAgentId,
        newConversationTitle || undefined
      );
      setCurrentConversation(conversation);
      setShowNewConversationModal(false);
      setNewConversationTitle("");
    } catch (err) {
      console.error("Failed to create conversation:", err);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageText.trim() || !currentConversation || isSending) return;

    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: currentConversation.id,
      role: "user",
      content: messageText,
      created_at: new Date().toISOString(),
    };

    addMessage(userMessage);
    setMessageText("");
    setIsSending(true);

    try {
      const response = await apiClient.chatWithAgent(
        currentConversation.agent_id,
        {
          conversation_id: currentConversation.id,
          message: messageText,
          stream: false,
        }
      );

      if (typeof response !== "object" || !("content" in response)) {
        throw new Error("Invalid response format");
      }

      // Map API response to Message format
      const assistantMessage: Message = {
        id: response.message_id,
        conversation_id: response.conversation_id,
        role: "assistant",
        content: response.content,
        retrieved_chunks: response.retrieved_chunks,
        tokens_used: response.tokens_used,
        latency_ms: response.latency_ms,
        created_at: new Date().toISOString(),
      };

      addMessage(assistantMessage);
    } catch (err) {
      console.error("Failed to send message:", err);
      addMessage({
        id: `error-${Date.now()}`,
        conversation_id: currentConversation.id,
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
        created_at: new Date().toISOString(),
      });
    } finally {
      setIsSending(false);
    }
  };

  const handleDeleteConversation = async (conversationId: string) => {
    if (window.confirm("Delete this conversation?")) {
      try {
        await deleteConversation(conversationId);
      } catch (err) {
        console.error("Failed to delete conversation:", err);
      }
    }
  };

  const handleGeneratePrompt = async (formData: any) => {
    if (!currentConversation || !selectedAgent) return;

    try {
      setIsSending(true);
      const result = await apiClient.generatePrompt({
        agent_id: selectedAgent.id,
        ...formData,
      });

      // Add the generated prompt as an assistant message
      const assistantMessage: Message = {
        id: result.id,
        conversation_id: currentConversation.id,
        role: "assistant",
        content: `# Generated Expert Prompt\n\n${
          result.generated_prompt
        }\n\n---\n\n**Confidence:** ${(result.confidence_score * 100).toFixed(
          0
        )}% | **Tokens:** ${result.tokens_count} | **Time:** ${
          result.generation_time_ms
        }ms`,
        retrieved_chunks: result.contexts_used,
        created_at: new Date().toISOString(),
      };

      addMessage(assistantMessage);
      setShowPromptModal(false);
    } catch (err) {
      console.error("Failed to generate prompt:", err);
    } finally {
      setIsSending(false);
    }
  };

  const filteredConversations = selectedAgentId
    ? conversations.filter((c) => c.agent_id === selectedAgentId)
    : conversations;

  const selectedAgent = agents.find((a) => a.id === selectedAgentId);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar - Agent & Conversation Selection */}
      <div className="w-80 bg-white border-r flex flex-col">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold mb-3">Select Agent</h2>
          <select
            value={selectedAgentId}
            onChange={(e) => {
              setSelectedAgentId(e.target.value);
              setCurrentConversation(null);
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Choose an agent...</option>
            {agents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
        </div>

        {selectedAgentId && (
          <>
            <div className="p-4 border-b">
              <Button
                onClick={() => setShowNewConversationModal(true)}
                className="w-full flex items-center justify-center gap-2"
              >
                <Plus className="w-4 h-4" />
                New Conversation
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto">
              <div className="p-2">
                {filteredConversations.length === 0 ? (
                  <p className="text-center text-gray-500 text-sm py-8">
                    No conversations yet
                  </p>
                ) : (
                  filteredConversations.map((conv) => (
                    <div
                      key={conv.id}
                      className={`p-3 mb-2 rounded-lg cursor-pointer group hover:bg-gray-50 ${
                        currentConversation?.id === conv.id
                          ? "bg-blue-50 border border-blue-200"
                          : "border border-transparent"
                      }`}
                      onClick={() => setCurrentConversation(conv)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <MessageSquare className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <p className="text-sm font-medium truncate">
                              {conv.title || "Untitled Conversation"}
                            </p>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(conv.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteConversation(conv.id);
                          }}
                          className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded"
                        >
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {!currentConversation ? (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <Bot className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-xl font-medium mb-2">
                No Conversation Selected
              </h3>
              <p className="text-sm">
                {selectedAgentId
                  ? "Create a new conversation or select an existing one"
                  : "Select an agent to get started"}
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Chat Header */}
            <div className="bg-white border-b p-4">
              <div className="flex items-center gap-3">
                <Bot className="w-8 h-8 text-blue-600" />
                <div>
                  <h2 className="font-semibold">
                    {selectedAgent?.name || "Agent"}
                  </h2>
                  <p className="text-sm text-gray-500">
                    {currentConversation.title || "Untitled Conversation"}
                  </p>
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <p>Start a conversation with {selectedAgent?.name}</p>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 ${
                      message.role === "user" ? "justify-end" : ""
                    }`}
                  >
                    {message.role === "assistant" && (
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                        <Bot className="w-5 h-5 text-blue-600" />
                      </div>
                    )}
                    <div
                      className={`max-w-[70%] rounded-lg p-4 ${
                        message.role === "user"
                          ? "bg-blue-600 text-white"
                          : "bg-white border border-gray-200"
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">
                        {message.content}
                      </p>

                      <div className="flex items-center gap-2 mt-2">
                        {/* View Context Button */}
                        {message.role === "assistant" &&
                          message.retrieved_chunks &&
                          message.retrieved_chunks.length > 0 && (
                            <button
                              onClick={() => {
                                setSelectedChunks(
                                  message.retrieved_chunks || []
                                );
                                setShowContextModal(true);
                              }}
                              className="text-xs px-2 py-1 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-md flex items-center gap-1 transition-colors"
                            >
                              <FileText className="w-3 h-3" />
                              View Context ({message.retrieved_chunks.length})
                            </button>
                          )}

                        {message.tokens_used && (
                          <p className="text-xs opacity-70">
                            {message.tokens_used} tokens · {message.latency_ms}
                            ms
                          </p>
                        )}
                      </div>
                    </div>
                    {message.role === "user" && (
                      <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                        <User className="w-5 h-5 text-gray-600" />
                      </div>
                    )}
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input */}
            <div className="bg-white border-t p-4">
              <div className="flex gap-2 mb-2">
                <button
                  onClick={() => setShowPromptModal(true)}
                  className="text-xs px-3 py-1.5 bg-purple-50 text-purple-600 hover:bg-purple-100 rounded-md flex items-center gap-1.5 transition-colors"
                >
                  <Wand2 className="w-3.5 h-3.5" />
                  Generate Prompt
                </button>
              </div>
              <form onSubmit={handleSendMessage} className="flex gap-3">
                <Input
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  placeholder="Type your message..."
                  disabled={isSending}
                  className="flex-1"
                />
                <Button
                  type="submit"
                  disabled={isSending || !messageText.trim()}
                >
                  {isSending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </Button>
              </form>
            </div>
          </>
        )}
      </div>

      {/* New Conversation Modal */}
      {showNewConversationModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md">
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold mb-4">New Conversation</h3>
              <Input
                value={newConversationTitle}
                onChange={(e) => setNewConversationTitle(e.target.value)}
                placeholder="Conversation title (optional)"
                className="mb-4"
              />
              <div className="flex gap-3">
                <Button onClick={handleCreateConversation} className="flex-1">
                  Create
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowNewConversationModal(false);
                    setNewConversationTitle("");
                  }}
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {showContextModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-3xl max-h-[80vh] bg-white rounded-lg shadow-xl flex flex-col">
            <div className="p-6 border-b flex items-center justify-between flex-shrink-0">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Retrieved Context ({selectedChunks.length} chunks)
              </h3>
              <button
                onClick={() => setShowContextModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-3">
              {selectedChunks.map((chunk, idx) => (
                <div
                  key={idx}
                  className="bg-gray-50 p-4 rounded-lg border border-gray-200"
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className="text-xs font-semibold text-gray-500">
                      Chunk {idx + 1}
                    </span>
                    <div className="flex gap-2 text-xs">
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                        Score: {chunk.score.toFixed(3)}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap mb-2">
                    {chunk.content}
                  </p>
                  <p className="text-xs text-gray-500">
                    📄 {chunk.document_name}
                  </p>
                </div>
              ))}
            </div>

            {/* Fixed Footer */}
            <div className="p-6 border-t flex-shrink-0">
              <Button
                onClick={() => setShowContextModal(false)}
                variant="outline"
                className="w-full"
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Prompt Generation Modal */}
      <PromptGenerationModal
        isOpen={showPromptModal}
        onClose={() => setShowPromptModal(false)}
        onGenerate={handleGeneratePrompt}
        isGenerating={isSending}
      />
    </div>
  );
}
