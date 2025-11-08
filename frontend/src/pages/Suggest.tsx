import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { PageHeader } from '@/components/PageHeader';
import { EntityChips } from '@/components/EntityChips';
import { SuggestionList } from '@/components/SuggestionList';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ArrowRight, ArrowLeft, Brain } from 'lucide-react';
import { getSuggestions } from '@/lib/api';
import { useClaimStore } from '@/store/claimStore';
import { toast } from 'sonner';

export default function Suggest() {
  const navigate = useNavigate();
  const { text, entities, suggestions, approved, setSuggestions, toggleApproved } = useClaimStore();

  const suggestMutation = useMutation({
    mutationFn: getSuggestions,
    onSuccess: (data) => {
      setSuggestions(data.suggestions);
      toast.success(`Found ${data.suggestions.length} code suggestions`);
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to get suggestions');
    },
  });

  useEffect(() => {
    if (!text) {
      navigate('/upload');
      return;
    }
    
    if (suggestions.length === 0) {
      suggestMutation.mutate({ text, top_k: 10 });
    }
  }, [text]);

  const handleContinue = () => {
    if (approved.length === 0) {
      toast.error('Please select at least one code to continue');
      return;
    }
    navigate('/review');
  };

  const handleBack = () => {
    navigate('/upload');
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-7xl px-4 py-8 space-y-8">
        <PageHeader
          title="AI Suggestions"
          subtitle="Review and select the recommended medical codes"
          step={{ current: 2, total: 3 }}
        />

        {/* Patient Note Summary */}
        <Card className="p-6 bg-accent/30 border-primary/20">
          <div className="space-y-3">
            <div className="flex items-center gap-2 mb-2">
              <Brain className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">Clinical Note Summary</h3>
            </div>
            
            <p className="text-sm text-muted-foreground line-clamp-3">
              {text.slice(0, 200)}...
            </p>
            
            {entities.length > 0 && (
              <div className="pt-2">
                <EntityChips entities={entities} />
              </div>
            )}
          </div>
        </Card>

        {/* Suggestions List */}
        {suggestMutation.isPending ? (
          <Card className="p-12">
            <div className="flex flex-col items-center justify-center gap-4 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
              <p className="text-lg text-muted-foreground">
                Analyzing clinical note with AI...
              </p>
            </div>
          </Card>
        ) : (
          <SuggestionList
            suggestions={suggestions}
            approved={approved}
            onToggle={toggleApproved}
          />
        )}

        {/* Footer Actions */}
        {!suggestMutation.isPending && suggestions.length > 0 && (
          <div className="sticky bottom-0 bg-background border-t py-4 animate-fade-in">
            <div className="flex items-center justify-between gap-4">
              <Button
                onClick={handleBack}
                variant="outline"
                size="lg"
              >
                <ArrowLeft className="mr-2 h-5 w-5" />
                Back to Upload
              </Button>

              <div className="flex items-center gap-3">
                {approved.length > 0 && (
                  <div className="text-sm">
                    <span className="font-semibold text-primary">{approved.length}</span>
                    <span className="text-muted-foreground"> codes selected</span>
                  </div>
                )}
                
                <Button
                  onClick={handleContinue}
                  size="lg"
                  disabled={approved.length === 0}
                >
                  Approve & Continue
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
