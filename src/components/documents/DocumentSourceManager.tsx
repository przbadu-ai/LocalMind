import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  FolderIcon,
  FileIcon,
  XIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  CheckIcon,
  RefreshCwIcon,
  LoaderIcon,
  FileTextIcon,
  ImageIcon,
  FileCodeIcon,
  FolderOpenIcon
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { FileService, FileSystemItem } from '@/services/file-service';
import { cn } from '@/lib/utils';

interface DocumentSourceManagerProps {
  onSourcesChange?: (sources: FileSystemItem[]) => void;
}

export function DocumentSourceManager({ onSourcesChange }: DocumentSourceManagerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [fileSystemItems, setFileSystemItems] = useState<FileSystemItem[]>([]);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [selectedCount, setSelectedCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedRootPath, setSelectedRootPath] = useState<string>('');
  const [stats, setStats] = useState({
    selectedFiles: 0,
    selectedFolders: 0,
    totalFiles: 0
  });

  // Update stats when items change
  useEffect(() => {
    const statistics = FileService.getSelectionStats(fileSystemItems);
    setStats({
      selectedFiles: statistics.selectedFiles,
      selectedFolders: statistics.selectedFolders,
      totalFiles: statistics.totalFiles
    });
    setSelectedCount(statistics.selectedFiles);
  }, [fileSystemItems]);

  // Notify parent of changes only when selection actually changes
  useEffect(() => {
    if (onSourcesChange) {
      const selectedPaths = FileService.getSelectedPaths(fileSystemItems);
      const selectedItems = fileSystemItems.filter(item =>
        selectedPaths.includes(item.path)
      );
      // Only call if there's actually a change
      if (selectedItems.length !== selectedCount || selectedCount > 0) {
        onSourcesChange(selectedItems);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCount, fileSystemItems.length]); // Depend on counts, not the callback

  const handleToggleFolder = (folderId: string) => {
    setExpandedFolders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(folderId)) {
        newSet.delete(folderId);
      } else {
        newSet.add(folderId);
      }
      return newSet;
    });
  };

  const handleSelectItem = (itemId: string, checked: boolean) => {
    const updatedItems = FileService.updateSelection(
      fileSystemItems,
      itemId,
      checked,
      true // Select children when selecting a folder
    );
    setFileSystemItems(updatedItems);
  };

  const handleSelectAll = () => {
    const updatedItems = FileService.selectAll(fileSystemItems, true);
    setFileSystemItems(updatedItems);
  };

  const handleClearAll = () => {
    const updatedItems = FileService.selectAll(fileSystemItems, false);
    setFileSystemItems(updatedItems);
  };

  const handleConnectFolder = async () => {
    setIsLoading(true);
    try {
      const folderPath = await FileService.selectFolder();

      if (folderPath) {
        setSelectedRootPath(folderPath);

        // Read the directory contents
        const items = await FileService.readDirectory(folderPath, true, 3);
        setFileSystemItems(items);

        // Auto-expand first level folders
        const firstLevelFolders = items
          .filter(item => item.type === 'folder')
          .map(item => item.id);
        setExpandedFolders(new Set(firstLevelFolders));
      }
    } catch (error) {
      console.error('Error connecting folder:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConnectFiles = async () => {
    setIsLoading(true);
    try {
      const filePaths = await FileService.selectFiles();

      if (filePaths && filePaths.length > 0) {
        // Convert file paths to FileSystemItems
        const items: FileSystemItem[] = filePaths.map((path, index) => {
          const name = path.split('/').pop() || path;
          return {
            id: `file_${index}`,
            name,
            path,
            type: 'file',
            selected: true,
            extension: name.includes('.') ? `.${name.split('.').pop()}` : undefined
          };
        });

        setFileSystemItems(prev => [...prev, ...items]);
      }
    } catch (error) {
      console.error('Error connecting files:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (selectedRootPath) {
      setIsLoading(true);
      try {
        const items = await FileService.readDirectory(selectedRootPath, true, 3);
        setFileSystemItems(items);
      } catch (error) {
        console.error('Error refreshing:', error);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const getFileIcon = (item: FileSystemItem) => {
    if (item.type === 'folder') {
      return <FolderIcon className="h-4 w-4 text-yellow-500" />;
    }

    const ext = item.extension?.toLowerCase();
    if (['.png', '.jpg', '.jpeg'].includes(ext || '')) {
      return <ImageIcon className="h-4 w-4 text-green-500" />;
    }
    if (['.md', '.txt'].includes(ext || '')) {
      return <FileTextIcon className="h-4 w-4 text-blue-500" />;
    }
    if (['.js', '.ts', '.tsx', '.jsx'].includes(ext || '')) {
      return <FileCodeIcon className="h-4 w-4 text-purple-500" />;
    }
    return <FileIcon className="h-4 w-4 text-gray-500" />;
  };

  const renderFileTree = (items: FileSystemItem[], depth: number = 0) => {
    return items.map(item => (
      <div key={item.id} className="select-none">
        <div
          className={cn(
            "flex items-center gap-2 py-1.5 hover:bg-secondary/50 rounded px-2 cursor-pointer",
            depth > 0 && "ml-4"
          )}
        >
          {item.type === 'folder' && (
            <Button
              variant="ghost"
              size="icon"
              className="h-5 w-5 p-0"
              onClick={(e) => {
                e.stopPropagation();
                handleToggleFolder(item.id);
              }}
            >
              {expandedFolders.has(item.id) ? (
                <ChevronDownIcon className="h-3 w-3" />
              ) : (
                <ChevronRightIcon className="h-3 w-3" />
              )}
            </Button>
          )}
          {item.type === 'file' && <div className="w-5" />}

          <Checkbox
            checked={item.selected}
            onCheckedChange={(checked) => handleSelectItem(item.id, checked as boolean)}
            onClick={(e) => e.stopPropagation()}
          />

          {getFileIcon(item)}

          <span className="text-sm flex-1 truncate">{item.name}</span>

          {item.fileCount !== undefined && item.fileCount > 0 && (
            <Badge variant="secondary" className="text-xs">
              {item.fileCount} files
            </Badge>
          )}
        </div>

        {item.type === 'folder' && item.children && expandedFolders.has(item.id) && (
          <div>{renderFileTree(item.children, depth + 1)}</div>
        )}
      </div>
    ));
  };

  return (
    <>
      <Button
        onClick={() => setIsOpen(true)}
        variant="outline"
        className="gap-2 bg-secondary/50"
      >
        <FolderIcon className="h-4 w-4" />
        + Sources
        {selectedCount > 0 && (
          <Badge variant="secondary" className="ml-2">
            {selectedCount} files
          </Badge>
        )}
      </Button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-3xl h-[600px] p-0 bg-background/95 backdrop-blur">
          <div className="flex flex-col h-full">
            <DialogHeader className="px-6 py-4 border-b">
              <div className="flex items-center justify-between">
                <div>
                  <DialogTitle className="text-lg font-semibold">
                    Connect Sources
                  </DialogTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    100% local processing
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setIsOpen(false)}
                >
                  <XIcon className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                File Types Supported: Plain text (.txt), Markdown (.md), Word (.docx), PDF (.pdf), PowerPoint (.pptx), and images (.png, .jpg, .jpeg)
              </p>
            </DialogHeader>

            <div className="flex-1 px-6 py-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <FolderOpenIcon className="h-5 w-5 text-yellow-500" />
                  <span className="font-medium">
                    {selectedRootPath ?
                      selectedRootPath.split('/').pop() || 'Local Folder' :
                      'Local Folder'}
                  </span>
                  {selectedRootPath && (
                    <span className="text-xs text-muted-foreground">
                      {selectedRootPath}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleConnectFolder}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <LoaderIcon className="h-3 w-3 mr-1 animate-spin" />
                    ) : (
                      <FolderIcon className="h-3 w-3 mr-1" />
                    )}
                    Connect folder
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleConnectFiles}
                    disabled={isLoading}
                  >
                    <FileIcon className="h-3 w-3 mr-1" />
                    Connect files
                  </Button>
                  {fileSystemItems.length > 0 && (
                    <>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleRefresh}
                        disabled={isLoading}
                      >
                        <RefreshCwIcon className="h-3 w-3" />
                      </Button>
                      <div className="ml-2 h-4 w-px bg-border" />
                      <div className="ml-2 flex items-center gap-2 text-sm">
                        <span className="text-muted-foreground">
                          {stats.selectedFiles} selected
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleSelectAll}
                        >
                          Select all
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleClearAll}
                        >
                          Clear
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              </div>

              <ScrollArea className="h-[350px] border rounded-lg">
                {fileSystemItems.length > 0 ? (
                  <div className="p-4">
                    {renderFileTree(fileSystemItems)}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-center p-8">
                    <FolderOpenIcon className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-sm text-muted-foreground mb-2">
                      No folder selected
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Click "Connect folder" to browse and select files to index
                    </p>
                  </div>
                )}
              </ScrollArea>

              {fileSystemItems.length > 0 && (
                <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    {stats.totalFiles} files found • {stats.selectedFiles} files selected • {stats.selectedFolders} folders selected
                  </span>
                </div>
              )}
            </div>

            <div className="px-6 py-4 border-t flex items-center justify-between">
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <CheckIcon className="h-3 w-3" />
                Local Mind tracks file changes. All processing stays on this device.
              </p>
              {fileSystemItems.length > 0 && (
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <RefreshCwIcon className="h-3 w-3" />
                  Last synced: {new Date().toLocaleTimeString()}
                </p>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}