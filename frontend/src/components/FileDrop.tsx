import { useCallback, useState } from 'react';
import { File, Upload } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface FileDropProps {
  onFileSelect: (file: File) => void;
  accept?: string;
}

export function FileDrop({ onFileSelect, accept = '.pdf,.jpg,.jpeg,.png' }: FileDropProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        const file = files[0];
        setSelectedFile(file);
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        const file = files[0];
        setSelectedFile(file);
        onFileSelect(file);
      }
    },
    [onFileSelect]
  );

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <Card
      className={cn(
        'relative border-2 border-dashed transition-all duration-200 hover:border-primary/50',
        isDragging ? 'border-primary bg-accent/50' : 'border-border',
        'animate-fade-in'
      )}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <label className="flex cursor-pointer flex-col items-center justify-center px-5 py-10 sm:px-8 sm:py-16">
        <input
          type="file"
          className="hidden"
          accept={accept}
          onChange={handleFileInput}
          aria-label="Upload clinical document"
        />

        {selectedFile ? (
          <div className="flex flex-col items-center gap-3 text-center">
            <File className="h-10 w-10 text-primary sm:h-12 sm:w-12" />
            <div>
              <p className="break-all font-semibold text-foreground">{selectedFile.name}</p>
              <p className="mt-1 text-sm text-muted-foreground">
                {selectedFile.type || 'Unknown type'} · {formatFileSize(selectedFile.size)}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 text-center">
            <Upload className="h-10 w-10 text-muted-foreground sm:h-12 sm:w-12" />
            <div>
              <p className="font-semibold text-foreground">Drop a PDF or image</p>
              <p className="mt-1 text-sm text-muted-foreground">Or click to browse files</p>
              <p className="mt-2 text-xs text-muted-foreground">Supports PDF, JPG, PNG</p>
            </div>
          </div>
        )}
      </label>
    </Card>
  );
}
