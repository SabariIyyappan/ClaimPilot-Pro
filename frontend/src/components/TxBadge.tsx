import { Badge } from '@/components/ui/badge';
import { ExternalLink } from 'lucide-react';

interface TxBadgeProps {
  txHash: string;
  explorerUrl?: string;
}

export function TxBadge({ txHash, explorerUrl }: TxBadgeProps) {
  const shortHash = `${txHash.slice(0, 6)}...${txHash.slice(-4)}`;
  const href = explorerUrl || `https://mumbai.polygonscan.com/tx/${txHash}`;

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1.5 transition-colors hover:opacity-80"
    >
      <Badge variant="outline" className="bg-success/10 text-success border-success/20 font-mono">
        {shortHash}
      </Badge>
      <ExternalLink className="h-3.5 w-3.5 text-success" />
    </a>
  );
}
