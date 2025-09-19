import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { useToast } from '@/hooks/use-toasts';
import { Loader2 } from 'lucide-react';

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface UserConfig {
  embedding_model: string;
  llm_provider: string;
  ollama_base_url: string;
  ollama_model: string;
  openai_api_key?: string;
  openai_model: string;
  chunk_size: number;
  chunk_overlap: number;
  max_file_size_mb: number;
  theme: string;
  language: string;
  enable_telemetry: boolean;
  custom_data_directory?: string;
}

export function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  const [config, setConfig] = useState<UserConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    if (open) {
      loadConfig();
    }
  }, [open]);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/config');
      const data = await response.json();
      setConfig(data.config);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load settings',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    if (!config) return;

    setSaving(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Settings saved successfully',
        });
        onOpenChange(false);
      } else {
        throw new Error('Failed to save settings');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save settings',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const testLLMConnection = async () => {
    setTestingConnection(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/config/test-llm', {
        method: 'POST',
      });
      const data = await response.json();

      if (data.status === 'connected') {
        toast({
          title: 'Connection Successful',
          description: `Connected to ${data.provider}. Found ${data.available_models?.length || 0} models.`,
        });
      } else {
        toast({
          title: 'Connection Failed',
          description: data.message,
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to test connection',
        variant: 'destructive',
      });
    } finally {
      setTestingConnection(false);
    }
  };

  if (!config || loading) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Configure Local Mind to work with your preferred models and settings
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="models" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="models">Models</TabsTrigger>
            <TabsTrigger value="processing">Processing</TabsTrigger>
            <TabsTrigger value="general">General</TabsTrigger>
          </TabsList>

          <TabsContent value="models" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="llm-provider">LLM Provider</Label>
              <Select
                value={config.llm_provider}
                onValueChange={(value) =>
                  setConfig({ ...config, llm_provider: value })
                }
              >
                <SelectTrigger id="llm-provider">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ollama">Ollama</SelectItem>
                  <SelectItem value="openai">OpenAI</SelectItem>
                  <SelectItem value="llamacpp">LlamaCPP</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {config.llm_provider === 'ollama' && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="ollama-url">Ollama Base URL</Label>
                  <Input
                    id="ollama-url"
                    value={config.ollama_base_url}
                    onChange={(e) =>
                      setConfig({ ...config, ollama_base_url: e.target.value })
                    }
                    placeholder="http://localhost:11434"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ollama-model">Ollama Model</Label>
                  <Input
                    id="ollama-model"
                    value={config.ollama_model}
                    onChange={(e) =>
                      setConfig({ ...config, ollama_model: e.target.value })
                    }
                    placeholder="llama2"
                  />
                </div>
              </>
            )}

            {config.llm_provider === 'openai' && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="openai-key">OpenAI API Key</Label>
                  <Input
                    id="openai-key"
                    type="password"
                    value={config.openai_api_key || ''}
                    onChange={(e) =>
                      setConfig({ ...config, openai_api_key: e.target.value })
                    }
                    placeholder="sk-..."
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="openai-model">OpenAI Model</Label>
                  <Select
                    value={config.openai_model}
                    onValueChange={(value) =>
                      setConfig({ ...config, openai_model: value })
                    }
                  >
                    <SelectTrigger id="openai-model">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                      <SelectItem value="gpt-4">GPT-4</SelectItem>
                      <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}

            <div className="space-y-2">
              <Label htmlFor="embedding-model">Embedding Model</Label>
              <Select
                value={config.embedding_model}
                onValueChange={(value) =>
                  setConfig({ ...config, embedding_model: value })
                }
              >
                <SelectTrigger id="embedding-model">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all-MiniLM-L6-v2">all-MiniLM-L6-v2 (Default)</SelectItem>
                  <SelectItem value="all-mpnet-base-v2">all-mpnet-base-v2</SelectItem>
                  <SelectItem value="multi-qa-mpnet-base-dot-v1">multi-qa-mpnet-base-dot-v1</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={testLLMConnection}
              disabled={testingConnection}
              variant="outline"
              className="w-full"
            >
              {testingConnection ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Testing Connection...
                </>
              ) : (
                'Test LLM Connection'
              )}
            </Button>
          </TabsContent>

          <TabsContent value="processing" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="chunk-size">
                Chunk Size: {config.chunk_size}
              </Label>
              <Slider
                id="chunk-size"
                min={256}
                max={2048}
                step={128}
                value={[config.chunk_size]}
                onValueChange={(value) =>
                  setConfig({ ...config, chunk_size: value[0] })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="chunk-overlap">
                Chunk Overlap: {config.chunk_overlap}
              </Label>
              <Slider
                id="chunk-overlap"
                min={0}
                max={200}
                step={10}
                value={[config.chunk_overlap]}
                onValueChange={(value) =>
                  setConfig({ ...config, chunk_overlap: value[0] })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="max-file-size">
                Max File Size (MB): {config.max_file_size_mb}
              </Label>
              <Slider
                id="max-file-size"
                min={10}
                max={500}
                step={10}
                value={[config.max_file_size_mb]}
                onValueChange={(value) =>
                  setConfig({ ...config, max_file_size_mb: value[0] })
                }
              />
            </div>
          </TabsContent>

          <TabsContent value="general" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="theme">Theme</Label>
              <Select
                value={config.theme}
                onValueChange={(value) =>
                  setConfig({ ...config, theme: value })
                }
              >
                <SelectTrigger id="theme">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="system">System</SelectItem>
                  <SelectItem value="light">Light</SelectItem>
                  <SelectItem value="dark">Dark</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="custom-data-dir">
                Custom Data Directory (Optional)
              </Label>
              <Input
                id="custom-data-dir"
                value={config.custom_data_directory || ''}
                onChange={(e) =>
                  setConfig({ ...config, custom_data_directory: e.target.value })
                }
                placeholder="Leave empty for default"
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="telemetry">Enable Telemetry</Label>
              <Switch
                id="telemetry"
                checked={config.enable_telemetry}
                onCheckedChange={(checked) =>
                  setConfig({ ...config, enable_telemetry: checked })
                }
              />
            </div>
          </TabsContent>
        </Tabs>

        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={saveConfig} disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Settings'
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}