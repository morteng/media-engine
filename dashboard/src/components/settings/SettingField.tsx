import * as React from 'react';
import clsx from 'clsx';
import { Database, FileCode, Terminal, Lock } from 'lucide-react';
import type { SettingSource, SettingValue } from '@/api/types';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select';

interface SettingFieldProps<T = unknown> {
  name: string;
  setting: SettingValue<T>;
  onChange?: (value: T) => void;
  options?: { value: string; label: string }[];
  disabled?: boolean;
}

const sourceIcons: Record<SettingSource, typeof Database> = {
  default: Database,
  project: FileCode,
  env: Terminal,
};

const sourceLabels: Record<SettingSource, string> = {
  default: 'Default',
  project: 'project.yaml',
  env: 'Environment',
};

const sourceColors: Record<SettingSource, string> = {
  default: 'text-base-content/50',
  project: 'text-primary',
  env: 'text-warning',
};

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '';
  if (Array.isArray(value)) return value.join(', ');
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

export function SettingField<T>({
  name,
  setting,
  onChange,
  options,
  disabled: disabledProp,
}: SettingFieldProps<T>) {
  const SourceIcon = sourceIcons[setting.source];
  const isDisabled = disabledProp || !setting.editable;
  const isToggle = typeof setting.value === 'boolean';
  const isNumber = typeof setting.value === 'number';
  const hasOptions = options && options.length > 0;

  const handleChange = React.useCallback(
    (newValue: T) => {
      if (onChange && !isDisabled) {
        onChange(newValue);
      }
    },
    [onChange, isDisabled]
  );

  const renderInput = () => {
    if (isToggle) {
      return (
        <input
          type="checkbox"
          className="toggle toggle-primary toggle-sm"
          checked={setting.value as boolean}
          onChange={(e) => handleChange(e.target.checked as T)}
          disabled={isDisabled}
        />
      );
    }

    if (hasOptions) {
      return (
        <Select
          value={String(setting.value)}
          onValueChange={(v) => handleChange((isNumber ? Number(v) : v) as T)}
          disabled={isDisabled}
        >
          <SelectTrigger className="w-40 h-8 text-sm">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {options.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      );
    }

    if (isNumber) {
      return (
        <Input
          type="number"
          className="w-32 h-8 text-sm"
          value={setting.value as number}
          onChange={(e) => handleChange(Number(e.target.value) as T)}
          disabled={isDisabled}
        />
      );
    }

    // String/text input
    return (
      <Input
        type="text"
        className="w-64 h-8 text-sm"
        value={formatValue(setting.value)}
        onChange={(e) => handleChange(e.target.value as T)}
        disabled={isDisabled}
      />
    );
  };

  return (
    <div className="flex items-center justify-between py-3 border-b border-base-300 last:border-0">
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <Label className="font-medium capitalize">
            {name.replace(/_/g, ' ')}
          </Label>
          {!setting.editable && (
            <Lock size={12} className="text-base-content/40" />
          )}
        </div>
        <p className="text-xs text-base-content/60 mt-0.5">
          {setting.description}
        </p>
        {setting.value !== setting.default && (
          <p className="text-xs text-base-content/40 mt-0.5">
            Default: {formatValue(setting.default)}
          </p>
        )}
      </div>

      <div className="flex items-center gap-3">
        {renderInput()}

        <div
          className={clsx(
            'flex items-center gap-1 text-xs',
            sourceColors[setting.source]
          )}
          title={`Source: ${sourceLabels[setting.source]}`}
        >
          <SourceIcon size={12} />
          <span className="hidden sm:inline">{sourceLabels[setting.source]}</span>
        </div>
      </div>
    </div>
  );
}
