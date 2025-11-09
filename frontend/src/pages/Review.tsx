import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { PageHeader } from '@/components/PageHeader';
import { ApprovedTable } from '@/components/ApprovedTable';
import { AmountEditor } from '@/components/AmountEditor';
import { SignatureBlock } from '@/components/SignatureBlock';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { TxBadge } from '@/components/TxBadge';
import { ArrowLeft, CheckCircle, FileText, Download, ClipboardList } from 'lucide-react';
import { generateClaim, downloadCms1500 } from '@/lib/api';
import { useClaimStore } from '@/store/claimStore';
import { useClaimsStore } from '@/store/claimsStore';
import { toast } from 'sonner';
import type { GenerateClaimResponse } from '@/lib/types';
import { CMS1500Dialog } from '@/components/CMS1500Dialog';

export default function Review() {
  const navigate = useNavigate();
  const [successData, setSuccessData] = useState<GenerateClaimResponse | null>(null);
  const [cmsOpen, setCmsOpen] = useState(false);
  const {
    approved,
    amount,
    signedBy,
    text,
    setAmount,
    setSignedBy,
    removeApproved,
    updateApproved,
    addApproved,
    reset,
  } = useClaimStore();
  const { add: addClaim } = useClaimsStore();

  const generateMutation = useMutation({
    mutationFn: generateClaim,
    onSuccess: (data) => {
      setSuccessData(data);
      // Add to local claim history
      try {
        addClaim({
          id: data.claim_id,
          date: new Date().toISOString(),
          codes_count: data.approved?.length || approved.length,
          amount: amount || undefined,
          tx_hash: data?.metadata?.tx?.hash || data?.metadata?.tx_hash,
        });
      } catch {}
      toast.success('Claim generated successfully');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to generate claim');
    },
  });

  const handleGenerate = () => {
    if (approved.length === 0) {
      toast.error('Please add at least one code');
      return;
    }
    
    if (!signedBy.trim()) {
      toast.error('Please sign the claim');
      return;
    }

    generateMutation.mutate({ approved, amount, signed_by: signedBy });
  };

  const handleBack = () => {
    navigate('/suggest');
  };

  const handleDownloadCMS1500 = async () => {
    try {
      const blob = await downloadCms1500({ approved, text });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'cms1500.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e: any) {
      toast.error(e?.message || 'Failed to generate CMS-1500 PDF');
    }
  };

  const handleOpenCMS = () => setCmsOpen(true);

  const handleCloseSuccess = () => {
    setSuccessData(null);
    reset();
    navigate('/claims');
  };

  if (approved.length === 0) {
    navigate('/suggest');
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-7xl px-4 py-8 space-y-8">
        <PageHeader
          title="Review & Sign Claim"
          subtitle="Verify the codes, add amount, and sign to generate the claim"
          step={{ current: 3, total: 3 }}
        />

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left: Approved Codes Table */}
          <div className="lg:col-span-2">
            <Card className="p-6">
              <ApprovedTable
                approved={approved}
                onRemove={removeApproved}
                onUpdate={updateApproved}
                onAdd={addApproved}
              />
            </Card>
          </div>

          {/* Right: Amount & Signature */}
          <div className="space-y-6">
          <AmountEditor amount={amount} onChange={setAmount} />
          <SignatureBlock signedBy={signedBy} onChange={setSignedBy} />

          <Button
            onClick={handleDownloadCMS1500}
            variant="outline"
            size="lg"
            className="w-full"
          >
            <Download className="mr-2 h-5 w-5" />
            Download CMS-1500 (Preview)
          </Button>

          <Button
            onClick={handleOpenCMS}
            variant="secondary"
            size="lg"
            className="w-full"
          >
            <ClipboardList className="mr-2 h-5 w-5" />
            Review & Generate CMS-1500
          </Button>

            <Button
              onClick={handleGenerate}
              size="lg"
              className="w-full"
              disabled={generateMutation.isPending || !signedBy.trim()}
            >
              {generateMutation.isPending ? (
                'Generating...'
              ) : (
                <>
                  <FileText className="mr-2 h-5 w-5" />
                  Generate Claim
                </>
              )}
            </Button>

            <Button
              onClick={handleBack}
              variant="outline"
              size="lg"
              className="w-full"
            >
              <ArrowLeft className="mr-2 h-5 w-5" />
              Back to Suggestions
            </Button>

            <Card className="p-4 bg-muted/30">
              <p className="text-sm leading-relaxed text-muted-foreground">
                Your claim will be recorded on the Polygon testnet blockchain for verification
                and audit purposes.
              </p>
            </Card>
          </div>
        </div>
      </div>

      {/* Success Dialog */}
      <Dialog open={!!successData} onOpenChange={() => handleCloseSuccess()}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <div className="flex justify-center mb-4">
              <div className="rounded-full bg-success/10 p-3">
                <CheckCircle className="h-12 w-12 text-success" />
              </div>
            </div>
            <DialogTitle className="text-center text-2xl">Claim Generated!</DialogTitle>
            <DialogDescription className="text-center text-base">
              Your claim has been successfully generated and recorded on the blockchain.
            </DialogDescription>
          </DialogHeader>

          {successData && (
            <div className="space-y-6 py-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-sm text-muted-foreground">Claim ID</span>
                  <span className="font-mono font-semibold">{successData.claim_id}</span>
                </div>

                <div className="flex justify-between items-center py-2 border-b">
                  <span className="text-sm text-muted-foreground">Codes</span>
                  <span className="font-semibold">{successData.approved.length}</span>
                </div>

                {successData.metadata.tx_hash && (
                  <div className="flex justify-between items-center py-2 border-b">
                    <span className="text-sm text-muted-foreground">Blockchain TX</span>
                    <TxBadge
                      txHash={successData.metadata.tx_hash}
                      explorerUrl={successData.metadata.explorer}
                    />
                  </div>
                )}

                {successData.metadata.pdf_url && (
                  <Button
                    asChild
                    variant="outline"
                    className="w-full"
                  >
                    <a
                      href={successData.metadata.pdf_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Download CMS-1500 PDF
                    </a>
                  </Button>
                )}
              </div>

              <Button onClick={handleCloseSuccess} className="w-full" size="lg">
                View All Claims
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* CMS-1500 Detailed Dialog */}
      <CMS1500Dialog
        open={cmsOpen}
        onOpenChange={setCmsOpen}
        approved={approved}
        text={text}
      />
    </div>
  );
}

