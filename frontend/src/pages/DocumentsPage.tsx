import { useEffect, useState } from "react";
import { useAgentStore } from "@/stores/agentStore";
import { apiClient } from "@/api";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components";
import {
  FileText,
  Upload,
  Trash2,
  CheckCircle,
  AlertCircle,
  Loader2,
  Download,
} from "lucide-react";
import type { Document } from "@/types";

export default function DocumentsPage() {
  const { agents, fetchAgents } = useAgentStore();
  const [selectedAgentId, setSelectedAgentId] = useState<string>("");
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAgents();
  }, []);

  useEffect(() => {
    if (selectedAgentId) {
      fetchDocuments();
    }
  }, [selectedAgentId]);

  const fetchDocuments = async () => {
    if (!selectedAgentId) return;

    setLoading(true);
    setError(null);
    try {
      const docs = await apiClient.listAgentDocuments(selectedAgentId);
      setDocuments(docs);
    } catch (err: any) {
      setError(err.message || "Failed to fetch documents");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file || !selectedAgentId) return;

    setUploading(true);
    setError(null);

    try {
      // Step 1: Get presigned URL
      const presignedData = await apiClient.getPresignedUploadUrl({
        agent_id: selectedAgentId,
        filename: file.name,
        file_type: file.type,
        file_size: file.size,
      });

      // Step 2: Upload file to S3
      await fetch(presignedData.upload_url, {
        method: "PUT",
        body: file,
        headers: {
          "Content-Type": file.type,
        },
      });

      // Step 3: Create document record
      await apiClient.createDocument({
        agent_id: selectedAgentId,
        filename: file.name,
        file_type: file.type,
        s3_key: presignedData.s3_key,
        file_size: file.size,
      });

      // Refresh documents list
      await fetchDocuments();

      // Reset file input
      event.target.value = "";
    } catch (err: any) {
      setError(err.message || "Failed to upload document");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (documentId: string) => {
    if (
      !window.confirm(
        "Delete this document? This will remove it from the vector database."
      )
    ) {
      return;
    }

    try {
      await apiClient.deleteDocument(documentId);
      await fetchDocuments();
    } catch (err: any) {
      setError(err.message || "Failed to delete document");
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case "processing":
        return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />;
      case "failed":
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Loader2 className="w-5 h-5 text-gray-400" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const selectedAgent = agents.find((a) => a.id === selectedAgentId);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Documents</h1>
          <p className="text-gray-600">Upload documents to train your agents</p>
        </div>

        {/* Agent Selection */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Select Agent</CardTitle>
            <CardDescription>
              Choose an agent to manage its documents
            </CardDescription>
          </CardHeader>
          <CardContent>
            <select
              value={selectedAgentId}
              onChange={(e) => setSelectedAgentId(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select an agent...</option>
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name}
                </option>
              ))}
            </select>
          </CardContent>
        </Card>

        {selectedAgentId && (
          <>
            {/* Upload Section */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Upload Document</CardTitle>
                <CardDescription>
                  Upload PDFs, DOCX, or TXT files to train {selectedAgent?.name}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                  <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={handleFileUpload}
                    disabled={uploading}
                    className="hidden"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <Button
                      type="button"
                      disabled={uploading}
                      onClick={() =>
                        document.getElementById("file-upload")?.click()
                      }
                    >
                      {uploading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Uploading...
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4 mr-2" />
                          Choose File
                        </>
                      )}
                    </Button>
                  </label>
                  <p className="text-sm text-gray-500 mt-2">
                    Supported formats: PDF, DOCX, TXT (Max 50MB)
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                {error}
              </div>
            )}

            {/* Documents List */}
            <Card>
              <CardHeader>
                <CardTitle>Uploaded Documents ({documents.length})</CardTitle>
                <CardDescription>
                  Manage documents for {selectedAgent?.name}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center py-8">
                    <Loader2 className="w-8 h-8 animate-spin mx-auto text-gray-400" />
                    <p className="text-gray-500 mt-2">Loading documents...</p>
                  </div>
                ) : documents.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <FileText className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                    <p>No documents uploaded yet</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {documents.map((doc) => (
                      <div
                        key={doc.id}
                        className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                      >
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <FileText className="w-8 h-8 text-blue-600 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <h3 className="font-medium truncate">
                              {doc.filename}
                            </h3>
                            <div className="flex items-center gap-3 text-sm text-gray-500">
                              <span>
                                {doc.file_size
                                  ? formatFileSize(doc.file_size)
                                  : "Unknown size"}
                              </span>
                              <span>•</span>
                              <span>{doc.num_chunks} chunks</span>
                              <span>•</span>
                              <span>
                                {new Date(doc.created_at).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(doc.status)}
                            <span className="text-sm capitalize">
                              {doc.status}
                            </span>
                          </div>
                          <button
                            onClick={() => handleDelete(doc.id)}
                            className="p-2 hover:bg-red-50 rounded-lg"
                          >
                            <Trash2 className="w-4 h-4 text-red-600" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
