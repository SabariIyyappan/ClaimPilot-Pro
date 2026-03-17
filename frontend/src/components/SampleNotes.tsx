import { ExternalLink, FlaskConical } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { SAMPLE_NOTES, type SampleNote } from '@/lib/sampleNotes';

interface SampleNotesProps {
  onSelect: (sample: SampleNote) => void;
}

const SAMPLE_REPORTS_URL = import.meta.env.VITE_SAMPLE_REPORTS_URL || '';

export function SampleNotes({ onSelect }: SampleNotesProps) {
  return (
    <Card className="border-primary/15 bg-accent/20 p-4 sm:p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <FlaskConical className="h-4 w-4 text-primary" />
            <h3 className="font-semibold">Sample Documents</h3>
          </div>
          <p className="text-sm text-muted-foreground">
            Load an anonymous sample note instantly, or open the shared folder with sample report PDFs.
          </p>
        </div>
        {SAMPLE_REPORTS_URL ? (
          <Button asChild variant="outline" size="sm" className="w-full shrink-0 sm:w-auto">
            <a href={SAMPLE_REPORTS_URL} target="_blank" rel="noreferrer">
              Sample PDFs
              <ExternalLink className="ml-2 h-4 w-4" />
            </a>
          </Button>
        ) : null}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {SAMPLE_NOTES.map((sample) => (
          <button
            key={sample.id}
            type="button"
            onClick={() => onSelect(sample)}
            className="rounded-lg border border-border bg-background/70 p-3 text-left transition hover:border-primary/50 hover:bg-background sm:p-4"
          >
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between sm:gap-3">
              <p className="font-medium leading-tight">{sample.title}</p>
              <span className="w-fit rounded-full bg-primary/10 px-2 py-1 text-xs font-medium text-primary">
                {sample.specialty}
              </span>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">{sample.summary}</p>
          </button>
        ))}
      </div>
    </Card>
  );
}
