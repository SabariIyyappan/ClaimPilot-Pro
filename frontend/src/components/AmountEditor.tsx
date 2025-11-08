import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { DollarSign } from 'lucide-react';

interface AmountEditorProps {
  amount: number;
  onChange: (amount: number) => void;
}

export function AmountEditor({ amount, onChange }: AmountEditorProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value) || 0;
    if (value >= 0) {
      onChange(value);
    }
  };

  return (
    <Card className="p-6 animate-fade-in">
      <div className="space-y-3">
        <Label htmlFor="claim-amount" className="text-base font-semibold">
          Claim Amount
        </Label>
        <div className="relative">
          <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          <Input
            id="claim-amount"
            type="number"
            min="0"
            step="0.01"
            value={amount || ''}
            onChange={handleChange}
            placeholder="0.00"
            className="pl-10 text-lg font-semibold h-12"
            aria-label="Enter claim amount in dollars"
          />
        </div>
        <p className="text-sm text-muted-foreground">
          Enter the total billable amount for this claim
        </p>
      </div>
    </Card>
  );
}
