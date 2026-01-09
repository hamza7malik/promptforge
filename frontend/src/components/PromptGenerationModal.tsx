import { useState } from "react";
import { X, Wand2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";

const ARCHITECTURE_STYLES = [
  { value: "microservices", label: "Microservices" },
  { value: "monolithic", label: "Monolithic" },
  { value: "serverless", label: "Serverless" },
  { value: "hybrid", label: "Hybrid" },
];

interface PromptGenerationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (data: any) => void;
  isGenerating: boolean;
}

export default function PromptGenerationModal({
  isOpen,
  onClose,
  onGenerate,
  isGenerating,
}: PromptGenerationModalProps) {
  const [featureName, setFeatureName] = useState("");
  const [userStory, setUserStory] = useState("");
  const [techStack, setTechStack] = useState<string[]>([]);
  const [techInput, setTechInput] = useState("");
  const [requirements, setRequirements] = useState<string[]>([]);
  const [reqInput, setReqInput] = useState("");
  const [constraints, setConstraints] = useState<string[]>([]);
  const [constraintInput, setConstraintInput] = useState("");
  const [architectureStyle, setArchitectureStyle] = useState("monolithic");
  const [codeContext, setCodeContext] = useState("");
  const [includeTests, setIncludeTests] = useState(true);
  const [includeDocumentation, setIncludeDocs] = useState(true);
  const [includeErrorHandling, setIncludeErrorHandling] = useState(true);

  const addItem = (
    value: string,
    list: string[],
    setter: (list: string[]) => void
  ) => {
    if (value.trim() && !list.includes(value.trim())) {
      setter([...list, value.trim()]);
    }
  };

  const removeItem = (
    index: number,
    list: string[],
    setter: (list: string[]) => void
  ) => {
    setter(list.filter((_, i) => i !== index));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!featureName.trim() || !userStory.trim()) return;

    onGenerate({
      feature_name: featureName,
      user_story: userStory,
      tech_stack: techStack,
      requirements,
      constraints,
      existing_code_context: codeContext,
      architecture_style: architectureStyle,
      include_tests: includeTests,
      include_documentation: includeDocumentation,
      include_error_handling: includeErrorHandling,
    });
  };

  const resetForm = () => {
    setFeatureName("");
    setUserStory("");
    setTechStack([]);
    setRequirements([]);
    setConstraints([]);
    setCodeContext("");
    setArchitectureStyle("monolithic");
    setIncludeTests(true);
    setIncludeDocs(true);
    setIncludeErrorHandling(true);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <Wand2 className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold">Generate Expert Prompt</h2>
          </div>
          <button
            onClick={handleClose}
            className="p-1 hover:bg-gray-100 rounded-md transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="overflow-y-auto flex-1 p-4">
          <div className="space-y-4">
            {/* Feature Name */}
            <div className="space-y-2">
              <Label htmlFor="feature-name">Feature Name *</Label>
              <Input
                id="feature-name"
                placeholder="e.g., User Authentication System"
                value={featureName}
                onChange={(e) => setFeatureName(e.target.value)}
                required
              />
            </div>

            {/* User Story */}
            <div className="space-y-2">
              <Label htmlFor="user-story">User Story *</Label>
              <Textarea
                id="user-story"
                placeholder="As a user, I want to..."
                value={userStory}
                onChange={(e) => setUserStory(e.target.value)}
                rows={3}
                required
              />
            </div>

            {/* Tech Stack */}
            <div className="space-y-2">
              <Label>Tech Stack</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Add technology"
                  value={techInput}
                  onChange={(e) => setTechInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addItem(techInput, techStack, setTechStack);
                      setTechInput("");
                    }
                  }}
                />
                <Button
                  type="button"
                  onClick={() => {
                    addItem(techInput, techStack, setTechStack);
                    setTechInput("");
                  }}
                  variant="outline"
                  size="sm"
                >
                  Add
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {techStack.map((tech, index) => (
                  <Badge
                    key={index}
                    variant="secondary"
                    className="cursor-pointer"
                    onClick={() => removeItem(index, techStack, setTechStack)}
                  >
                    {tech} ×
                  </Badge>
                ))}
              </div>
            </div>

            {/* Requirements */}
            <div className="space-y-2">
              <Label>Requirements</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Add requirement"
                  value={reqInput}
                  onChange={(e) => setReqInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addItem(reqInput, requirements, setRequirements);
                      setReqInput("");
                    }
                  }}
                />
                <Button
                  type="button"
                  onClick={() => {
                    addItem(reqInput, requirements, setRequirements);
                    setReqInput("");
                  }}
                  variant="outline"
                  size="sm"
                >
                  Add
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {requirements.map((req, index) => (
                  <Badge
                    key={index}
                    variant="secondary"
                    className="cursor-pointer"
                    onClick={() =>
                      removeItem(index, requirements, setRequirements)
                    }
                  >
                    {req} ×
                  </Badge>
                ))}
              </div>
            </div>

            {/* Architecture Style */}
            <div className="space-y-2">
              <Label>Architecture Style</Label>
              <Select
                value={architectureStyle}
                onValueChange={setArchitectureStyle}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ARCHITECTURE_STYLES.map((style) => (
                    <SelectItem key={style.value} value={style.value}>
                      {style.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Options */}
            <div className="space-y-2">
              <Label>Include</Label>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="tests"
                    checked={includeTests}
                    onCheckedChange={(checked: boolean) =>
                      setIncludeTests(checked)
                    }
                  />
                  <label htmlFor="tests" className="text-sm cursor-pointer">
                    Testing guidelines
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="docs"
                    checked={includeDocumentation}
                    onCheckedChange={(checked: boolean) =>
                      setIncludeDocs(checked)
                    }
                  />
                  <label htmlFor="docs" className="text-sm cursor-pointer">
                    Documentation
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="errors"
                    checked={includeErrorHandling}
                    onCheckedChange={(checked: boolean) =>
                      setIncludeErrorHandling(checked)
                    }
                  />
                  <label htmlFor="errors" className="text-sm cursor-pointer">
                    Error handling
                  </label>
                </div>
              </div>
            </div>
          </div>
        </form>

        <div className="p-4 border-t flex gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isGenerating || !featureName.trim() || !userStory.trim()}
            className="flex-1"
          >
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Wand2 className="mr-2 h-4 w-4" />
                Generate Prompt
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
