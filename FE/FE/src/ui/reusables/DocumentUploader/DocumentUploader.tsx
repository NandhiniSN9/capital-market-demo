import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileUp, X } from 'lucide-react';
import { useDocumentStore } from '@/store/documentStore';
import { toast } from 'sonner';
import { cn } from '@/helpers/utilities/utils';

interface DocumentUploaderProps {
  onClose: () => void;
}

export function DocumentUploader({ onClose }: DocumentUploaderProps) {
  const addDocument = useDocumentStore((s) => s.addDocument);
  const updateDocumentStatus = useDocumentStore((s) => s.updateDocumentStatus);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      acceptedFiles.forEach((file) => {
        const id = `doc-upload-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
        const subType = detectDocumentType(file.name);

        // Add as processing
        addDocument({
          id,
          name: file.name.replace(/\.[^/.]+$/, ''),
          shortName: subType,
          type: detectCategory(subType),
          subType,
          company: 'Uploaded',
          period: new Date().getFullYear().toString(),
          pageCount: Math.floor(Math.random() * 50) + 10,
          uploadDate: new Date().toISOString().split('T')[0],
          status: 'processing',
          sections: [],
        });

        toast.info(`Processing ${file.name}...`);

        // Simulate processing
        setTimeout(() => {
          updateDocumentStatus(id, 'ready');
          toast.success(`${file.name} is ready`);
        }, 2000);
      });
      onClose();
    },
    [addDocument, updateDocumentStatus, onClose]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/plain': ['.txt'],
    },
  });

  return (
    <div className="relative">
      <button
        onClick={onClose}
        className="absolute -top-1 -right-1 rounded-full p-0.5 text-slate-500 hover:text-slate-300 hover:bg-slate-700 z-10"
      >
        <X className="h-3 w-3" />
      </button>
      <div
        {...getRootProps()}
        className={cn(
          'flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 cursor-pointer transition-all',
          isDragActive
            ? 'border-sky-400 bg-sky-500/5'
            : 'border-slate-700 bg-slate-900/30 hover:border-slate-600 hover:bg-slate-900/50'
        )}
      >
        <input {...getInputProps()} />
        <FileUp className={cn('h-6 w-6 mb-2', isDragActive ? 'text-sky-400' : 'text-slate-600')} />
        <p className="text-xs text-slate-400">
          {isDragActive ? 'Drop files here' : 'Drag & drop files or click to browse'}
        </p>
        <p className="mt-1 text-[10px] text-slate-600">PDF, DOCX, XLSX, TXT</p>
      </div>
    </div>
  );
}

function detectDocumentType(filename: string): string {
  const lower = filename.toLowerCase();
  if (lower.includes('10-k') || lower.includes('10k')) return '10-K';
  if (lower.includes('10-q') || lower.includes('10q')) return '10-Q';
  if (lower.includes('8-k') || lower.includes('8k')) return '8-K';
  if (lower.includes('earning') || lower.includes('transcript')) return 'Earnings Transcript';
  if (lower.includes('credit') || lower.includes('agreement')) return 'Credit Agreement';
  if (lower.includes('presentation') || lower.includes('deck')) return 'Presentation';
  if (lower.includes('press') || lower.includes('release')) return 'Press Release';
  return 'Document';
}

function detectCategory(subType: string): 'financial' | 'legal' | 'operational' | 'market' {
  if (['10-K', '10-Q', '8-K'].includes(subType)) return 'financial';
  if (['Credit Agreement'].includes(subType)) return 'legal';
  if (['Presentation'].includes(subType)) return 'operational';
  return 'market';
}
