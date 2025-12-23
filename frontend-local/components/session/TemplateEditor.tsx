'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api-client';
import type {
  Template,
  TemplateField,
  TemplateSection,
  AutofillResponse,
  Session,
} from '@/lib/types';
import { Sparkles, AlertCircle, Loader2, Check } from 'lucide-react';

interface TemplateEditorProps {
  template: Template;
  initialContent?: Record<string, unknown>;
  onSave: (content: Record<string, unknown>) => void;
  onCancel?: () => void;
  sessionId: string;
  showAutofill?: boolean;
  session?: Session;
}

interface FieldError {
  fieldId: string;
  sectionId: string;
  message: string;
}

interface ConfidenceLevel {
  score: number;
  color: string;
  label: string;
}

/**
 * TemplateEditor Component
 *
 * Renders a clinical note template as an editable form with validation and AI autofill.
 * Supports all field types: text, textarea, select, multiselect, checkbox, number, date, scale.
 */
export function TemplateEditor({
  template,
  initialContent = {},
  onSave,
  onCancel,
  sessionId,
  showAutofill = false,
  session,
}: TemplateEditorProps) {
  const [formContent, setFormContent] = useState<Record<string, unknown>>(initialContent);
  const [errors, setErrors] = useState<FieldError[]>([]);
  const [isDirty, setIsDirty] = useState(false);
  const [isAutofilling, setIsAutofilling] = useState(false);
  const [autofillData, setAutofillData] = useState<AutofillResponse | null>(null);
  const [touchedFields, setTouchedFields] = useState<Set<string>>(new Set());

  // Initialize form content from initialContent
  useEffect(() => {
    setFormContent(initialContent);
  }, [initialContent]);

  /**
   * Get confidence level styling based on score
   */
  const getConfidenceLevel = (score: number): ConfidenceLevel => {
    if (score > 0.8) {
      return { score, color: 'bg-green-100 text-green-800 border-green-300', label: 'High confidence' };
    } else if (score >= 0.5) {
      return { score, color: 'bg-yellow-100 text-yellow-800 border-yellow-300', label: 'Medium confidence' };
    } else {
      return { score, color: 'bg-red-100 text-red-800 border-red-300', label: 'Low confidence' };
    }
  };

  /**
   * Handle autofill from AI extracted data
   */
  const handleAutofill = async () => {
    setIsAutofilling(true);
    try {
      const result = await apiClient.autofillTemplate<AutofillResponse>(
        sessionId,
        template.template_type
      );

      if (result.success) {
        setAutofillData(result.data);
        setFormContent(result.data.auto_filled_content);
        setIsDirty(true);
      } else {
        console.error('Autofill failed:', result.error);
      }
    } catch (error) {
      console.error('Autofill error:', error);
    } finally {
      setIsAutofilling(false);
    }
  };

  /**
   * Get field value from nested content structure
   */
  const getFieldValue = (sectionId: string, fieldId: string): unknown => {
    const sectionContent = formContent[sectionId] as Record<string, unknown> | undefined;
    return sectionContent?.[fieldId] ?? '';
  };

  /**
   * Update field value in nested content structure
   */
  const setFieldValue = (sectionId: string, fieldId: string, value: unknown) => {
    setFormContent((prev) => ({
      ...prev,
      [sectionId]: {
        ...(prev[sectionId] as Record<string, unknown> | undefined),
        [fieldId]: value,
      },
    }));
    setIsDirty(true);
  };

  /**
   * Mark field as touched (for validation)
   */
  const markFieldTouched = (sectionId: string, fieldId: string) => {
    setTouchedFields((prev) => new Set(prev).add(`${sectionId}.${fieldId}`));
  };

  /**
   * Validate a single field
   */
  const validateField = (section: TemplateSection, field: TemplateField): string | null => {
    const value = getFieldValue(section.id, field.id);

    if (field.required) {
      if (value === '' || value === null || value === undefined) {
        return `${field.label} is required`;
      }

      // Check for empty arrays in multiselect
      if (field.type === 'multiselect' && Array.isArray(value) && value.length === 0) {
        return `${field.label} is required`;
      }
    }

    return null;
  };

  /**
   * Validate all fields
   */
  const validateForm = (): boolean => {
    const newErrors: FieldError[] = [];

    template.structure.sections.forEach((section) => {
      section.fields.forEach((field) => {
        const error = validateField(section, field);
        if (error) {
          newErrors.push({
            sectionId: section.id,
            fieldId: field.id,
            message: error,
          });
        }
      });
    });

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSave = () => {
    if (validateForm()) {
      onSave(formContent);
    }
  };

  /**
   * Get error for specific field
   */
  const getFieldError = (sectionId: string, fieldId: string): string | null => {
    const error = errors.find(
      (e) => e.sectionId === sectionId && e.fieldId === fieldId
    );
    return error?.message ?? null;
  };

  /**
   * Check if field has been touched
   */
  const isFieldTouched = (sectionId: string, fieldId: string): boolean => {
    return touchedFields.has(`${sectionId}.${fieldId}`);
  };

  /**
   * Render individual field based on type
   */
  const renderField = (section: TemplateSection, field: TemplateField) => {
    const value = getFieldValue(section.id, field.id);
    const error = getFieldError(section.id, field.id);
    const isTouched = isFieldTouched(section.id, field.id);
    const showError = isTouched && error;

    const fieldKey = `${section.id}.${field.id}`;

    const commonProps = {
      id: fieldKey,
      onBlur: () => markFieldTouched(section.id, field.id),
    };

    switch (field.type) {
      case 'text':
        return (
          <Input
            {...commonProps}
            type="text"
            value={value as string}
            onChange={(e) => setFieldValue(section.id, field.id, e.target.value)}
            placeholder={field.placeholder ?? ''}
            className={cn(showError && 'border-red-500')}
          />
        );

      case 'textarea':
        return (
          <Textarea
            {...commonProps}
            value={value as string}
            onChange={(e) => setFieldValue(section.id, field.id, e.target.value)}
            placeholder={field.placeholder ?? ''}
            className={cn(showError && 'border-red-500', 'min-h-[120px]')}
          />
        );

      case 'number':
        return (
          <Input
            {...commonProps}
            type="number"
            value={value as string | number}
            onChange={(e) => setFieldValue(section.id, field.id, parseFloat(e.target.value) || 0)}
            placeholder={field.placeholder ?? ''}
            className={cn(showError && 'border-red-500')}
          />
        );

      case 'date':
        return (
          <Input
            {...commonProps}
            type="date"
            value={value as string}
            onChange={(e) => setFieldValue(section.id, field.id, e.target.value)}
            className={cn(showError && 'border-red-500')}
          />
        );

      case 'scale':
        return (
          <div className="space-y-2">
            <Input
              {...commonProps}
              type="number"
              min="1"
              max="10"
              value={value as string | number}
              onChange={(e) => {
                const val = parseInt(e.target.value, 10);
                if (val >= 1 && val <= 10) {
                  setFieldValue(section.id, field.id, val);
                }
              }}
              placeholder="1-10"
              className={cn(showError && 'border-red-500')}
            />
            <div className="text-xs text-gray-500 flex justify-between">
              <span>1 (Low)</span>
              <span>10 (High)</span>
            </div>
          </div>
        );

      case 'select':
        return (
          <Select
            value={value as string}
            onValueChange={(newValue) => setFieldValue(section.id, field.id, newValue)}
          >
            <SelectTrigger className={cn(showError && 'border-red-500')}>
              <SelectValue placeholder={field.placeholder ?? 'Select an option'} />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case 'multiselect':
        const selectedValues = (value as string[]) || [];
        return (
          <div className="space-y-2">
            {field.options?.map((option) => (
              <div key={option} className="flex items-center space-x-2">
                <Checkbox
                  id={`${fieldKey}-${option}`}
                  checked={selectedValues.includes(option)}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      setFieldValue(section.id, field.id, [...selectedValues, option]);
                    } else {
                      setFieldValue(
                        section.id,
                        field.id,
                        selectedValues.filter((v) => v !== option)
                      );
                    }
                  }}
                />
                <label
                  htmlFor={`${fieldKey}-${option}`}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  {option}
                </label>
              </div>
            ))}
          </div>
        );

      case 'checkbox':
        return (
          <div className="flex items-center space-x-2">
            <Checkbox
              {...commonProps}
              id={fieldKey}
              checked={value as boolean}
              onCheckedChange={(checked) => setFieldValue(section.id, field.id, checked)}
            />
            <label
              htmlFor={fieldKey}
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              {field.label}
            </label>
          </div>
        );

      default:
        return <p className="text-sm text-gray-500">Unsupported field type: {field.type}</p>;
    }
  };

  /**
   * Get confidence score for a section
   */
  const getSectionConfidence = (sectionId: string): number | null => {
    return autofillData?.confidence_scores[sectionId] ?? null;
  };

  /**
   * Check if section has missing fields
   */
  const getSectionMissingFields = (sectionId: string): readonly string[] => {
    return autofillData?.missing_fields[sectionId] ?? [];
  };

  const canAutofill = showAutofill && session?.extracted_notes;
  const hasErrors = errors.length > 0;
  const canSave = isDirty && !hasErrors;

  return (
    <div className="space-y-6">
      {/* Header with Autofill Button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{template.name}</h2>
          {template.description && (
            <p className="text-sm text-gray-500 mt-1">{template.description}</p>
          )}
        </div>

        {canAutofill && (
          <Button
            onClick={handleAutofill}
            disabled={isAutofilling}
            variant="outline"
            className="gap-2"
          >
            {isAutofilling ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Autofilling...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Autofill from AI
              </>
            )}
          </Button>
        )}
      </div>

      {/* Unsaved Changes Warning */}
      {isDirty && (
        <div className="flex items-center gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800">
          <AlertCircle className="w-4 h-4" />
          <span>You have unsaved changes</span>
        </div>
      )}

      {/* Sections */}
      {template.structure.sections.map((section) => {
        const confidence = getSectionConfidence(section.id);
        const missingFields = getSectionMissingFields(section.id);
        const confidenceLevel = confidence !== null ? getConfidenceLevel(confidence) : null;

        return (
          <Card key={section.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg">{section.name}</CardTitle>
                  {section.description && (
                    <CardDescription className="mt-1">{section.description}</CardDescription>
                  )}
                </div>

                {/* Confidence Badge */}
                {confidenceLevel && (
                  <Badge
                    variant="outline"
                    className={cn('ml-4', confidenceLevel.color)}
                  >
                    <Check className="w-3 h-3 mr-1" />
                    {confidenceLevel.label} ({Math.round(confidenceLevel.score * 100)}%)
                  </Badge>
                )}
              </div>

              {/* Missing Fields Warning */}
              {missingFields.length > 0 && (
                <div className="mt-3 flex items-start gap-2 p-2 bg-amber-50 border border-amber-200 rounded text-xs text-amber-800">
                  <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium">Manual review needed:</p>
                    <p>{missingFields.join(', ')}</p>
                  </div>
                </div>
              )}
            </CardHeader>

            <CardContent className="space-y-4">
              {section.fields.map((field) => {
                const error = getFieldError(section.id, field.id);
                const isTouched = isFieldTouched(section.id, field.id);
                const showError = isTouched && error;

                // Don't show label for checkbox (it's rendered by the field itself)
                const showLabel = field.type !== 'checkbox';

                return (
                  <div key={field.id} className="space-y-2">
                    {showLabel && (
                      <label
                        htmlFor={`${section.id}.${field.id}`}
                        className="block text-sm font-medium text-gray-700"
                      >
                        {field.label}
                        {field.required && <span className="text-red-500 ml-1">*</span>}
                        {field.ai_mapping && (
                          <Badge variant="outline" className="ml-2 text-xs">
                            AI-mapped
                          </Badge>
                        )}
                      </label>
                    )}

                    {renderField(section, field)}

                    {/* Field Help Text */}
                    {!showError && field.help_text && (
                      <p className="text-xs text-gray-500">{field.help_text}</p>
                    )}

                    {/* Field Error */}
                    {showError && (
                      <div className="flex items-start gap-2 text-sm text-red-600">
                        <AlertCircle className="w-4 h-4 mt-0.5" />
                        <span>{error}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>
        );
      })}

      {/* Form Actions */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t">
        {onCancel && (
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button
          onClick={handleSave}
          disabled={!canSave}
          className="gap-2"
        >
          <Check className="w-4 h-4" />
          Save Note
        </Button>
      </div>

      {/* Validation Summary */}
      {hasErrors && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-start gap-2 text-sm text-red-800">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium">Please fix the following errors:</p>
              <ul className="list-disc list-inside mt-2 space-y-1">
                {errors.map((error, index) => (
                  <li key={index}>{error.message}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
