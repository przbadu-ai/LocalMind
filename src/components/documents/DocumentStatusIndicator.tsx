import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  FileIcon,
  FolderIcon,
  RefreshCwIcon,
  CheckCircleIcon,
  AlertCircleIcon,
  LoaderIcon
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface DocumentStatus {
  total: number;
  processed: number;
  indexing: boolean;
  error?: string;
  lastSync?: Date;
}

interface DocumentStatusIndicatorProps {
  status: DocumentStatus;
  className?: string;
  compact?: boolean;
}

export function DocumentStatusIndicator({
  status,
  className,
  compact = false
}: DocumentStatusIndicatorProps) {
  const percentage = status.total > 0 ? (status.processed / status.total) * 100 : 0;

  if (compact) {
    return (
      <div className={cn("flex items-center gap-2", className)}>
        {status.indexing ? (
          <LoaderIcon className="h-4 w-4 animate-spin text-primary" />
        ) : status.error ? (
          <AlertCircleIcon className="h-4 w-4 text-destructive" />
        ) : (
          <CheckCircleIcon className="h-4 w-4 text-green-500" />
        )}
        <Badge variant="secondary" className="text-xs">
          {status.processed}/{status.total} files
        </Badge>
      </div>
    );
  }

  return (
    <div className={cn("space-y-3 p-4 bg-secondary/30 rounded-lg", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FolderIcon className="h-5 w-5 text-yellow-500" />
          <span className="font-medium text-sm">Local Folder</span>
        </div>
        <Badge variant="secondary">
          {status.processed}/{status.total} files
        </Badge>
      </div>

      {status.indexing && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Processing documents...</span>
            <span className="font-mono">{percentage.toFixed(0)}%</span>
          </div>
          <Progress value={percentage} className="h-2" />
        </div>
      )}

      {status.error && (
        <div className="flex items-center gap-2 text-sm text-destructive">
          <AlertCircleIcon className="h-4 w-4" />
          <span>{status.error}</span>
        </div>
      )}

      {!status.indexing && !status.error && status.processed > 0 && (
        <div className="flex items-center gap-2 text-sm text-green-600">
          <CheckCircleIcon className="h-4 w-4" />
          <span>All documents indexed successfully</span>
        </div>
      )}

      {status.lastSync && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <RefreshCwIcon className="h-3 w-3" />
          <span>Last synced: {status.lastSync.toLocaleString()}</span>
        </div>
      )}
    </div>
  );
}