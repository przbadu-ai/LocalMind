import { useState, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronRight, Brain } from 'lucide-react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

interface ReasoningBlockProps {
  content: string;
  defaultOpen?: boolean;
}

function ReasoningBlock({ content, defaultOpen = false }: ReasoningBlockProps) {
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

// Patterns to detect reasoning/thinking blocks
const REASONING_PATTERNS = [
  // <think>...</think> tags (common in many reasoning models)
  { start: /<think>/i, end: /<\/think>/i, tagStart: '<think>', tagEnd: '</think>' },
  // <thinking>...</thinking> tags
  { start: /<thinking>/i, end: /<\/thinking>/i, tagStart: '<thinking>', tagEnd: '</thinking>' },
  // <reasoning>...</reasoning> tags
  { start: /<reasoning>/i, end: /<\/reasoning>/i, tagStart: '<reasoning>', tagEnd: '</reasoning>' },
  // DeepSeek-R1 / qwen3-coder style: <|begin_of_thought|>...<|end_of_thought|>
  { start: /<\|begin_of_thought\|>/i, end: /<\|end_of_thought\|>/i, tagStart: '<|begin_of_thought|>', tagEnd: '<|end_of_thought|>' },
  // Alternative DeepSeek format
  { start: /<\|thinking\|>/i, end: /<\|\/thinking\|>/i, tagStart: '<|thinking|>', tagEnd: '<|/thinking|>' },
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
  let remaining = content;

  // First, check for explicit reasoning tags
  for (const pattern of REASONING_PATTERNS) {
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

        // Add reasoning block
        const reasoningContent = afterStart.substring(0, endMatch.index!).trim();
        if (reasoningContent) {
          parts.push({ type: 'reasoning', text: reasoningContent });
        }

        // Continue with remaining content
        remaining = afterStart.substring(endMatch.index! + pattern.tagEnd.length).trim();
      }
    }
  }

  // If we found reasoning tags, add remaining content
  if (parts.length > 0 && remaining) {
    parts.push({ type: 'content', text: remaining });
    return parts;
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

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  const parts = useMemo(() => parseContent(content), [content]);

  return (
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
  );
}
