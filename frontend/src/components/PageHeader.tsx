import { ChevronRight } from 'lucide-react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  step?: { current: number; total: number };
}

export function PageHeader({ title, subtitle, step }: PageHeaderProps) {
  return (
    <div className="space-y-2 animate-fade-in">
      {step && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>Step {step.current} of {step.total}</span>
          <ChevronRight className="h-4 w-4" />
          <span className="text-foreground font-medium">{title}</span>
        </div>
      )}
      <div>
        <h1 className="mb-2">{title}</h1>
        {subtitle && <p className="text-lg text-muted-foreground">{subtitle}</p>}
      </div>
    </div>
  );
}
