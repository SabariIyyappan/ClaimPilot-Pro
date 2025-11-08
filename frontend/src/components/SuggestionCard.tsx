import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { HelpCircle } from 'lucide-react';
import type { CodeSuggestion } from '@/lib/types';
import { cn } from '@/lib/utils';

interface SuggestionCardProps {
  suggestion: CodeSuggestion;
  isSelected: boolean;
  onToggle: (suggestion: CodeSuggestion) => void;
}

const systemColors: Record<string, string> = {
  'ICD-10': 'bg-primary text-primary-foreground',
  'CPT': 'bg-accent-foreground text-white',
};

export function SuggestionCard({ suggestion, isSelected, onToggle }: SuggestionCardProps) {
  const confidencePercent = Math.round(suggestion.score * 100);
  
  return (
    <Card
      className={cn(
        'p-4 transition-all duration-200 cursor-pointer hover:shadow-md animate-scale-in',
        isSelected ? 'ring-2 ring-primary bg-accent/30' : ''
      )}
      onClick={() => onToggle(suggestion)}
    >
      <div className="flex items-start gap-3">
        <Checkbox
          checked={isSelected}
          onCheckedChange={() => onToggle(suggestion)}
          className="mt-1"
          aria-label={`Select code ${suggestion.code}`}
        />
        
        <div className="flex-1 space-y-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Badge className={systemColors[suggestion.system] || 'bg-muted'}>
                  {suggestion.system}
                </Badge>
                <span className="font-mono font-semibold text-lg">
                  {suggestion.code}
                </span>
              </div>
              <p className="text-base leading-relaxed">{suggestion.description}</p>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm text-muted-foreground">Confidence</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold">{confidencePercent}%</span>
                <Popover>
                  <PopoverTrigger asChild>
                    <button
                      className="text-muted-foreground hover:text-foreground transition-colors"
                      aria-label="Why was this suggested?"
                    >
                      <HelpCircle className="h-4 w-4" />
                    </button>
                  </PopoverTrigger>
                  <PopoverContent className="w-80" align="end">
                    <div className="space-y-2">
                      <h4 className="font-semibold text-sm">Why this code?</h4>
                      <p className="text-sm leading-relaxed text-muted-foreground">
                        {suggestion.reason}
                      </p>
                    </div>
                  </PopoverContent>
                </Popover>
              </div>
            </div>
            <Progress
              value={confidencePercent}
              className="h-2"
              aria-label={`${confidencePercent}% confidence`}
            />
          </div>
        </div>
      </div>
    </Card>
  );
}
