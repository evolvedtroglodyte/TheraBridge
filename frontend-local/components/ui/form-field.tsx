'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Input, type ValidationState } from './input';
import type { ValidationRule } from '@/lib/validation';
import { validateField, getFirstError, hasError, isSuccess } from '@/lib/validation';

interface FormFieldProps {
  /** Field name/identifier */
  name: string;
  /** Field label */
  label: string;
  /** Field type (text, email, password, etc.) */
  type?: string;
  /** Field value */
  value: string;
  /** Called when field value changes */
  onChange: (value: string) => void;
  /** Called when field loses focus */
  onBlur?: () => void;
  /** Validation rules for this field */
  rules?: ValidationRule[];
  /** Placeholder text */
  placeholder?: string;
  /** Whether field is required */
  required?: boolean;
  /** Whether to show validation errors */
  showErrors?: boolean;
  /** Whether to show validation icon */
  showValidationIcon?: boolean;
  /** Whether to enable real-time validation as user types */
  validateOnChange?: boolean;
  /** Whether to validate on blur */
  validateOnBlur?: boolean;
  /** Help text to show below field */
  helpText?: string;
  /** Additional CSS classes for the wrapper */
  className?: string;
  /** Additional CSS classes for the input */
  inputClassName?: string;
  /** Disabled state */
  disabled?: boolean;
  /** Auto-focus */
  autoFocus?: boolean;
}

interface FieldState {
  isValid: boolean;
  errors: string[];
  isDirty: boolean;
  isTouched: boolean;
}

/**
 * FormField component with integrated validation
 *
 * Features:
 * - Real-time validation as user types
 * - Field-specific error messages
 * - Success state indicators
 * - Touch state tracking
 * - Customizable validation rules
 *
 * @example
 * ```tsx
 * <FormField
 *   name="email"
 *   label="Email"
 *   type="email"
 *   value={email}
 *   onChange={setEmail}
 *   rules={emailRules}
 *   validateOnChange
 *   showErrors
 * />
 * ```
 */
export function FormField({
  name,
  label,
  type = 'text',
  value,
  onChange,
  onBlur,
  rules = [],
  placeholder,
  required = false,
  showErrors = true,
  showValidationIcon = true,
  validateOnChange = true,
  validateOnBlur = true,
  helpText,
  className,
  inputClassName,
  disabled = false,
  autoFocus = false,
}: FormFieldProps) {
  const [fieldState, setFieldState] = useState<FieldState>({
    isValid: true,
    errors: [],
    isDirty: false,
    isTouched: false,
  });

  // Validate field
  const validateFieldValue = useCallback(
    (fieldValue: string) => {
      const { isValid, errors } = validateField(fieldValue, rules);
      return { isValid, errors };
    },
    [rules]
  );

  // Handle change event
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    onChange(newValue);

    if (validateOnChange) {
      const { isValid, errors } = validateFieldValue(newValue);
      setFieldState((prev) => ({
        ...prev,
        isValid,
        errors,
        isDirty: newValue.length > 0,
      }));
    } else {
      // Just mark as dirty if not validating on change
      setFieldState((prev) => ({
        ...prev,
        isDirty: newValue.length > 0,
      }));
    }
  };

  // Handle blur event
  const handleBlur = () => {
    setFieldState((prev) => ({
      ...prev,
      isTouched: true,
    }));

    if (validateOnBlur && !validateOnChange) {
      const { isValid, errors } = validateFieldValue(value);
      setFieldState((prev) => ({
        ...prev,
        isValid,
        errors,
      }));
    }

    onBlur?.();
  };

  // Update validation when value changes externally or rules change
  useEffect(() => {
    if (validateOnChange && fieldState.isDirty) {
      const { isValid, errors } = validateFieldValue(value);
      setFieldState((prev) => ({
        ...prev,
        isValid,
        errors,
      }));
    }
  }, [rules, validateOnChange, validateFieldValue, value, fieldState.isDirty]);

  // Determine validation state for UI
  let validationState: ValidationState = 'idle';
  if (showValidationIcon && fieldState.isDirty) {
    if (fieldState.isValid) {
      validationState = 'valid';
    } else if (fieldState.errors.length > 0) {
      validationState = 'error';
    }
  }

  const errorMessage = getFirstError(fieldState);
  const shouldShowErrors = showErrors && fieldState.isDirty && !fieldState.isValid;

  return (
    <div className={cn('w-full', className)}>
      <div className="space-y-2">
        {/* Label */}
        <label
          htmlFor={name}
          className="block text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>

        {/* Input with validation state */}
        <Input
          id={name}
          name={name}
          type={type}
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={disabled}
          autoFocus={autoFocus}
          validationState={validationState}
          showValidationIcon={showValidationIcon}
          className={inputClassName}
          aria-invalid={fieldState.isDirty && !fieldState.isValid}
          aria-describedby={
            shouldShowErrors || helpText ? `${name}-helper` : undefined
          }
        />

        {/* Error message */}
        {shouldShowErrors && errorMessage && (
          <div
            id={`${name}-helper`}
            className="flex items-start gap-2 text-sm text-red-600 dark:text-red-400"
          >
            <span className="mt-0.5">•</span>
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Help text */}
        {!shouldShowErrors && helpText && (
          <p
            id={`${name}-helper`}
            className="text-xs text-gray-500 dark:text-gray-400"
          >
            {helpText}
          </p>
        )}

        {/* Success message when field is valid and dirty */}
        {isSuccess(fieldState) && (
          <div className="flex items-start gap-2 text-sm text-green-600 dark:text-green-400">
            <span className="mt-0.5">✓</span>
            <span>Looks good!</span>
          </div>
        )}
      </div>
    </div>
  );
}

