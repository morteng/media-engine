import { Info } from 'lucide-react';
import { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import clsx from 'clsx';

interface InfoTooltipProps {
  content: string;
  title?: string;
  size?: 'sm' | 'md' | 'lg';
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export function InfoTooltip({
  content,
  title,
  size = 'sm',
  position = 'top'
}: InfoTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [tooltipStyle, setTooltipStyle] = useState<React.CSSProperties>({});
  const triggerRef = useRef<HTMLButtonElement>(null);

  const iconSizes = {
    sm: 14,
    md: 16,
    lg: 18,
  };

  const updateTooltipPosition = useCallback(() => {
    if (!triggerRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const padding = 8;
    const tooltipWidth = 280;
    const tooltipHeight = 100; // Estimate

    let top = 0;
    let left = 0;
    let actualPosition = position;

    // Calculate initial position
    switch (position) {
      case 'top':
        top = triggerRect.top - tooltipHeight - padding;
        left = triggerRect.left + triggerRect.width / 2 - tooltipWidth / 2;
        break;
      case 'bottom':
        top = triggerRect.bottom + padding;
        left = triggerRect.left + triggerRect.width / 2 - tooltipWidth / 2;
        break;
      case 'left':
        top = triggerRect.top + triggerRect.height / 2 - tooltipHeight / 2;
        left = triggerRect.left - tooltipWidth - padding;
        break;
      case 'right':
        top = triggerRect.top + triggerRect.height / 2 - tooltipHeight / 2;
        left = triggerRect.right + padding;
        break;
    }

    // Adjust for viewport boundaries
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    // Flip if necessary
    if (position === 'top' && top < 0) {
      actualPosition = 'bottom';
      top = triggerRect.bottom + padding;
    } else if (position === 'bottom' && top + tooltipHeight > viewportHeight) {
      actualPosition = 'top';
      top = triggerRect.top - tooltipHeight - padding;
    } else if (position === 'left' && left < 0) {
      actualPosition = 'right';
      left = triggerRect.right + padding;
    } else if (position === 'right' && left + tooltipWidth > viewportWidth) {
      actualPosition = 'left';
      left = triggerRect.left - tooltipWidth - padding;
    }

    // Keep within horizontal bounds
    left = Math.max(8, Math.min(left, viewportWidth - tooltipWidth - 8));
    // Keep within vertical bounds
    top = Math.max(8, Math.min(top, viewportHeight - tooltipHeight - 8));

    setTooltipStyle({
      position: 'fixed',
      top: `${top}px`,
      left: `${left}px`,
      width: `${tooltipWidth}px`,
      ['--tooltip-position' as string]: actualPosition,
    });
  }, [position]);

  useEffect(() => {
    if (isVisible) {
      updateTooltipPosition();
      window.addEventListener('scroll', updateTooltipPosition, true);
      window.addEventListener('resize', updateTooltipPosition);
      return () => {
        window.removeEventListener('scroll', updateTooltipPosition, true);
        window.removeEventListener('resize', updateTooltipPosition);
      };
    }
  }, [isVisible, updateTooltipPosition]);

  const tooltipContent = isVisible ? (
    <div
      className="info-tooltip-portal"
      style={tooltipStyle}
      role="tooltip"
    >
      {title && <strong className="tooltip-title">{title}</strong>}
      <span className="tooltip-text">{content}</span>
    </div>
  ) : null;

  return (
    <span className="info-tooltip-wrapper">
      <button
        ref={triggerRef}
        type="button"
        className={clsx('info-tooltip-trigger', `info-tooltip-${size}`)}
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        aria-label={title || 'More information'}
      >
        <Info size={iconSizes[size]} />
      </button>
      {createPortal(tooltipContent, document.body)}
    </span>
  );
}

// Metric explanation constants for reuse across pages
export const METRIC_EXPLANATIONS = {
  // Health & Quality Scores
  healthScore: {
    title: 'Health Score',
    content: 'Weighted average of all component scores. Above 90 = Excellent (A), 80-89 = Good (B), 70-79 = Fair (C), below 70 = Needs Work.',
  },
  qualityScore: {
    title: 'Quality Score',
    content: 'Overall content quality based on freshness, translation coverage, consistency, links, readability, dependencies, and metadata completeness.',
  },

  // Component Scores
  freshness: {
    title: 'Freshness',
    content: 'Percentage of documents updated within configured freshness period (default: 90 days). Stale content reduces this score.',
  },
  translation: {
    title: 'Translation Coverage',
    content: 'Percentage of source documents with up-to-date translations. Outdated or missing translations reduce this score.',
  },
  consistency: {
    title: 'Consistency',
    content: 'Checks for incomplete markers (TODO, FIXME), draft status in final docs, and style uniformity across documents.',
  },
  links: {
    title: 'Link Health',
    content: 'Percentage of valid internal and external links. Broken links, redirects, and missing references reduce this score.',
  },
  readability: {
    title: 'Readability',
    content: 'Based on Flesch Reading Ease, Flesch-Kincaid Grade, and language-specific metrics (LIX for Scandinavian). Target: accessible to general audience.',
  },
  dependencies: {
    title: 'Dependencies',
    content: 'Measures proper prerequisite ordering and cross-references. Orphan documents and circular dependencies reduce this score.',
  },
  metadata: {
    title: 'Metadata Completeness',
    content: 'Percentage of documents with complete frontmatter: title, version, status, author, and required custom fields.',
  },

  // Dashboard Metrics
  documentCount: {
    title: 'Total Documents',
    content: 'Count of all content documents (markdown, YAML scripts) across all languages in the project.',
  },
  languageCount: {
    title: 'Languages',
    content: 'Number of language variants configured for your project. Each language has its own content directory.',
  },
  issueCount: {
    title: 'Issues',
    content: 'Total quality issues detected: critical errors + warnings. Critical issues block release, warnings are advisory.',
  },
  staleCount: {
    title: 'Stale Content',
    content: 'Documents not updated within the freshness period. Review and update or mark as still-current.',
  },

  // Advanced Analysis
  semanticDuplicates: {
    title: 'Near Duplicates',
    content: 'Document pairs with >85% semantic similarity using TF-IDF or embeddings. May indicate content that should be merged.',
  },
  terminologyDrift: {
    title: 'Terminology Drift',
    content: 'Inconsistent term usage across documents (e.g., "API Key" vs "api-key"). Standardize for clarity.',
  },
  orphanConcepts: {
    title: 'Orphan Concepts',
    content: 'Concepts mentioned but never defined or linked. Add definitions or cross-references to improve navigation.',
  },
  prerequisiteIssues: {
    title: 'Prerequisite Issues',
    content: 'Documents using concepts before they are introduced. Reorder content or add links to prerequisite docs.',
  },

  // Freshness & Predictive
  freshnessProgress: {
    title: 'Overall Freshness',
    content: 'Percentage of tracked items (docs, assets) within their freshness window. Aims for >90% fresh content.',
  },
  predictiveStaleness: {
    title: 'Predictive Staleness',
    content: 'ML-based prediction of which documents are likely to become stale soon, based on update patterns and dependencies.',
  },
  highRiskDocs: {
    title: 'High Risk Documents',
    content: 'Documents predicted to become stale within 30 days based on historical update patterns and external dependencies.',
  },

  // Code Sync
  syntaxErrors: {
    title: 'Syntax Errors',
    content: 'Code blocks in documentation with invalid syntax. These examples will not run and should be fixed.',
  },
  deprecatedPatterns: {
    title: 'Deprecated Patterns',
    content: 'Code examples using deprecated APIs or patterns. Update to current best practices.',
  },
  apiIssues: {
    title: 'API Reference Issues',
    content: 'Documentation references to functions/classes that no longer exist in the codebase.',
  },

  // Norwegian LIX
  lixScore: {
    title: 'LIX Score',
    content: 'Scandinavian readability index. <25: Very Easy, 25-34: Easy, 35-44: Medium, 45-54: Difficult, >54: Very Difficult.',
  },

  // Activity
  recentCommits: {
    title: 'Recent Commits',
    content: 'Git commits affecting content files in the last 30 days. Indicates active maintenance.',
  },
  productionVelocity: {
    title: 'Production Velocity',
    content: 'Rate of content creation and updates over time. Helps track team productivity.',
  },
};

// Helper component for inline metric labels with tooltips
interface MetricLabelProps {
  label: string;
  metric: keyof typeof METRIC_EXPLANATIONS;
  className?: string;
}

export function MetricLabel({ label, metric, className }: MetricLabelProps) {
  const explanation = METRIC_EXPLANATIONS[metric];
  return (
    <span className={clsx('metric-label-with-info', className)}>
      {label}
      <InfoTooltip
        title={explanation.title}
        content={explanation.content}
      />
    </span>
  );
}

// Nav tooltip component for sidebar icons
interface NavTooltipProps {
  label: string;
  children: React.ReactNode;
  show?: boolean;
}

export function NavTooltip({ label, children, show = true }: NavTooltipProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  const updatePosition = useCallback(() => {
    if (!triggerRef.current || !show) return;

    const rect = triggerRef.current.getBoundingClientRect();
    const padding = 12;

    setPosition({
      top: rect.top + rect.height / 2,
      left: rect.right + padding,
    });
  }, [show]);

  useEffect(() => {
    if (isHovered && show) {
      updatePosition();
      window.addEventListener('scroll', updatePosition, true);
      window.addEventListener('resize', updatePosition);
      return () => {
        window.removeEventListener('scroll', updatePosition, true);
        window.removeEventListener('resize', updatePosition);
      };
    } else {
      setPosition(null);
    }
  }, [isHovered, show, updatePosition]);

  // Only render tooltip when we have a valid position
  const tooltipContent = isHovered && show && position ? (
    <div
      className="nav-tooltip-portal"
      style={{
        position: 'fixed',
        top: `${position.top}px`,
        left: `${position.left}px`,
        transform: 'translateY(-50%)',
      }}
      role="tooltip"
    >
      {label}
    </div>
  ) : null;

  return (
    <div
      ref={triggerRef}
      className="nav-tooltip-wrapper"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {children}
      {createPortal(tooltipContent, document.body)}
    </div>
  );
}
