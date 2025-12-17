import { useState, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight, Brain } from 'lucide-react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

interface ThinkingBlockProps {
  content: string;
  defaultOpen?: boolean;
}

function ThinkingBlock({ content, defaultOpen = false }: ThinkingBlockProps) {
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
        <span>Thinking</span>
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
}

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
  code: ({ children, className, ...props }: any) => {
    const isInline = !('data-language' in props);
    if (isInline) {
      return (
        <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs">
          {children}
        </code>
      );
    }
    return (
      <pre className="bg-muted p-3 rounded-lg overflow-x-auto my-3">
        <code className={cn("font-mono text-xs", className)}>
          {children}
        </code>
      </pre>
    );
  },
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

// Patterns to detect thinking blocks
const THINKING_PATTERNS = [
  // <think>...</think> tags
  { start: /<think>/i, end: /<\/think>/i, tagStart: '<think>', tagEnd: '</think>' },
  // <thinking>...</thinking> tags
  { start: /<thinking>/i, end: /<\/thinking>/i, tagStart: '<thinking>', tagEnd: '</thinking>' },
  // Common LLM thinking patterns - detect by content patterns
];

// Heuristic patterns that suggest content is "thinking" rather than actual response
const THINKING_HEURISTICS = [
  /^The user has shared a video with the ID of/i,
  /^Let me analyze/i,
  /^Let's analyze/i,
  /^I'll analyze/i,
  /^Looking at this/i,
  /^First, let me/i,
  /^Let me think/i,
  /^Thinking about/i,
  /^Analyzing the/i,
];

interface ContentPart {
  type: 'thinking' | 'content';
  text: string;
}

function parseContent(content: string): ContentPart[] {
  const parts: ContentPart[] = [];
  let remaining = content;

  // First, check for explicit thinking tags
  for (const pattern of THINKING_PATTERNS) {
    const startMatch = remaining.match(pattern.start);
    if (startMatch) {
      const startIndex = startMatch.index!;
      const afterStart = remaining.substring(startIndex + pattern.tagStart.length);
      const endMatch = afterStart.match(pattern.end);

      if (endMatch) {
        // Add content before thinking block
        if (startIndex > 0) {
          const beforeContent = remaining.substring(0, startIndex).trim();
          if (beforeContent) {
            parts.push({ type: 'content', text: beforeContent });
          }
        }

        // Add thinking block
        const thinkingContent = afterStart.substring(0, endMatch.index!).trim();
        if (thinkingContent) {
          parts.push({ type: 'thinking', text: thinkingContent });
        }

        // Continue with remaining content
        remaining = afterStart.substring(endMatch.index! + pattern.tagEnd.length).trim();
      }
    }
  }

  // If we found thinking tags, add remaining content
  if (parts.length > 0 && remaining) {
    parts.push({ type: 'content', text: remaining });
    return parts;
  }

  // No explicit tags found - check for heuristic patterns
  // Look for content that appears to be internal reasoning followed by actual response
  const lines = content.split('\n\n');

  // Check if the first paragraph looks like thinking
  if (lines.length > 1) {
    const firstPara = lines[0].trim();
    const isThinking = THINKING_HEURISTICS.some(pattern => pattern.test(firstPara));

    if (isThinking) {
      // Find where the actual response starts (usually after a more definitive statement)
      let thinkingEnd = 0;
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
          thinkingEnd = i;
          break;
        }
        thinkingEnd = i + 1;
      }

      // Only treat as thinking if it's not the entire content
      if (thinkingEnd > 0 && thinkingEnd < lines.length) {
        const thinkingContent = lines.slice(0, thinkingEnd).join('\n\n').trim();
        const mainContent = lines.slice(thinkingEnd).join('\n\n').trim();

        if (thinkingContent && mainContent) {
          parts.push({ type: 'thinking', text: thinkingContent });
          parts.push({ type: 'content', text: mainContent });
          return parts;
        }
      }
    }
  }

  // No thinking detected - return as-is
  return [{ type: 'content', text: content }];
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  const parts = useMemo(() => parseContent(content), [content]);

  return (
    <div className={className}>
      {parts.map((part, index) => {
        if (part.type === 'thinking') {
          return <ThinkingBlock key={index} content={part.text} />;
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
  );
}
