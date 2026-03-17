import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { PageHeader } from '@/components/PageHeader';
import { FileDrop } from '@/components/FileDrop';
import { PasteText } from '@/components/PasteText';
import { SampleNotes } from '@/components/SampleNotes';
import { EntityChips } from '@/components/EntityChips';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ArrowRight, FileText } from 'lucide-react';
import {
  uploadFile,
  uploadText,
  API_URL,
  ENABLE_S3_DIRECT_UPLOAD,
  createPresignedUpload,
  putFileToPresignedUrl,
  processUploadedFile,
} from '@/lib/api';
import { useClaimStore } from '@/store/claimStore';
import { toast } from 'sonner';
import type { SampleNote } from '@/lib/sampleNotes';

export default function Upload() {
  const navigate = useNavigate();
  const [pastedText, setPastedText] = useState('');
  const { text, setText, setEntities, entities, setSuggestions } = useClaimStore();

  const uploadFileMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!ENABLE_S3_DIRECT_UPLOAD) {
        return uploadFile(file);
      }
      const presigned = await createPresignedUpload({
        filename: file.name,
        content_type: file.type || 'application/octet-stream',
      });
      await putFileToPresignedUrl(presigned.upload_url, file, presigned.headers || {});
      return processUploadedFile(presigned.key, file.name);
    },
    onSuccess: (data) => {
      setText(data.text);
      setEntities(data.entities);
      setSuggestions([]);
      toast.success('Document processed successfully');
    },
    onError: (error: any) => {
      const status = (error && (error as any).response && (error as any).response.status) as number | undefined;
      const statusText = (error && (error as any).response && (error as any).response.statusText) as string | undefined;
      const msg = status
        ? `API ${status} ${statusText || ''}`.trim()
        : `Network error contacting ${API_URL}. Is the backend running and CORS allowing ${window.location.origin}?`;
      toast.error(msg);
      try { console.error('[uploadFile] error', error); } catch {}
    },
  });

  const uploadTextMutation = useMutation({
    mutationFn: uploadText,
    onSuccess: (data) => {
      setText(data.text);
      setEntities(data.entities);
      setSuggestions([]);
      toast.success('Text processed successfully');
    },
    onError: (error: any) => {
      const status = (error && (error as any).response && (error as any).response.status) as number | undefined;
      const statusText = (error && (error as any).response && (error as any).response.statusText) as string | undefined;
      const msg = status
        ? `API ${status} ${statusText || ''}`.trim()
        : `Network error contacting ${API_URL}. Is the backend running and CORS allowing ${window.location.origin}?`;
      toast.error(msg);
      try { console.error('[uploadText] error', error); } catch {}
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

  const handleSampleSelect = (sample: SampleNote) => {
    setPastedText(sample.text);
  };

  const handleContinue = () => {
    navigate('/suggest');
  };

  const isLoading = uploadFileMutation.isPending || uploadTextMutation.isPending;
  const hasContent = Boolean(text.trim());

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-7xl space-y-6 px-4 py-6 sm:space-y-8 sm:py-8">
        <PageHeader
          title="Upload Clinical Note"
          subtitle="Start by uploading a document or pasting clinical note text"
          step={{ current: 1, total: 3 }}
        />

        <div className="grid gap-6 lg:grid-cols-2 lg:gap-8">
          <Card className="p-4 sm:p-6">
            <div className="space-y-4">
              <h3 className="font-semibold">Drop PDF Or Image</h3>
              <FileDrop onFileSelect={handleFileSelect} />
            </div>
          </Card>

          <Card className="p-4 sm:p-6">
            <h3 className="mb-4 flex items-center gap-2 font-semibold">
              <FileText className="h-5 w-5 text-primary" />
              Extracted Content Preview
            </h3>

            {isLoading ? (
              <div className="space-y-3">
                <div className="h-4 animate-pulse rounded bg-muted" />
                <div className="h-4 w-5/6 animate-pulse rounded bg-muted" />
                <div className="h-4 w-4/6 animate-pulse rounded bg-muted" />
              </div>
            ) : hasContent ? (
              <div className="space-y-4">
                <div className="max-h-[300px] overflow-y-auto rounded-lg bg-muted/30 p-3 sm:p-4">
                  <pre className="font-mono text-sm whitespace-pre-wrap break-words">{text}</pre>
                </div>

                <div>
                  <p className="mb-3 text-sm text-muted-foreground">Detected Entities:</p>
                  {entities.length > 0 ? (
                    <EntityChips entities={entities} />
                  ) : (
                    <p className="text-sm text-muted-foreground">No entities detected yet.</p>
                  )}
                </div>

                <Button onClick={handleContinue} className="w-full" size="lg">
                  Suggest Codes
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </div>
            ) : (
              <div className="py-12 text-center text-muted-foreground">
                <p>Upload a document or process text to see the extracted preview</p>
              </div>
            )}
          </Card>

          <Card className="p-4 sm:p-6">
            <div className="space-y-4">
              <h3 className="font-semibold">Paste Clinical Notes</h3>
              <PasteText value={pastedText} onChange={setPastedText} />
              <Button
                onClick={handleTextSubmit}
                className="w-full"
                size="lg"
                disabled={!pastedText.trim() || isLoading}
              >
                {isLoading ? 'Processing...' : 'Process Text'}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </div>
          </Card>

          <div className="space-y-6">
            <SampleNotes onSelect={handleSampleSelect} />

            <Card className="border-primary/20 bg-accent/30 p-4 sm:p-6">
              <p className="text-sm leading-relaxed text-muted-foreground">
                <strong className="text-foreground">Flow:</strong> upload or paste a note, review the extracted text,
                then click <span className="font-medium text-foreground">Suggest Codes</span> to continue to the
                suggestions page.
              </p>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
