import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Trash2, Edit2, Check, X, Plus } from 'lucide-react';
import type { CodeSuggestion } from '@/lib/types';

interface ApprovedTableProps {
  approved: CodeSuggestion[];
  onRemove: (code: string) => void;
  onUpdate: (code: string, updates: Partial<CodeSuggestion>) => void;
  onAdd: (suggestion: CodeSuggestion) => void;
}

const systemColors: Record<string, string> = {
  'ICD-10': 'bg-primary text-primary-foreground',
  'CPT': 'bg-accent-foreground text-white',
};

export function ApprovedTable({ approved, onRemove, onUpdate, onAdd }: ApprovedTableProps) {
  const [editingCode, setEditingCode] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [deleteCode, setDeleteCode] = useState<string | null>(null);
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [newCode, setNewCode] = useState({ code: '', system: 'ICD-10', description: '' });

  const startEdit = (code: string, currentDescription: string) => {
    setEditingCode(code);
    setEditValue(currentDescription);
  };

  const saveEdit = (code: string) => {
    onUpdate(code, { description: editValue });
    setEditingCode(null);
    setEditValue('');
  };

  const cancelEdit = () => {
    setEditingCode(null);
    setEditValue('');
  };

  const handleAdd = () => {
    if (newCode.code && newCode.description) {
      onAdd({
        ...newCode,
        score: 0.85,
        reason: 'Manually added code',
      });
      setNewCode({ code: '', system: 'ICD-10', description: '' });
      setIsAddingNew(false);
    }
  };

  if (approved.length === 0 && !isAddingNew) {
    return (
      <div className="text-center py-16 animate-fade-in">
        <p className="text-xl text-muted-foreground mb-4">
          No codes approved yet
        </p>
        <Button onClick={() => setIsAddingNew(true)} variant="outline">
          <Plus className="h-4 w-4 mr-2" />
          Add Manual Code
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Approved Codes ({approved.length})</h3>
        <Button
          onClick={() => setIsAddingNew(true)}
          variant="outline"
          size="sm"
          disabled={isAddingNew}
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Code
        </Button>
      </div>

      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">System</TableHead>
              <TableHead className="w-[140px]">Code</TableHead>
              <TableHead>Description</TableHead>
              <TableHead className="w-[120px]">Confidence</TableHead>
              <TableHead className="w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isAddingNew && (
              <TableRow className="bg-accent/30">
                <TableCell>
                  <select
                    value={newCode.system}
                    onChange={(e) => setNewCode({ ...newCode, system: e.target.value })}
                    className="w-full px-2 py-1 rounded border bg-background"
                  >
                    <option value="ICD-10">ICD-10</option>
                    <option value="CPT">CPT</option>
                  </select>
                </TableCell>
                <TableCell>
                  <Input
                    value={newCode.code}
                    onChange={(e) => setNewCode({ ...newCode, code: e.target.value })}
                    placeholder="Code"
                    className="h-8"
                  />
                </TableCell>
                <TableCell>
                  <Input
                    value={newCode.description}
                    onChange={(e) => setNewCode({ ...newCode, description: e.target.value })}
                    placeholder="Description"
                    className="h-8"
                  />
                </TableCell>
                <TableCell>—</TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    <Button size="icon" variant="ghost" onClick={handleAdd} className="h-8 w-8">
                      <Check className="h-4 w-4" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => {
                        setIsAddingNew(false);
                        setNewCode({ code: '', system: 'ICD-10', description: '' });
                      }}
                      className="h-8 w-8"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            )}
            {approved.map((item) => (
              <TableRow key={item.code}>
                <TableCell>
                  <Badge className={systemColors[item.system] || 'bg-muted'}>
                    {item.system}
                  </Badge>
                </TableCell>
                <TableCell className="font-mono font-semibold">{item.code}</TableCell>
                <TableCell>
                  {editingCode === item.code ? (
                    <Input
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveEdit(item.code);
                        if (e.key === 'Escape') cancelEdit();
                      }}
                      className="h-8"
                      autoFocus
                    />
                  ) : (
                    <span>{item.description}</span>
                  )}
                </TableCell>
                <TableCell>
                  <div className="space-y-1">
                    <span className="text-sm font-semibold">{Math.round(item.score * 100)}%</span>
                    <Progress value={item.score * 100} className="h-1.5" />
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    {editingCode === item.code ? (
                      <>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => saveEdit(item.code)}
                          className="h-8 w-8"
                          aria-label="Save changes"
                        >
                          <Check className="h-4 w-4" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={cancelEdit}
                          className="h-8 w-8"
                          aria-label="Cancel editing"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => startEdit(item.code, item.description)}
                          className="h-8 w-8"
                          aria-label="Edit description"
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => setDeleteCode(item.code)}
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          aria-label="Remove code"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <AlertDialog open={!!deleteCode} onOpenChange={() => setDeleteCode(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove code?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to remove code <strong>{deleteCode}</strong> from the approved list?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deleteCode) onRemove(deleteCode);
                setDeleteCode(null);
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
