import { useState, useMemo, useEffect, memo, createContext, useContext } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight, oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ChevronDown, ChevronRight, Brain, Copy, Check, Eye } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const PreviewContext = createContext<(code: string) => void>(() => { });

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

interface ReasoningBlockProps {
  content: string;
  defaultOpen?: boolean;
}

const ReasoningBlock = memo(({ content, defaultOpen = false }: ReasoningBlockProps) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="my-3 border border-border/50 rounded-lg overflow-hidden bg-muted/30">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-2 px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted/50 transition-colors"
      >
        {isOpen ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
        <Brain className="h-4 w-4" />
        <span>Reasoning</span>
        {!isOpen && (
          <span className="text-xs text-muted-foreground/60 ml-2">
            (click to expand)
          </span>
        )}
      </button>
      {isOpen && (
        <div className="px-4 py-3 border-t border-border/50 text-sm text-muted-foreground bg-muted/20">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={markdownComponents}
          >
            {content}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
});

// CodeBlock component with syntax highlighting, line numbers, and copy button
interface CodeBlockProps {
  children?: React.ReactNode;
  className?: string;
  inline?: boolean;
}

const CodeBlock = memo(({ children, className, inline }: CodeBlockProps) => {
  const [copied, setCopied] = useState(false);
  const setPreviewCode = useContext(PreviewContext);
  const [isDark, setIsDark] = useState(() =>
    typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
  );

  // Check for dark mode changes
  useEffect(() => {
    const checkDark = () => setIsDark(document.documentElement.classList.contains('dark'));
    checkDark();
    const observer = new MutationObserver(checkDark);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  // Extract language from className (e.g., "language-typescript" -> "typescript")
  const match = /language-(\w+)/.exec(className || '');
  const language = match ? match[1] : '';

  // Get code string
  const codeString = String(children).replace(/\n$/, '');

  // Inline code
  if (inline || !language) {
    return (
      <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs">
        {children}
      </code>
    );
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(codeString);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  const isHtml = language.toLowerCase() === 'html' || language.toLowerCase() === 'xml';

  return (
    <div className="code-block group my-4 rounded-lg overflow-hidden border border-border">
      {/* Header with language badge and copy button */}
      <div className="flex items-center justify-between px-4 py-2 bg-muted/50 border-b border-border">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {language}
        </span>
        <div className="flex items-center gap-3">
          {isHtml && (
            <button
              onClick={() => setPreviewCode(codeString)}
              className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
              title="Preview HTML"
            >
              <Eye className="h-3.5 w-3.5" />
              <span>Preview</span>
            </button>
          )}
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-green-500" />
                <span className="text-green-500">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Code with syntax highlighting */}
      <SyntaxHighlighter
        style={isDark ? oneDark : oneLight}
        language={language}
        showLineNumbers={true}
        customStyle={{
          margin: 0,
          borderRadius: 0,
          fontSize: '0.75rem',
          lineHeight: '1.5',
          overflowX: 'auto',
          maxHeight: '800px',
          overflowY: 'auto',
        }}
        lineNumberStyle={{
          minWidth: '2.5em',
          paddingRight: '1em',
          color: isDark ? '#6e7681' : '#8b949e',
          borderRight: '1px solid',
          borderColor: isDark ? '#30363d' : '#d0d7de',
          marginRight: '1em',
        }}
      >
        {codeString}
      </SyntaxHighlighter>
    </div>
  );
});

// Shared markdown components
const markdownComponents = {
  p: ({ children }: any) => (
    <p className="text-sm leading-relaxed mb-3 last:mb-0">{children}</p>
  ),
  a: ({ href, children }: any) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-primary hover:underline"
    >
      {children}
    </a>
  ),
  ul: ({ children }: any) => (
    <ul className="list-disc pl-5 space-y-1 my-3">{children}</ul>
  ),
  ol: ({ children }: any) => (
    <ol className="list-decimal pl-5 space-y-1 my-3">{children}</ol>
  ),
  li: ({ children }: any) => (
    <li className="text-sm">{children}</li>
  ),
  blockquote: ({ children }: any) => (
    <blockquote className="border-l-4 border-muted-foreground/30 pl-4 italic my-3">
      {children}
    </blockquote>
  ),
  code: ({ children, className, inline }: any) => (
    <CodeBlock className={className} inline={inline}>
      {children}
    </CodeBlock>
  ),
  // Let CodeBlock handle the pre wrapper for block code
  pre: ({ children }: any) => <>{children}</>,
  h1: ({ children }: any) => (
    <h1 className="text-xl font-bold mb-3 mt-4">{children}</h1>
  ),
  h2: ({ children }: any) => (
    <h2 className="text-lg font-semibold mb-2 mt-3">{children}</h2>
  ),
  h3: ({ children }: any) => (
    <h3 className="text-base font-medium mb-2 mt-2">{children}</h3>
  ),
  hr: () => <hr className="my-4 border-border" />,
  table: ({ children }: any) => (
    <div className="overflow-x-auto my-3">
      <table className="min-w-full divide-y divide-border">
        {children}
      </table>
    </div>
  ),
  thead: ({ children }: any) => (
    <thead className="bg-muted/50">{children}</thead>
  ),
  tbody: ({ children }: any) => (
    <tbody className="divide-y divide-border">{children}</tbody>
  ),
  tr: ({ children }: any) => <tr>{children}</tr>,
  th: ({ children }: any) => (
    <th className="px-3 py-2 text-left text-xs font-medium uppercase tracking-wider">
      {children}
    </th>
  ),
  td: ({ children }: any) => (
    <td className="px-3 py-2 text-sm">{children}</td>
  ),
};

// Patterns to detect reasoning/thinking blocks
// Based on Jan AI's implementation: https://github.com/janhq/jan/blob/main/web-app/src/containers/ThreadContent.tsx
// Uses capturing groups to extract content between tags, supports multiline with [\s\S]*?
// qwen3 models use <think>...</think> tags for reasoning output
const REASONING_REGEX_PATTERNS = [
  // <think>...</think> tags (qwen3 and other reasoning models)
  /<think>([\s\S]*?)<\/think>/gi,
  // <thinking>...</thinking> tags
  /<thinking>([\s\S]*?)<\/thinking>/gi,
  // <reasoning>...</reasoning> tags
  /<reasoning>([\s\S]*?)<\/reasoning>/gi,
  // DeepSeek-R1 / qwen3-coder style: <|begin_of_thought|>...<|end_of_thought|>
  /<\|begin_of_thought\|>([\s\S]*?)<\|end_of_thought\|>/gi,
  // Alternative DeepSeek format
  /<\|thinking\|>([\s\S]*?)<\|\/thinking\|>/gi,
];

// Heuristic patterns that suggest content is "reasoning" rather than actual response
const REASONING_HEURISTICS = [
  /^The user has shared a video with the ID of/i,
  /^Let me analyze/i,
  /^Let's analyze/i,
  /^I'll analyze/i,
  /^Looking at this/i,
  /^First, let me/i,
  /^Let me think/i,
  /^Thinking about/i,
  /^Analyzing the/i,
  // Additional reasoning patterns
  /^I need to think/i,
  /^Let me reason/i,
  /^My reasoning/i,
  /^Step by step/i,
  /^Breaking this down/i,
  /^Let me work through/i,
  /^I should consider/i,
  /^To solve this/i,
  /^The key here is/i,
];

interface ContentPart {
  type: 'reasoning' | 'content';
  text: string;
}

function parseContent(content: string): ContentPart[] {
  const parts: ContentPart[] = [];

  // Try each regex pattern to find reasoning blocks
  for (const pattern of REASONING_REGEX_PATTERNS) {
    // Reset lastIndex for global regex
    pattern.lastIndex = 0;

    // Check if this pattern matches
    if (pattern.test(content)) {
      // Reset again after test
      pattern.lastIndex = 0;

      let lastIndex = 0;
      let match;

      while ((match = pattern.exec(content)) !== null) {
        // Add content before this reasoning block
        if (match.index > lastIndex) {
          const beforeContent = content.substring(lastIndex, match.index).trim();
          if (beforeContent) {
            parts.push({ type: 'content', text: beforeContent });
          }
        }

        // Add reasoning block (captured group 1)
        const reasoningContent = match[1].trim();
        if (reasoningContent) {
          parts.push({ type: 'reasoning', text: reasoningContent });
        }

        lastIndex = match.index + match[0].length;
      }

      // Add remaining content after last reasoning block
      if (lastIndex < content.length) {
        const remainingContent = content.substring(lastIndex).trim();
        if (remainingContent) {
          parts.push({ type: 'content', text: remainingContent });
        }
      }

      // If we found matches, return the parts
      if (parts.length > 0) {
        return parts;
      }
    }
  }

  // No explicit tags found - check for heuristic patterns
  // Look for content that appears to be internal reasoning followed by actual response
  const lines = content.split('\n\n');

  // Check if the first paragraph looks like reasoning
  if (lines.length > 1) {
    const firstPara = lines[0].trim();
    const isReasoning = REASONING_HEURISTICS.some(pattern => pattern.test(firstPara));

    if (isReasoning) {
      // Find where the actual response starts (usually after a more definitive statement)
      let reasoningEnd = 0;
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        // Look for response indicators
        if (
          line.startsWith('##') ||
          line.startsWith('**Summary') ||
          line.startsWith('**Key') ||
          line.startsWith('Here') ||
          line.startsWith('Based on') ||
          line.match(/^[0-9]+\./) // Numbered list start
        ) {
          reasoningEnd = i;
          break;
        }
        reasoningEnd = i + 1;
      }

      // Only treat as reasoning if it's not the entire content
      if (reasoningEnd > 0 && reasoningEnd < lines.length) {
        const reasoningContent = lines.slice(0, reasoningEnd).join('\n\n').trim();
        const mainContent = lines.slice(reasoningEnd).join('\n\n').trim();

        if (reasoningContent && mainContent) {
          parts.push({ type: 'reasoning', text: reasoningContent });
          parts.push({ type: 'content', text: mainContent });
          return parts;
        }
      }
    }
  }

  // No reasoning detected - return as-is
  return [{ type: 'content', text: content }];
}

export const MarkdownRenderer = memo(({ content, className }: MarkdownRendererProps) => {
  const parts = useMemo(() => parseContent(content), [content]);
  const [previewCode, setPreviewCode] = useState<string | null>(null);

  return (
    <PreviewContext.Provider value={setPreviewCode}>
      <div className={className}>
        {parts.map((part, index) => {
          if (part.type === 'reasoning') {
            return <ReasoningBlock key={index} content={part.text} />;
          }
          return (
            <ReactMarkdown
              key={index}
              remarkPlugins={[remarkGfm]}
              components={markdownComponents}
            >
              {part.text}
            </ReactMarkdown>
          );
        })}
      </div>

      <Dialog open={!!previewCode} onOpenChange={(open) => !open && setPreviewCode(null)}>
        <DialogContent className="max-w-[90vw] w-[1200px] h-[85vh] flex flex-col p-0 gap-0">
          <DialogHeader className="p-4 border-b">
            <DialogTitle>HTML Preview</DialogTitle>
          </DialogHeader>
          <div className="flex-1 w-full h-full bg-white relative rounded-b-lg overflow-hidden">
            <iframe
              srcDoc={previewCode || ''}
              className="w-full h-full border-0 block"
              title="HTML Preview"
              sandbox="allow-scripts allow-popups allow-modals"
            />
          </div>
        </DialogContent>
      </Dialog>
    </PreviewContext.Provider>
  );
});
