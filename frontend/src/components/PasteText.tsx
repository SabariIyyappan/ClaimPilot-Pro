import { useState } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';

interface PasteTextProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function PasteText({
  value,
  onChange,
  placeholder = 'Paste clinical note text here...',
}: PasteTextProps) {
  const [charCount, setCharCount] = useState(value.length);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
    setCharCount(newValue.length);
  };

  return (
    <div className="space-y-2 animate-fade-in">
      <div className="flex items-center justify-between">
        <Label htmlFor="clinical-text">Or paste clinical note text</Label>
        <span className="text-sm text-muted-foreground">{charCount} characters</span>
      </div>
      <Textarea
        id="clinical-text"
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        className="min-h-[300px] font-mono text-base resize-y"
        aria-label="Clinical note text input"
      />
    </div>
  );
}
