import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Card } from '@/components/ui/card';
import { Shield } from 'lucide-react';

interface SignatureBlockProps {
  signedBy: string;
  onChange: (signedBy: string) => void;
}

export function SignatureBlock({ signedBy, onChange }: SignatureBlockProps) {
  const [agreed, setAgreed] = useState(false);

  const handleAgreedChange = (checked: boolean) => {
    setAgreed(checked);
    if (!checked) {
      onChange('');
    }
  };

  return (
    <Card className="p-6 animate-fade-in">
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          <h3 className="text-base font-semibold">Signature</h3>
        </div>

        <div className="space-y-3">
          <Label htmlFor="signer-name">Your Name</Label>
          <Input
            id="signer-name"
            type="text"
            value={signedBy}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Enter your full name"
            disabled={!agreed}
            className="text-base"
            aria-label="Enter your name for signature"
          />
        </div>

        <div className="flex items-start gap-3 pt-2">
          <Checkbox
            id="certify"
            checked={agreed}
            onCheckedChange={handleAgreedChange}
            aria-label="I certify this claim is accurate"
          />
          <Label
            htmlFor="certify"
            className="text-sm leading-relaxed cursor-pointer font-normal"
          >
            I certify that this claim is accurate and complete to the best of my knowledge.
            I understand that submission of false information may result in penalties.
          </Label>
        </div>
      </div>
    </Card>
  );
}
