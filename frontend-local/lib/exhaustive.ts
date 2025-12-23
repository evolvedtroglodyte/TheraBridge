/**
 * Exhaustive checking utilities for TypeScript
 * Provides compile-time guarantees that all cases are handled in switch statements
 * and conditional chains for enums and union types.
 *
 * @example
 * type Status = 'active' | 'inactive' | 'pending';
 *
 * const status: Status = 'active';
 * switch (status) {
 *   case 'active':
 *     console.log('Active');
 *     break;
 *   case 'inactive':
 *     console.log('Inactive');
 *     break;
 *   case 'pending':
 *     console.log('Pending');
 *     break;
 *   default:
 *     assertNever(status); // TypeScript error if a case is missing
 * }
 */

/**
 * Assert that a value should never be reached.
 *
 * This function should be used in the `default` case of exhaustive switch statements
 * or at the end of conditional chains to ensure all possible values are handled.
 *
 * If TypeScript reports an error on this line, it means you haven't handled all
 * possible cases for the type.
 *
 * @param x - A value that should never exist (caught by TypeScript's type system)
 * @returns Never (function throws or returns never type)
 *
 * @throws {Error} With message indicating the exhaustive check failed
 *
 * @example
 * // Example 1: Switch statement
 * type Color = 'red' | 'blue' | 'green';
 * const color: Color = 'red';
 * switch (color) {
 *   case 'red':
 *     return 'Red color';
 *   case 'blue':
 *     return 'Blue color';
 *   case 'green':
 *     return 'Green color';
 *   default:
 *     return assertNever(color);
 * }
 *
 * @example
 * // Example 2: If-else chain
 * type Status = 'loading' | 'success' | 'error';
 * if (status === 'loading') {
 *   return <Spinner />;
 * } else if (status === 'success') {
 *   return <Result />;
 * } else if (status === 'error') {
 *   return <Error />;
 * } else {
 *   return assertNever(status); // TypeScript error if a case is missing
 * }
 *
 * @example
 * // Example 3: With enums
 * enum UserRole {
 *   Admin = 'admin',
 *   User = 'user',
 *   Guest = 'guest',
 * }
 *
 * const role = UserRole.Admin;
 * switch (role) {
 *   case UserRole.Admin:
 *     return 'Admin panel';
 *   case UserRole.User:
 *     return 'User panel';
 *   case UserRole.Guest:
 *     return 'Guest panel';
 *   default:
 *     return assertNever(role);
 * }
 */
export function assertNever(x: never): never {
  throw new Error(`Exhaustive check failed: Unexpected value ${JSON.stringify(x)}`);
}

/**
 * Type guard to check if a value is in a specific set of values.
 * Useful for narrowing union types.
 *
 * @param value - The value to check
 * @param validValues - Array of valid values
 * @returns True if value is in validValues
 *
 * @example
 * type Status = 'active' | 'inactive' | 'pending';
 * const status: Status = 'active';
 *
 * if (isValidValue(status, ['active', 'pending'])) {
 *   // status is now 'active' | 'pending'
 * }
 */
export function isValidValue<T>(
  value: unknown,
  validValues: readonly T[]
): value is T {
  return validValues.includes(value as T);
}

/**
 * Create an exhaustive switch statement handler for a union type.
 * Returns an object where you must provide a handler for each case.
 *
 * @param value - The value to match on
 * @param handlers - Object with handler for each possible value
 * @returns Result from the matched handler
 *
 * @example
 * type Status = 'loading' | 'success' | 'error';
 *
 * const result = match(status, {
 *   loading: () => 'Loading...',
 *   success: () => 'Done!',
 *   error: () => 'Error!',
 * });
 */
export function match<T extends string | number, R>(
  value: T,
  handlers: Record<T, () => R>
): R {
  if (!(value in handlers)) {
    assertNever(value as never);
  }
  return handlers[value]();
}

/**
 * Create an exhaustive switch statement handler with data.
 * Similar to match() but passes data to each handler.
 *
 * @param value - The value to match on
 * @param data - Data to pass to handlers
 * @param handlers - Object with handler for each possible value
 * @returns Result from the matched handler
 *
 * @example
 * type Status = 'loading' | 'success' | 'error';
 *
 * const result = matchWith(status, userData, {
 *   loading: (data) => `Loading ${data.name}...`,
 *   success: (data) => `Loaded ${data.name}!`,
 *   error: (data) => `Error loading ${data.name}!`,
 * });
 */
export function matchWith<T extends string | number, D, R>(
  value: T,
  data: D,
  handlers: Record<T, (data: D) => R>
): R {
  if (!(value in handlers)) {
    assertNever(value as never);
  }
  return handlers[value](data);
}

/**
 * Validate that an object has all required keys from a union type.
 * Useful for creating lookup tables and ensuring complete coverage.
 *
 * @param obj - The object to validate
 * @returns The same object (for chaining)
 *
 * @throws {Error} If object is missing any required keys
 *
 * @example
 * type Status = 'active' | 'inactive' | 'pending';
 *
 * const statusLabels = exhaustive<Status>({
 *   active: 'Active',
 *   inactive: 'Inactive',
 *   pending: 'Pending',
 * });
 *
 * // TypeScript error if you forget a case:
 * const badLabels = exhaustive<Status>({
 *   active: 'Active',
 *   inactive: 'Inactive',
 *   // Error: missing 'pending'
 * });
 */
export function exhaustive<T extends string | number>(
  obj: Record<T, unknown>
): Record<T, unknown> {
  return obj;
}

/**
 * Build an exhaustive configuration object for a union type.
 * Ensures compile-time that all cases are handled.
 *
 * @param config - Configuration object with entries for each case
 * @returns The validated configuration
 *
 * @example
 * type Status = 'loading' | 'success' | 'error';
 *
 * const statusConfig = buildExhaustive<Status>({
 *   loading: { icon: Spinner, label: 'Loading' },
 *   success: { icon: CheckMark, label: 'Success' },
 *   error: { icon: AlertIcon, label: 'Error' },
 * });
 */
export function buildExhaustive<T extends string | number, V>(
  config: Record<T, V>
): Record<T, V> {
  return config;
}
