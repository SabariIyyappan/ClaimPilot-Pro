import { useState, useMemo } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { SuggestionCard } from './SuggestionCard';
import type { CodeSuggestion } from '@/lib/types';

interface SuggestionListProps {
  suggestions: CodeSuggestion[];
  approved: CodeSuggestion[];
  onToggle: (suggestion: CodeSuggestion) => void;
}

export function SuggestionList({ suggestions, approved, onToggle }: SuggestionListProps) {
  const [activeTab, setActiveTab] = useState('all');

  const filteredSuggestions = useMemo(() => {
    if (activeTab === 'all') return suggestions;
    return suggestions.filter((s) => s.system === activeTab);
  }, [suggestions, activeTab]);

  const isSelected = (suggestion: CodeSuggestion) =>
    approved.some((a) => a.code === suggestion.code);

  const counts = useMemo(() => {
    return {
      all: suggestions.length,
      'ICD-10': suggestions.filter((s) => s.system === 'ICD-10').length,
      CPT: suggestions.filter((s) => s.system === 'CPT').length,
    };
  }, [suggestions]);

  if (suggestions.length === 0) {
    return (
      <div className="text-center py-16 animate-fade-in">
        <p className="text-xl text-muted-foreground mb-2">
          No suggestions found
        </p>
        <p className="text-base text-muted-foreground">
          Try editing your note or add a code manually in the next step
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="all">All ({counts.all})</TabsTrigger>
          <TabsTrigger value="ICD-10">ICD-10 ({counts['ICD-10']})</TabsTrigger>
          <TabsTrigger value="CPT">CPT ({counts.CPT})</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-6 space-y-4">
          {filteredSuggestions.map((suggestion) => (
            <SuggestionCard
              key={suggestion.code}
              suggestion={suggestion}
              isSelected={isSelected(suggestion)}
              onToggle={onToggle}
            />
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
}
