import * as React from 'react';
import { Save, RotateCcw, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface SettingsSectionProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
  onSave?: () => void;
  onReset?: () => void;
  hasChanges?: boolean;
  isSaving?: boolean;
  canEdit?: boolean;
  compact?: boolean; // When true, skip Card wrapper (for use inside ExpandableSection)
}

export function SettingsSection({
  title,
  description,
  icon,
  children,
  onSave,
  onReset,
  hasChanges = false,
  isSaving = false,
  canEdit = true,
  compact = false,
}: SettingsSectionProps) {
  const showHeader = title || description || icon;
  const showActions = canEdit && (onSave || onReset);

  const header = showHeader || showActions ? (
    <div className={`flex items-start justify-between ${compact ? 'mb-4' : 'p-4 border-b border-base-300'}`}>
      {showHeader && (
        <div>
          {title && (
            <h2 className="text-lg font-semibold flex items-center gap-2">
              {icon}
              {title}
            </h2>
          )}
          {description && (
            <p className="text-sm text-base-content/60 mt-1">{description}</p>
          )}
        </div>
      )}
      {showActions && (
        <div className="flex items-center gap-2">
          {onReset && hasChanges && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onReset}
              disabled={isSaving}
            >
              <RotateCcw size={14} className="mr-1" />
              Reset
            </Button>
          )}
          {onSave && (
            <Button
              variant="primary"
              size="sm"
              onClick={onSave}
              disabled={!hasChanges || isSaving}
            >
              {isSaving ? (
                <>
                  <Loader2 size={14} className="mr-1 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save size={14} className="mr-1" />
                  Save
                </>
              )}
            </Button>
          )}
        </div>
      )}
    </div>
  ) : null;

  const content = <div className={compact ? '' : 'p-4'}>{children}</div>;

  if (compact) {
    return (
      <div>
        {header}
        {content}
      </div>
    );
  }

  return (
    <Card>
      {header}
      <CardContent className="p-4">{children}</CardContent>
    </Card>
  );
}
