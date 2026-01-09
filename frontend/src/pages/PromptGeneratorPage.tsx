import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import {
  Copy,
  Check,
  ThumbsUp,
  ThumbsDown,
  Save,
  Loader2,
  AlertCircle,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { apiClient } from "@/api/client";
import { Agent, GeneratedPrompt } from "@/types";
import ContextModal from "@/components/ContextModal";

const ARCHITECTURE_STYLES = [
  { value: "microservices", label: "Microservices" },
  { value: "monolithic", label: "Monolithic" },
  { value: "serverless", label: "Serverless" },
  { value: "hybrid", label: "Hybrid" },
];

export default function PromptGeneratorPage() {
  const { agentId } = useParams<{ agentId: string }>();

  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);

  // Form state
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

  // Generated prompt state
  const [generatedPrompt, setGeneratedPrompt] =
    useState<GeneratedPrompt | null>(null);
  const [copied, setCopied] = useState(false);
  const [rating, setRating] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showContextModal, setShowContextModal] = useState(false);

  useEffect(() => {
    if (agentId) {
      fetchAgent();
    }
  }, [agentId]);

  const fetchAgent = async () => {
    try {
      setLoading(true);
      const agent = await apiClient.getAgent(agentId!);
      setAgent(agent);
    } catch (err) {
      setError("Failed to load agent");
    } finally {
      setLoading(false);
    }
  };

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

  const handleGenerate = async () => {
    if (!featureName.trim() || !userStory.trim()) {
      setError("Feature name and user story are required");
      return;
    }

    try {
      setGenerating(true);
      setError(null);

      const result = await apiClient.generatePrompt({
        agent_id: agentId,
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

      setGeneratedPrompt(result);
      setRating(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to generate prompt");
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = async () => {
    if (!generatedPrompt?.generated_prompt) return;

    try {
      await navigator.clipboard.writeText(generatedPrompt.generated_prompt);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      setError("Failed to copy to clipboard");
    }
  };

  const handleSave = async () => {
    if (!generatedPrompt?.id) return;

    try {
      setSaving(true);
      await apiClient.savePrompt({
        prompt_id: generatedPrompt.id,
        is_public: false,
        tags: techStack,
      });

      setGeneratedPrompt({ ...generatedPrompt, is_saved: true });
    } catch (err) {
      setError("Failed to save prompt");
    } finally {
      setSaving(false);
    }
  };

  const handleRate = async (ratingValue: number) => {
    if (!generatedPrompt?.id) return;

    try {
      await apiClient.ratePrompt({
        prompt_id: generatedPrompt.id,
        rating: ratingValue,
        was_successful: ratingValue >= 4,
      });

      setRating(ratingValue);
    } catch (err) {
      setError("Failed to rate prompt");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-6 max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Generate Expert Prompt</h1>
          {agent && (
            <p className="text-muted-foreground">
              Using{" "}
              <span className="text-primary font-medium">{agent.name}</span>{" "}
              agent
            </p>
          )}
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Form Section */}
          <Card className="">
            <CardHeader>
              <CardTitle className="">Feature Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Feature Name */}
              <div className="space-y-2">
                <Label htmlFor="feature-name" className="">
                  Feature Name *
                </Label>
                <Input
                  id="feature-name"
                  placeholder="e.g., User Authentication System"
                  value={featureName}
                  onChange={(e) => setFeatureName(e.target.value)}
                  className=""
                />
              </div>

              {/* User Story */}
              <div className="space-y-2">
                <Label htmlFor="user-story" className="">
                  User Story *
                </Label>
                <Textarea
                  id="user-story"
                  placeholder="As a user, I want to..."
                  value={userStory}
                  onChange={(e) => setUserStory(e.target.value)}
                  rows={4}
                  className=""
                />
              </div>

              {/* Tech Stack */}
              <div className="space-y-2">
                <Label className="">Tech Stack</Label>
                <div className="flex gap-2">
                  <Input
                    placeholder="Add technology (e.g., React)"
                    value={techInput}
                    onChange={(e) => setTechInput(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        addItem(techInput, techStack, setTechStack);
                        setTechInput("");
                      }
                    }}
                    className=""
                  />
                  <Button
                    onClick={() => {
                      addItem(techInput, techStack, setTechStack);
                      setTechInput("");
                    }}
                    variant="outline"
                    className=""
                  >
                    Add
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
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
                <Label className="">Requirements</Label>
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
                    className=""
                  />
                  <Button
                    onClick={() => {
                      addItem(reqInput, requirements, setRequirements);
                      setReqInput("");
                    }}
                    variant="outline"
                    className=""
                  >
                    Add
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
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

              {/* Constraints */}
              <div className="space-y-2">
                <Label className="">Constraints</Label>
                <div className="flex gap-2">
                  <Input
                    placeholder="Add constraint"
                    value={constraintInput}
                    onChange={(e) => setConstraintInput(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        addItem(constraintInput, constraints, setConstraints);
                        setConstraintInput("");
                      }
                    }}
                    className=""
                  />
                  <Button
                    onClick={() => {
                      addItem(constraintInput, constraints, setConstraints);
                      setConstraintInput("");
                    }}
                    variant="outline"
                    className=""
                  >
                    Add
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2 mt-2">
                  {constraints.map((constraint, index) => (
                    <Badge
                      key={index}
                      variant="secondary"
                      className="cursor-pointer"
                      onClick={() =>
                        removeItem(index, constraints, setConstraints)
                      }
                    >
                      {constraint} ×
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Architecture Style */}
              <div className="space-y-2">
                <Label htmlFor="architecture" className="">
                  Architecture Style
                </Label>
                <Select
                  value={architectureStyle}
                  onValueChange={setArchitectureStyle}
                >
                  <SelectTrigger className="">
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

              {/* Code Context */}
              <div className="space-y-2">
                <Label htmlFor="code-context" className="">
                  Existing Code Context (Optional)
                </Label>
                <Textarea
                  id="code-context"
                  placeholder="Paste relevant existing code..."
                  value={codeContext}
                  onChange={(e) => setCodeContext(e.target.value)}
                  rows={6}
                  className="font-mono text-sm"
                />
              </div>

              {/* Options */}
              <div className="space-y-3">
                <Label className="">Include</Label>
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
                    Documentation requirements
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
                    Error handling patterns
                  </label>
                </div>
              </div>

              <Button
                onClick={handleGenerate}
                disabled={
                  generating || !featureName.trim() || !userStory.trim()
                }
                className="w-full"
                size="lg"
              >
                {generating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  "Generate Prompt"
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Preview Section */}
          <Card className="">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="">Generated Prompt</CardTitle>
                {generatedPrompt && (
                  <div className="flex gap-2">
                    <Button
                      onClick={handleCopy}
                      variant="outline"
                      size="sm"
                      className=""
                    >
                      {copied ? (
                        <>
                          <Check className="mr-2 h-4 w-4" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="mr-2 h-4 w-4" />
                          Copy
                        </>
                      )}
                    </Button>
                    {!generatedPrompt.is_saved && (
                      <Button
                        onClick={handleSave}
                        disabled={saving}
                        variant="outline"
                        size="sm"
                        className=""
                      >
                        {saving ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <Save className="mr-2 h-4 w-4" />
                        )}
                        Save
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {!generatedPrompt ? (
                <div className="text-center py-12 text-muted-foreground">
                  <p>
                    Fill out the form and click "Generate Prompt" to create an
                    expert prompt
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Confidence Score */}
                  <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
                    <span className="text-sm text-muted-foreground">
                      Confidence Score
                    </span>
                    <Badge
                      variant={
                        generatedPrompt.confidence_score >= 0.7
                          ? "default"
                          : "secondary"
                      }
                    >
                      {(generatedPrompt.confidence_score * 100).toFixed(0)}%
                    </Badge>
                  </div>

                  {/* View Context Button */}
                  {generatedPrompt.contexts_used &&
                    generatedPrompt.contexts_used.length > 0 && (
                      <button
                        onClick={() => setShowContextModal(true)}
                        className="text-xs px-3 py-1.5 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-md flex items-center gap-1.5 transition-colors w-fit"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        View Context ({generatedPrompt.contexts_used.length})
                      </button>
                    )}

                  {/* Prompt Content */}
                  <div className="bg-muted p-4 rounded-lg overflow-auto max-h-[600px]">
                    <pre className="text-sm whitespace-pre-wrap font-mono">
                      {generatedPrompt.generated_prompt}
                    </pre>
                  </div>

                  {/* Rating */}
                  <div className="flex items-center justify-center gap-4 pt-4 border-t">
                    <span className="text-sm text-muted-foreground">
                      How was this prompt?
                    </span>
                    <div className="flex gap-2">
                      <Button
                        onClick={() => handleRate(5)}
                        variant={rating === 5 ? "default" : "outline"}
                        size="sm"
                        className=""
                      >
                        <ThumbsUp className="h-4 w-4" />
                      </Button>
                      <Button
                        onClick={() => handleRate(1)}
                        variant={rating === 1 ? "default" : "outline"}
                        size="sm"
                        className=""
                      >
                        <ThumbsDown className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="text-xs text-muted-foreground text-center">
                    Generated in {generatedPrompt.generation_time_ms}ms •{" "}
                    {generatedPrompt.tokens_count} tokens
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Context Modal */}
        <ContextModal
          contexts={generatedPrompt?.contexts_used || []}
          isOpen={showContextModal}
          onClose={() => setShowContextModal(false)}
          title="Retrieved Knowledge"
        />
      </div>
    </div>
  );
}
