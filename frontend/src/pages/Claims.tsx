import { PageHeader } from '@/components/PageHeader';
import { Card } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { TxBadge } from '@/components/TxBadge';
import { FileText, Database } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';

// Mock data for demonstration
const mockClaims = [
  {
    id: 'CLM-2024-001',
    date: '2024-01-15',
    codes_count: 5,
    amount: 1250.00,
    tx_hash: '0x742d35cc6634c0532925a3b844bc9e7fe6e0d3f1b3f3e9c2d0f5a9b5f3e7a9c5',
  },
  {
    id: 'CLM-2024-002',
    date: '2024-01-14',
    codes_count: 3,
    amount: 875.50,
    tx_hash: '0x8a3f57dd7845d0643a36b4c955cd0e8f7f0e4g2c4g4f0d3e1g6b0cg4f8b0d6',
  },
];

export default function Claims() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-7xl px-4 py-8 space-y-8">
        <div className="flex items-center justify-between">
          <PageHeader
            title="Claim History"
            subtitle="View all generated claims and their blockchain records"
          />
          <Button onClick={() => navigate('/upload')}>
            <FileText className="mr-2 h-4 w-4" />
            New Claim
          </Button>
        </div>

        {mockClaims.length === 0 ? (
          <Card className="p-16">
            <div className="flex flex-col items-center justify-center gap-4 text-center">
              <Database className="h-16 w-16 text-muted-foreground" />
              <div>
                <h3 className="text-xl font-semibold mb-2">No claims yet</h3>
                <p className="text-muted-foreground mb-6">
                  Start by uploading a clinical note to generate your first claim
                </p>
                <Button onClick={() => navigate('/upload')}>
                  <FileText className="mr-2 h-4 w-4" />
                  Create New Claim
                </Button>
              </div>
            </div>
          </Card>
        ) : (
          <Card className="animate-fade-in">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Claim ID</TableHead>
                  <TableHead className="text-center">Codes</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Blockchain TX</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mockClaims.map((claim) => (
                  <TableRow key={claim.id} className="cursor-pointer hover:bg-accent/50">
                    <TableCell>
                      {new Date(claim.date).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </TableCell>
                    <TableCell>
                      <span className="font-mono font-semibold">{claim.id}</span>
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant="secondary">{claim.codes_count}</Badge>
                    </TableCell>
                    <TableCell className="text-right font-semibold">
                      ${claim.amount.toFixed(2)}
                    </TableCell>
                    <TableCell>
                      <TxBadge txHash={claim.tx_hash} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        )}
      </div>
    </div>
  );
}
