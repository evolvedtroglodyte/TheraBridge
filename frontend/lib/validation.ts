/**
 * Form validation utilities and rules
 */

export type ValidationRule = {
  validate: (value: string) => boolean;
  message: string;
};

export type FieldValidation = {
  isValid: boolean;
  errors: string[];
  isDirty: boolean;
};

export type ValidationState = {
  [fieldName: string]: FieldValidation;
};

/**
 * Email validation regex pattern
 */
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Password strength validation regex
 */
const PASSWORD_STRONG_PATTERN = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;

/**
 * Validation rules for email field
 */
export const emailRules: ValidationRule[] = [
  {
    validate: (value) => value.trim().length > 0,
    message: 'Email is required',
  },
  {
    validate: (value) => EMAIL_PATTERN.test(value),
    message: 'Please enter a valid email address',
  },
];

/**
 * Validation rules for password field
 */
export const passwordRules: ValidationRule[] = [
  {
    validate: (value) => value.length > 0,
    message: 'Password is required',
  },
  {
    validate: (value) => value.length >= 8,
    message: 'Password must be at least 8 characters long',
  },
];

/**
 * Validation rules for password with strength requirements
 */
export const passwordStrongRules: ValidationRule[] = [
  {
    validate: (value) => value.length > 0,
    message: 'Password is required',
  },
  {
    validate: (value) => value.length >= 8,
    message: 'Password must be at least 8 characters long',
  },
  {
    validate: (value) => /[a-z]/.test(value),
    message: 'Password must contain lowercase letters',
  },
  {
    validate: (value) => /[A-Z]/.test(value),
    message: 'Password must contain uppercase letters',
  },
  {
    validate: (value) => /\d/.test(value),
    message: 'Password must contain at least one number',
  },
];

/**
 * Validation rules for full name field
 */
export const fullNameRules: ValidationRule[] = [
  {
    validate: (value) => value.trim().length > 0,
    message: 'Full name is required',
  },
  {
    validate: (value) => value.trim().length >= 2,
    message: 'Name must be at least 2 characters long',
  },
  {
    validate: (value) => /^[a-zA-Z\s'-]+$/.test(value.trim()),
    message: 'Name can only contain letters, spaces, hyphens, and apostrophes',
  },
];

/**
 * Validation rules for first name field
 */
export const firstNameRules: ValidationRule[] = [
  {
    validate: (value) => value.trim().length > 0,
    message: 'First name is required',
  },
  {
    validate: (value) => value.trim().length >= 2,
    message: 'First name must be at least 2 characters long',
  },
  {
    validate: (value) => /^[a-zA-Z\s'-]+$/.test(value.trim()),
    message: 'First name can only contain letters, spaces, hyphens, and apostrophes',
  },
];

/**
 * Validation rules for last name field
 */
export const lastNameRules: ValidationRule[] = [
  {
    validate: (value) => value.trim().length > 0,
    message: 'Last name is required',
  },
  {
    validate: (value) => value.trim().length >= 2,
    message: 'Last name must be at least 2 characters long',
  },
  {
    validate: (value) => /^[a-zA-Z\s'-]+$/.test(value.trim()),
    message: 'Last name can only contain letters, spaces, hyphens, and apostrophes',
  },
];

/**
 * Validate a field against a set of rules
 * @param value - The field value to validate
 * @param rules - Array of validation rules to check
 * @returns Object with validation results
 */
export function validateField(
  value: string,
  rules: ValidationRule[]
): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];

  for (const rule of rules) {
    if (!rule.validate(value)) {
      errors.push(rule.message);
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Validate multiple fields at once
 * @param fields - Object with field names and their values
 * @param rulesMap - Map of field names to their validation rules
 * @returns Validation state for all fields
 */
export function validateFields(
  fields: Record<string, string>,
  rulesMap: Record<string, ValidationRule[]>
): ValidationState {
  const validationState: ValidationState = {};

  for (const [fieldName, value] of Object.entries(fields)) {
    const rules = rulesMap[fieldName] || [];
    const { isValid, errors } = validateField(value, rules);

    validationState[fieldName] = {
      isValid,
      errors,
      isDirty: value.length > 0,
    };
  }

  return validationState;
}

/**
 * Check if all fields in validation state are valid
 */
export function isAllValid(validationState: ValidationState): boolean {
  return Object.values(validationState).every((field) => field.isValid);
}

/**
 * Get the first error message for a field
 */
export function getFirstError(fieldValidation: FieldValidation): string | null {
  return fieldValidation.errors.length > 0 ? fieldValidation.errors[0] : null;
}

/**
 * Check if a field is in error state (dirty and has errors)
 */
export function hasError(fieldValidation: FieldValidation): boolean {
  return fieldValidation.isDirty && !fieldValidation.isValid;
}

/**
 * Check if a field is in success state (dirty and valid)
 */
export function isSuccess(fieldValidation: FieldValidation): boolean {
  return fieldValidation.isDirty && fieldValidation.isValid;
}
