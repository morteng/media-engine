/**
 * YamlEditor - Simple YAML editor with syntax highlighting
 *
 * Uses a textarea with overlaid highlighting for a lightweight approach.
 * Highlights: keys, strings, numbers, booleans, comments
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import clsx from 'clsx';

interface YamlEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  readOnly?: boolean;
}

// Tokenize YAML for highlighting
function tokenizeYaml(text: string): { type: string; value: string }[] {
  const tokens: { type: string; value: string }[] = [];
  const lines = text.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    let pos = 0;

    // Check for comment
    const commentMatch = line.match(/^(\s*)(#.*)$/);
    if (commentMatch) {
      if (commentMatch[1]) {
        tokens.push({ type: 'whitespace', value: commentMatch[1] });
      }
      tokens.push({ type: 'comment', value: commentMatch[2] });
      if (i < lines.length - 1) {
        tokens.push({ type: 'newline', value: '\n' });
      }
      continue;
    }

    // Check for key-value
    const keyMatch = line.match(/^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:\s*)/);
    if (keyMatch) {
      if (keyMatch[1]) {
        tokens.push({ type: 'whitespace', value: keyMatch[1] });
      }
      tokens.push({ type: 'key', value: keyMatch[2] });
      tokens.push({ type: 'punctuation', value: keyMatch[3] });
      pos = keyMatch[0].length;

      const rest = line.slice(pos);

      // Check value type
      if (/^".*"$/.test(rest) || /^'.*'$/.test(rest)) {
        tokens.push({ type: 'string', value: rest });
      } else if (/^-?\d+(\.\d+)?$/.test(rest)) {
        tokens.push({ type: 'number', value: rest });
      } else if (/^(true|false|null|yes|no)$/i.test(rest)) {
        tokens.push({ type: 'boolean', value: rest });
      } else if (rest.startsWith('|') || rest.startsWith('>')) {
        tokens.push({ type: 'multiline', value: rest });
      } else if (rest.trim()) {
        tokens.push({ type: 'value', value: rest });
      }
    } else {
      // Check for list item
      const listMatch = line.match(/^(\s*)(-\s+)/);
      if (listMatch) {
        if (listMatch[1]) {
          tokens.push({ type: 'whitespace', value: listMatch[1] });
        }
        tokens.push({ type: 'list', value: listMatch[2] });
        pos = listMatch[0].length;

        const rest = line.slice(pos);
        if (rest.trim()) {
          // Check if it's a key-value in list
          const nestedKeyMatch = rest.match(/^([a-zA-Z_][a-zA-Z0-9_]*)(\s*:\s*)/);
          if (nestedKeyMatch) {
            tokens.push({ type: 'key', value: nestedKeyMatch[1] });
            tokens.push({ type: 'punctuation', value: nestedKeyMatch[2] });
            const nestedRest = rest.slice(nestedKeyMatch[0].length);
            if (nestedRest) {
              tokens.push({ type: 'value', value: nestedRest });
            }
          } else {
            tokens.push({ type: 'value', value: rest });
          }
        }
      } else {
        // Plain text
        tokens.push({ type: 'plain', value: line });
      }
    }

    if (i < lines.length - 1) {
      tokens.push({ type: 'newline', value: '\n' });
    }
  }

  return tokens;
}

// Render highlighted YAML
function renderHighlightedYaml(tokens: { type: string; value: string }[]): React.ReactNode[] {
  return tokens.map((token, i) => {
    const className = {
      key: 'text-primary font-medium',
      string: 'text-success',
      number: 'text-info',
      boolean: 'text-warning',
      comment: 'text-base-content/40 italic',
      punctuation: 'text-base-content/50',
      list: 'text-secondary',
      multiline: 'text-accent',
      value: 'text-base-content',
      whitespace: '',
      newline: '',
      plain: 'text-base-content/60',
    }[token.type] || '';

    if (token.type === 'newline') {
      return <br key={i} />;
    }

    return (
      <span key={i} className={className}>
        {token.value}
      </span>
    );
  });
}

export function YamlEditor({
  value,
  onChange,
  placeholder = 'Enter YAML content...',
  className = '',
  readOnly = false,
}: YamlEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const highlightRef = useRef<HTMLDivElement>(null);
  const [tokens, setTokens] = useState<{ type: string; value: string }[]>([]);

  // Tokenize on value change
  useEffect(() => {
    setTokens(tokenizeYaml(value));
  }, [value]);

  // Sync scroll between textarea and highlight
  const handleScroll = useCallback(() => {
    if (textareaRef.current && highlightRef.current) {
      highlightRef.current.scrollTop = textareaRef.current.scrollTop;
      highlightRef.current.scrollLeft = textareaRef.current.scrollLeft;
    }
  }, []);

  return (
    <div className={clsx('relative font-mono text-sm', className)}>
      {/* Highlighted overlay (behind textarea) */}
      <div
        ref={highlightRef}
        className="absolute inset-0 overflow-hidden pointer-events-none whitespace-pre-wrap break-words p-3"
        aria-hidden="true"
      >
        {value ? renderHighlightedYaml(tokens) : (
          <span className="text-base-content/40">{placeholder}</span>
        )}
      </div>

      {/* Invisible textarea for editing */}
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onScroll={handleScroll}
        placeholder=""
        readOnly={readOnly}
        className={clsx(
          'relative w-full h-full resize-none p-3',
          'bg-transparent text-transparent caret-base-content',
          'border border-base-300 rounded-lg',
          'focus:outline-none focus:border-primary',
          readOnly && 'cursor-default'
        )}
        spellCheck={false}
      />
    </div>
  );
}

export default YamlEditor;
