import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { PageHeader } from '@/components/PageHeader';
import { FileDrop } from '@/components/FileDrop';
import { PasteText } from '@/components/PasteText';
import { EntityChips } from '@/components/EntityChips';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ArrowRight, FileText } from 'lucide-react';
import { uploadFile, uploadText } from '@/lib/api';
import { useClaimStore } from '@/store/claimStore';
import { toast } from 'sonner';

export default function Upload() {
  const navigate = useNavigate();
  const [pastedText, setPastedText] = useState('');
  const { setText, setEntities, entities } = useClaimStore();

  const uploadFileMutation = useMutation({
    mutationFn: uploadFile,
    onSuccess: (data) => {
      setText(data.text);
      setEntities(data.entities);
      toast.success('Document processed successfully');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to process document');
    },
  });

  const uploadTextMutation = useMutation({
    mutationFn: uploadText,
    onSuccess: (data) => {
      setText(data.text);
      setEntities(data.entities);
      toast.success('Text processed successfully');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to process text');
    },
  });

  const handleFileSelect = (file: File) => {
    uploadFileMutation.mutate(file);
  };

  const handleTextSubmit = () => {
    if (pastedText.trim()) {
      uploadTextMutation.mutate(pastedText);
    }
  };

  const handleContinue = () => {
    navigate('/suggest');
  };

  const isLoading = uploadFileMutation.isPending || uploadTextMutation.isPending;
  const hasContent = entities.length > 0;

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-7xl px-4 py-8 space-y-8">
        <PageHeader
          title="Upload Clinical Note"
          subtitle="Start by uploading a document or pasting clinical note text"
          step={{ current: 1, total: 3 }}
        />

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left: Upload Section */}
          <div className="space-y-6">
            <FileDrop onFileSelect={handleFileSelect} />
            
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <Separator />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="bg-background px-4 text-muted-foreground">or</span>
              </div>
            </div>

            <PasteText value={pastedText} onChange={setPastedText} />

            {pastedText.trim() && !hasContent && (
              <Button
                onClick={handleTextSubmit}
                className="w-full"
                size="lg"
                disabled={isLoading}
              >
                {isLoading ? 'Processing...' : 'Process Text'}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            )}
          </div>

          {/* Right: Preview Section */}
          <div className="space-y-6">
            <Card className="p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                Extracted Content Preview
              </h3>

              {isLoading ? (
                <div className="space-y-3">
                  <div className="h-4 bg-muted animate-pulse rounded" />
                  <div className="h-4 bg-muted animate-pulse rounded w-5/6" />
                  <div className="h-4 bg-muted animate-pulse rounded w-4/6" />
                </div>
              ) : hasContent ? (
                <div className="space-y-4">
                  <div className="bg-muted/30 p-4 rounded-lg max-h-[300px] overflow-y-auto">
                    <pre className="font-mono text-sm whitespace-pre-wrap break-words">
                      {useClaimStore.getState().text}
                    </pre>
                  </div>
                  
                  <div>
                    <p className="text-sm text-muted-foreground mb-3">Detected Entities:</p>
                    <EntityChips entities={entities} />
                  </div>

                  <Button
                    onClick={handleContinue}
                    className="w-full"
                    size="lg"
                  >
                    Continue to Suggestions
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Button>
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <p>Upload a document or paste text to see the preview</p>
                </div>
              )}
            </Card>

            {hasContent && (
              <Card className="p-6 bg-accent/30 border-primary/20">
                <p className="text-sm leading-relaxed text-muted-foreground">
                  <strong className="text-foreground">Next step:</strong> Our AI will analyze this clinical note
                  and suggest appropriate ICD-10 diagnosis codes and CPT procedure codes based on the content.
                </p>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
