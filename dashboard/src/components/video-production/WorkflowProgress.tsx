/**
 * WorkflowProgress - Horizontal stepper showing video production workflow
 *
 * Features:
 * - Shows workflow steps: Scripts -> Voiceover -> Props -> Timeline -> Render
 * - Each step shows icon, label, status indicator
 * - Visual connections between steps
 * - Clickable steps for navigation
 * - Tooltip for disabled steps explaining why
 */

import { useState, useRef, useEffect, useCallback, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { createPortal } from 'react-dom';
import type { LucideIcon } from 'lucide-react';
import {
  Code,
  Mic,
  FileJson,
  Layers,
  Play,
  Check,
} from 'lucide-react';
import { cn } from '@/utils/cn';

// ============================================================================
// Types
// ============================================================================

export type StepStatus = 'complete' | 'current' | 'available' | 'disabled';

export interface WorkflowStep {
  id: string;
  label: string;
  icon: LucideIcon;
  path: string;
  status: StepStatus;
  disabledReason?: string;
}

interface WorkflowProgressProps {
  /** Current step ID based on URL */
  currentStep: string;
  /** Set of completed step IDs */
  completedSteps: Set<string>;
  /** Callback when a step is clicked */
  onStepClick?: (stepId: string, path: string) => void;
  /** Additional className */
  className?: string;
}

// ============================================================================
// Step Configuration
// ============================================================================

const WORKFLOW_STEPS: Omit<WorkflowStep, 'status' | 'disabledReason'>[] = [
  { id: 'scripts', label: 'Scripts', icon: Code, path: '/video/scripts' },
  { id: 'voiceover', label: 'Voiceover', icon: Mic, path: '/video/assets' },
  { id: 'props', label: 'Props', icon: FileJson, path: '/video/props' },
  { id: 'timeline', label: 'Timeline', icon: Layers, path: '/video/timeline' },
  { id: 'render', label: 'Render', icon: Play, path: '/video/render' },
];

// ============================================================================
// Step Tooltip Component
// ============================================================================

interface StepTooltipProps {
  content: string;
  children: ReactNode;
  show?: boolean;
}

function StepTooltip({ content, children, show = true }: StepTooltipProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  const updatePosition = useCallback(() => {
    if (!triggerRef.current || !show) return;

    const rect = triggerRef.current.getBoundingClientRect();
    const padding = 8;

    setPosition({
      top: rect.bottom + padding,
      left: rect.left + rect.width / 2,
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

  const tooltipContent = isHovered && show && position ? (
    <div
      className="z-[9999] px-2 py-1 rounded shadow-lg bg-base-300 text-xs text-base-content border border-base-content/10 whitespace-nowrap"
      style={{
        position: 'fixed',
        top: `${position.top}px`,
        left: `${position.left}px`,
        transform: 'translateX(-50%)',
      }}
      role="tooltip"
    >
      {content}
    </div>
  ) : null;

  return (
    <div
      ref={triggerRef}
      className="relative"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {children}
      {createPortal(tooltipContent, document.body)}
    </div>
  );
}

// ============================================================================
// Step Icon Component
// ============================================================================

interface StepIconProps {
  step: WorkflowStep;
  onClick?: () => void;
}

function StepIcon({ step, onClick }: StepIconProps) {
  const Icon = step.icon;
  const isClickable = step.status !== 'disabled';

  const baseClasses = cn(
    'flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all duration-200',
    // Complete state
    step.status === 'complete' && 'bg-success border-success text-success-content',
    // Current state
    step.status === 'current' && 'bg-primary border-primary text-primary-content ring-2 ring-primary/30 ring-offset-2 ring-offset-base-100',
    // Available state
    step.status === 'available' && 'bg-base-100 border-base-300 text-base-content hover:border-primary hover:text-primary',
    // Disabled state
    step.status === 'disabled' && 'bg-base-200 border-base-300 text-base-content/40 cursor-not-allowed',
    // Clickable cursor
    isClickable && 'cursor-pointer'
  );

  const content = (
    <button
      type="button"
      className={baseClasses}
      onClick={isClickable ? onClick : undefined}
      disabled={!isClickable}
      aria-label={`${step.label} - ${step.status}`}
      aria-current={step.status === 'current' ? 'step' : undefined}
    >
      {step.status === 'complete' ? (
        <Check size={18} strokeWidth={2.5} />
      ) : (
        <Icon size={18} />
      )}
    </button>
  );

  // Wrap in tooltip if disabled
  if (step.status === 'disabled' && step.disabledReason) {
    return (
      <StepTooltip content={step.disabledReason}>
        {content}
      </StepTooltip>
    );
  }

  return content;
}

// ============================================================================
// Connector Line Component
// ============================================================================

interface ConnectorProps {
  fromStatus: StepStatus;
  toStatus: StepStatus;
}

function Connector({ fromStatus, toStatus }: ConnectorProps) {
  // Line is filled if the 'from' step is complete
  const isFilled = fromStatus === 'complete';
  // Line is partially filled if 'from' is current and 'to' is available
  const isPartial = fromStatus === 'current' && toStatus === 'available';

  return (
    <div className="flex-1 h-0.5 mx-2 relative">
      {/* Background line */}
      <div className="absolute inset-0 bg-base-300 rounded-full" />
      {/* Filled portion */}
      {isFilled && (
        <div className="absolute inset-0 bg-success rounded-full" />
      )}
      {isPartial && (
        <div className="absolute left-0 top-0 bottom-0 w-1/2 bg-primary rounded-full" />
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function WorkflowProgress({
  currentStep,
  completedSteps,
  onStepClick,
  className,
}: WorkflowProgressProps) {
  const navigate = useNavigate();

  // Build steps with status
  const steps: WorkflowStep[] = WORKFLOW_STEPS.map((step, index) => {
    let status: StepStatus;
    let disabledReason: string | undefined;

    if (completedSteps.has(step.id)) {
      status = 'complete';
    } else if (step.id === currentStep) {
      status = 'current';
    } else {
      // Check if previous step is complete or current
      const prevStepIndex = index - 1;
      const prevStep = WORKFLOW_STEPS[prevStepIndex];

      if (prevStepIndex < 0) {
        // First step is always available
        status = 'available';
      } else if (completedSteps.has(prevStep.id) || prevStep.id === currentStep) {
        status = 'available';
      } else {
        status = 'disabled';
        disabledReason = `Complete ${prevStep.label} first`;
      }
    }

    return { ...step, status, disabledReason };
  });

  const handleStepClick = (step: WorkflowStep) => {
    if (step.status === 'disabled') return;

    if (onStepClick) {
      onStepClick(step.id, step.path);
    } else {
      navigate(step.path);
    }
  };

  return (
    <div className={cn('bg-base-200 rounded-lg p-4', className)}>
      <div className="flex items-center justify-between max-w-2xl mx-auto">
        {steps.map((step, index) => (
          <div key={step.id} className="contents">
            {/* Step */}
            <div className="flex flex-col items-center gap-2">
              <StepIcon
                step={step}
                onClick={() => handleStepClick(step)}
              />
              <span
                className={cn(
                  'text-xs font-medium transition-colors',
                  step.status === 'complete' && 'text-success',
                  step.status === 'current' && 'text-primary',
                  step.status === 'available' && 'text-base-content',
                  step.status === 'disabled' && 'text-base-content/40'
                )}
              >
                {step.label}
              </span>
            </div>

            {/* Connector (not after last step) */}
            {index < steps.length - 1 && (
              <Connector
                fromStatus={step.status}
                toStatus={steps[index + 1].status}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// Helper hook for determining step from URL
// ============================================================================

export function useCurrentWorkflowStep(pathname: string): string {
  // Map URL paths to step IDs
  const pathToStep: Record<string, string> = {
    '/video/scripts': 'scripts',
    '/video/assets': 'voiceover',
    '/video/props': 'props',
    '/video/timeline': 'timeline',
    '/video/render': 'render',
  };

  return pathToStep[pathname] || 'scripts';
}

export default WorkflowProgress;
