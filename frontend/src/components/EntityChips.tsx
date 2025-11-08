import { Badge } from '@/components/ui/badge';
import type { Entity } from '@/lib/types';

interface EntityChipsProps {
  entities: Entity[];
}

const labelColors: Record<string, string> = {
  DIAGNOSIS: 'bg-primary/10 text-primary border-primary/20',
  PROCEDURE: 'bg-accent-foreground/10 text-accent-foreground border-accent-foreground/20',
};

export function EntityChips({ entities }: EntityChipsProps) {
  if (entities.length === 0) return null;

  const uniqueEntities = Array.from(
    new Map(entities.map((e) => [e.text, e])).values()
  );

  return (
    <div className="flex flex-wrap gap-2 animate-fade-in">
      {uniqueEntities.map((entity, idx) => (
        <Badge
          key={idx}
          variant="outline"
          className={labelColors[entity.label] || 'bg-muted/50 text-muted-foreground'}
        >
          <span className="font-semibold text-xs mr-1.5">{entity.label}</span>
          {entity.text}
        </Badge>
      ))}
    </div>
  );
}
