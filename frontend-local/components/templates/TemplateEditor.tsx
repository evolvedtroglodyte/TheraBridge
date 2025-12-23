'use client';

import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { Template, TemplateField, TemplateSection } from '@/lib/types';
import { AlertCircle, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TemplateEditorProps {
  template: Template;
  initialContent?: Record<string, any>;
  onContentChange: (content: Record<string, any>) => void;
  onAutoFill?: () => Promise<void>;
  isAutoFilling?: boolean;
  showAutoFill?: boolean;
}

export function TemplateEditor({
  template,
  initialContent = {},
  onContentChange,
  onAutoFill,
  isAutoFilling = false,
  showAutoFill = false,
}: TemplateEditorProps) {
  const [content, setContent] = React.useState<Record<string, any>>(initialContent);
  const [touchedFields, setTouchedFields] = React.useState<Set<string>>(new Set());

  // Update parent when content changes
  React.useEffect(() => {
    onContentChange(content);
  }, [content, onContentChange]);

  // Update content when initialContent changes (e.g., after autofill)
  React.useEffect(() => {
    if (Object.keys(initialContent).length > 0) {
      setContent(initialContent);
    }
  }, [initialContent]);

  const handleFieldChange = (sectionId: string, fieldId: string, value: any) => {
    setContent((prev) => ({
      ...prev,
      [sectionId]: {
        ...(prev[sectionId] || {}),
        [fieldId]: value,
      },
    }));
    setTouchedFields((prev) => new Set(prev).add(`${sectionId}.${fieldId}`));
  };

  const getFieldValue = (sectionId: string, fieldId: string): any => {
    return content[sectionId]?.[fieldId] ?? '';
  };

  const isFieldTouched = (sectionId: string, fieldId: string): boolean => {
    return touchedFields.has(`${sectionId}.${fieldId}`);
  };

  const isFieldEmpty = (sectionId: string, fieldId: string): boolean => {
    const value = getFieldValue(sectionId, fieldId);
    if (Array.isArray(value)) return value.length === 0;
    if (typeof value === 'string') return value.trim() === '';
    if (typeof value === 'boolean') return false;
    return value == null;
  };

  const renderField = (section: TemplateSection, field: TemplateField) => {
    const fieldId = `${section.id}-${field.id}`;
    const value = getFieldValue(section.id, field.id);
    const isEmpty = isFieldEmpty(section.id, field.id);
    const isTouched = isFieldTouched(section.id, field.id);
    const showError = field.required && isEmpty && isTouched;

    const fieldLabel = (
      <label htmlFor={fieldId} className="text-sm font-medium flex items-center gap-2">
        {field.label}
        {field.required && <span className="text-destructive">*</span>}
        {field.help_text && (
          <span className="text-xs text-muted-foreground font-normal">
            ({field.help_text})
          </span>
        )}
      </label>
    );

    switch (field.type) {
      case 'text':
        return (
          <div key={fieldId} className="space-y-2">
            {fieldLabel}
            <Input
              id={fieldId}
              value={value || ''}
              onChange={(e) => handleFieldChange(section.id, field.id, e.target.value)}
              placeholder={field.placeholder || ''}
              className={cn(showError && 'border-destructive')}
            />
            {showError && (
              <p className="text-xs text-destructive flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                This field is required
              </p>
            )}
          </div>
        );

      case 'textarea':
        return (
          <div key={fieldId} className="space-y-2">
            {fieldLabel}
            <Textarea
              id={fieldId}
              value={value || ''}
              onChange={(e) => handleFieldChange(section.id, field.id, e.target.value)}
              placeholder={field.placeholder || ''}
              rows={4}
              className={cn(showError && 'border-destructive')}
            />
            {showError && (
              <p className="text-xs text-destructive flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                This field is required
              </p>
            )}
          </div>
        );

      case 'select':
        return (
          <div key={fieldId} className="space-y-2">
            {fieldLabel}
            <select
              id={fieldId}
              value={value || ''}
              onChange={(e) => handleFieldChange(section.id, field.id, e.target.value)}
              className={cn(
                'w-full rounded-md border border-input bg-background px-3 py-2 text-sm',
                'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                showError && 'border-destructive'
              )}
            >
              <option value="">Select an option...</option>
              {field.options?.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {showError && (
              <p className="text-xs text-destructive flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                This field is required
              </p>
            )}
          </div>
        );

      case 'checkbox':
        return (
          <div key={fieldId} className="flex items-center space-x-2">
            <Checkbox
              id={fieldId}
              checked={value || false}
              onCheckedChange={(checked) =>
                handleFieldChange(section.id, field.id, checked)
              }
            />
            {fieldLabel}
          </div>
        );

      case 'number':
        return (
          <div key={fieldId} className="space-y-2">
            {fieldLabel}
            <Input
              id={fieldId}
              type="number"
              value={value || ''}
              onChange={(e) =>
                handleFieldChange(section.id, field.id, parseFloat(e.target.value))
              }
              placeholder={field.placeholder || ''}
              className={cn(showError && 'border-destructive')}
            />
            {showError && (
              <p className="text-xs text-destructive flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                This field is required
              </p>
            )}
          </div>
        );

      case 'date':
        return (
          <div key={fieldId} className="space-y-2">
            {fieldLabel}
            <Input
              id={fieldId}
              type="date"
              value={value || ''}
              onChange={(e) => handleFieldChange(section.id, field.id, e.target.value)}
              className={cn(showError && 'border-destructive')}
            />
            {showError && (
              <p className="text-xs text-destructive flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                This field is required
              </p>
            )}
          </div>
        );

      case 'scale':
        return (
          <div key={fieldId} className="space-y-2">
            {fieldLabel}
            <div className="flex items-center gap-2">
              <Input
                id={fieldId}
                type="range"
                min="0"
                max="10"
                value={value || 0}
                onChange={(e) =>
                  handleFieldChange(section.id, field.id, parseInt(e.target.value))
                }
                className="flex-1"
              />
              <span className="text-sm font-medium w-8 text-center">{value || 0}</span>
            </div>
            {showError && (
              <p className="text-xs text-destructive flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                This field is required
              </p>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with auto-fill button */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">{template.name}</h3>
          {template.description && (
            <p className="text-sm text-muted-foreground">{template.description}</p>
          )}
        </div>
        {showAutoFill && onAutoFill && (
          <Button
            onClick={onAutoFill}
            disabled={isAutoFilling}
            variant="outline"
            size="sm"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            {isAutoFilling ? 'Auto-filling...' : 'Auto-fill from AI'}
          </Button>
        )}
      </div>

      {/* Sections */}
      <div className="space-y-6">
        {template.structure.sections.map((section) => (
          <Card key={section.id}>
            <CardHeader>
              <CardTitle className="text-base">{section.name}</CardTitle>
              {section.description && (
                <CardDescription>{section.description}</CardDescription>
              )}
            </CardHeader>
            <CardContent className="space-y-4">
              {section.fields.map((field) => renderField(section, field))}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Required fields notice */}
      <div className="flex items-start gap-2 p-3 rounded-md bg-muted/50 text-xs text-muted-foreground">
        <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <span>Fields marked with * are required</span>
      </div>
    </div>
  );
}
