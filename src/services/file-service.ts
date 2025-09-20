import { open } from '@tauri-apps/plugin-dialog';
import { readDir } from '@tauri-apps/plugin-fs';

interface DirEntry {
  name: string;
  isDirectory: boolean;
  isFile: boolean;
  isSymlink: boolean;
}

export interface FileSystemItem {
  id: string;
  name: string;
  path: string;
  type: 'file' | 'folder';
  size?: number;
  children?: FileSystemItem[];
  selected: boolean;
  fileCount?: number;
  extension?: string;
}

export class FileService {
  private static supportedExtensions = [
    '.pdf', '.txt', '.md', '.docx', '.pptx',
    '.png', '.jpg', '.jpeg'
  ];

  /**
   * Open native folder picker dialog
   */
  static async selectFolder(): Promise<string | null> {
    try {
      if (!open) {
        console.warn('Dialog API not available');
        return null;
      }

      const selected = await open({
        directory: true,
        multiple: false,
        title: 'Select Folder to Index'
      });

      return selected as string | null;
    } catch (error) {
      console.error('Error selecting folder:', error);
      return null;
    }
  }

  /**
   * Open native file picker dialog
   */
  static async selectFiles(): Promise<string[] | null> {
    try {
      if (!open) {
        console.warn('Dialog API not available');
        return null;
      }

      const selected = await open({
        directory: false,
        multiple: true,
        title: 'Select Files to Index',
        filters: [
          {
            name: 'Documents',
            extensions: ['pdf', 'txt', 'md', 'docx', 'pptx']
          },
          {
            name: 'Images',
            extensions: ['png', 'jpg', 'jpeg']
          },
          {
            name: 'All Files',
            extensions: ['*']
          }
        ]
      });

      return selected as string[] | null;
    } catch (error) {
      console.error('Error selecting files:', error);
      return null;
    }
  }

  /**
   * Read directory contents recursively
   */
  static async readDirectory(
    dirPath: string,
    recursive: boolean = false,
    maxDepth: number = 3
  ): Promise<FileSystemItem[]> {
    try {
      if (!readDir) {
        console.warn('File system API not available');
        return [];
      }

      const entries = await readDir(dirPath);
      return this.processEntries(entries, dirPath, 0, maxDepth, recursive);
    } catch (error) {
      console.error('Error reading directory:', error);
      return [];
    }
  }

  /**
   * Process file entries into structured items
   */
  private static async processEntries(
    entries: DirEntry[],
    basePath: string,
    currentDepth: number,
    maxDepth: number,
    recursive: boolean = false
  ): Promise<FileSystemItem[]> {
    const items: FileSystemItem[] = [];

    for (const entry of entries) {
      const item: FileSystemItem = {
        id: `${basePath}/${entry.name}`,
        name: entry.name || '',
        path: `${basePath}/${entry.name}`,
        type: entry.isDirectory ? 'folder' : 'file',
        selected: false
      };

      // Add file extension for files
      if (!entry.isDirectory && entry.name) {
        const ext = this.getFileExtension(entry.name);
        if (ext) {
          item.extension = ext;
        }
      }

      // Process children if it's a folder and within depth limit
      if (entry.isDirectory && recursive && currentDepth < maxDepth) {
        try {
          const childPath = `${basePath}/${entry.name}`;
          const children = await readDir(childPath);
          item.children = await this.processEntries(
            children,
            childPath,
            currentDepth + 1,
            maxDepth,
            recursive
          );
          item.fileCount = this.countFiles(item.children);
        } catch (error) {
          console.error(`Error reading subdirectory ${entry.name}:`, error);
          item.fileCount = 0;
        }
      }

      items.push(item);
    }

    return items;
  }

  /**
   * Count total files in a tree structure
   */
  private static countFiles(items: FileSystemItem[]): number {
    let count = 0;

    for (const item of items) {
      if (item.type === 'file' && this.isSupportedFile(item.name)) {
        count++;
      } else if (item.children) {
        count += this.countFiles(item.children);
      }
    }

    return count;
  }

  /**
   * Check if file is supported
   */
  static isSupportedFile(fileName: string): boolean {
    const ext = this.getFileExtension(fileName);
    return ext ? this.supportedExtensions.includes(ext.toLowerCase()) : false;
  }

  /**
   * Get file extension
   */
  private static getFileExtension(fileName: string): string | null {
    const lastDot = fileName.lastIndexOf('.');
    return lastDot !== -1 ? fileName.substring(lastDot) : null;
  }

  /**
   * Get selected files from the tree structure
   */
  static getSelectedPaths(items: FileSystemItem[]): string[] {
    const paths: string[] = [];

    const traverse = (items: FileSystemItem[]) => {
      for (const item of items) {
        if (item.selected) {
          paths.push(item.path);
        }
        if (item.children) {
          traverse(item.children);
        }
      }
    };

    traverse(items);
    return paths;
  }

  /**
   * Update selection state in tree
   */
  static updateSelection(
    items: FileSystemItem[],
    itemId: string,
    selected: boolean,
    selectChildren: boolean = true
  ): FileSystemItem[] {
    return items.map(item => {
      if (item.id === itemId) {
        // Update this item and optionally its children
        const updatedItem = { ...item, selected };
        if (selectChildren && item.children) {
          updatedItem.children = this.selectAll(item.children, selected);
        }
        return updatedItem;
      } else if (item.children) {
        // Recursively update children
        return {
          ...item,
          children: this.updateSelection(item.children, itemId, selected, selectChildren)
        };
      }
      return item;
    });
  }

  /**
   * Select/deselect all items
   */
  static selectAll(items: FileSystemItem[], selected: boolean): FileSystemItem[] {
    return items.map(item => ({
      ...item,
      selected,
      children: item.children ? this.selectAll(item.children, selected) : undefined
    }));
  }

  /**
   * Get statistics about selected files
   */
  static getSelectionStats(items: FileSystemItem[]): {
    totalFiles: number;
    totalFolders: number;
    selectedFiles: number;
    selectedFolders: number;
    fileTypes: Record<string, number>;
  } {
    const stats = {
      totalFiles: 0,
      totalFolders: 0,
      selectedFiles: 0,
      selectedFolders: 0,
      fileTypes: {} as Record<string, number>
    };

    const traverse = (items: FileSystemItem[]) => {
      for (const item of items) {
        if (item.type === 'file') {
          stats.totalFiles++;
          if (item.selected) {
            stats.selectedFiles++;
          }
          if (item.extension) {
            stats.fileTypes[item.extension] = (stats.fileTypes[item.extension] || 0) + 1;
          }
        } else {
          stats.totalFolders++;
          if (item.selected) {
            stats.selectedFolders++;
          }
        }

        if (item.children) {
          traverse(item.children);
        }
      }
    };

    traverse(items);
    return stats;
  }
}