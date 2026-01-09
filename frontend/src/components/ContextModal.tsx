import { X, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface Context {
  content: string;
  score: number;
  document_name: string;
}

interface ContextModalProps {
  contexts: Context[];
  isOpen: boolean;
  onClose: () => void;
  title?: string;
}

export default function ContextModal({
  contexts,
  isOpen,
  onClose,
  title = "Retrieved Context",
}: ContextModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-4xl max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-md transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 p-4">
          {contexts.length === 0 ? (
            <p className="text-center text-gray-500 py-8">
              No context retrieved
            </p>
          ) : (
            <div className="space-y-4">
              {contexts.map((chunk, index) => (
                <div
                  key={index}
                  className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-gray-500" />
                      <span className="font-medium text-sm text-gray-900">
                        {chunk.document_name}
                      </span>
                    </div>
                    <Badge variant="secondary" className="text-xs">
                      {(chunk.score * 100).toFixed(1)}% match
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {chunk.content}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-4 border-t">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-gray-900 text-white rounded-md hover:bg-gray-800 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
