/**
 * Discriminated unions for async loading states
 * Provides type-safe handling of loading, success, and error states
 */

import { assertNever } from './exhaustive';

/**
 * Represents the state of an asynchronous operation
 *
 * @template T - The type of successful data
 * @template E - The type of error (defaults to Error)
 *
 * @example
 * type UserState = AsyncState<User>;
 *
 * const state: UserState = { status: 'success', data: user };
 *
 * if (state.status === 'success') {
 *   console.log(state.data); // TypeScript knows state.data exists
 * }
 */
export type AsyncState<T, E = Error> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: E };

/**
 * Create an idle state (initial/unstarted state)
 *
 * @example
 * const state = idle<User>();
 */
export function idle<T, E = Error>(): AsyncState<T, E> {
  return { status: 'idle' };
}

/**
 * Create a loading state
 *
 * @example
 * const state = loading<User>();
 */
export function loading<T, E = Error>(): AsyncState<T, E> {
  return { status: 'loading' };
}

/**
 * Create a success state with data
 *
 * @param data - The successful data
 *
 * @example
 * const state = success(user);
 */
export function success<T, E = Error>(data: T): AsyncState<T, E> {
  return { status: 'success', data };
}

/**
 * Create an error state with an error
 *
 * @param error - The error object
 *
 * @example
 * const state = error(new Error('Failed to fetch user'));
 */
export function error<T, E = Error>(error: E): AsyncState<T, E> {
  return { status: 'error', error };
}

/**
 * Type guard to check if state is idle
 *
 * @example
 * if (isIdle(state)) {
 *   return <InitialPrompt />;
 * }
 */
export function isIdle<T, E = Error>(
  state: AsyncState<T, E>
): state is { status: 'idle' } {
  return state.status === 'idle';
}

/**
 * Type guard to check if state is loading
 *
 * @example
 * if (isLoading(state)) {
 *   return <Spinner />;
 * }
 */
export function isLoading<T, E = Error>(
  state: AsyncState<T, E>
): state is { status: 'loading' } {
  return state.status === 'loading';
}

/**
 * Type guard to check if state is success
 *
 * @example
 * if (isSuccess(state)) {
 *   return <UserCard user={state.data} />;
 * }
 */
export function isSuccess<T, E = Error>(
  state: AsyncState<T, E>
): state is { status: 'success'; data: T } {
  return state.status === 'success';
}

/**
 * Type guard to check if state is error
 *
 * @example
 * if (isError(state)) {
 *   return <ErrorAlert message={state.error.message} />;
 * }
 */
export function isError<T, E = Error>(
  state: AsyncState<T, E>
): state is { status: 'error'; error: E } {
  return state.status === 'error';
}

/**
 * Check if state is in a loading or idle state (not final)
 *
 * @example
 * if (isPending(state)) {
 *   return <Skeleton />;
 * }
 */
export function isPending<T, E = Error>(
  state: AsyncState<T, E>
): state is { status: 'idle' } | { status: 'loading' } {
  return state.status === 'idle' || state.status === 'loading';
}

/**
 * Check if state is in a final state (success or error)
 *
 * @example
 * if (isSettled(state)) {
 *   return <Content />;
 * }
 */
export function isSettled<T, E = Error>(
  state: AsyncState<T, E>
): state is { status: 'success'; data: T } | { status: 'error'; error: E } {
  return state.status === 'success' || state.status === 'error';
}

/**
 * Extract data if success, otherwise return undefined
 *
 * @example
 * const user = getData(state);
 * if (user) {
 *   console.log(user.name);
 * }
 */
export function getData<T, E = Error>(
  state: AsyncState<T, E>
): T | undefined {
  return isSuccess(state) ? state.data : undefined;
}

/**
 * Extract error if error state, otherwise return undefined
 *
 * @example
 * const err = getError(state);
 * if (err) {
 *   console.error(err.message);
 * }
 */
export function getError<T, E = Error>(
  state: AsyncState<T, E>
): E | undefined {
  return isError(state) ? state.error : undefined;
}

/**
 * Transform success data using a mapping function
 * Other states pass through unchanged
 *
 * @param state - The async state
 * @param fn - Function to transform the data
 *
 * @example
 * const userNames = map(userState, user => user.name);
 */
export function map<T, U, E = Error>(
  state: AsyncState<T, E>,
  fn: (data: T) => U
): AsyncState<U, E> {
  if (isSuccess(state)) {
    return success(fn(state.data));
  }
  return state as AsyncState<U, E>;
}

/**
 * Transform async state with a function that returns a new async state
 * Flattens nested AsyncState results
 *
 * @param state - The async state
 * @param fn - Function that transforms data into a new async state
 *
 * @example
 * const nested = flatMap(userState, user => fetchUserPosts(user.id));
 */
export function flatMap<T, U, E = Error>(
  state: AsyncState<T, E>,
  fn: (data: T) => AsyncState<U, E>
): AsyncState<U, E> {
  if (isSuccess(state)) {
    return fn(state.data);
  }
  return state as AsyncState<U, E>;
}

/**
 * Match on all possible states and execute the corresponding handler
 * Ensures exhaustive handling of all cases
 *
 * @param state - The async state
 * @param handlers - Object with handler functions for each state
 *
 * @example
 * const content = match(userState, {
 *   idle: () => <InitialPrompt />,
 *   loading: () => <Spinner />,
 *   success: (user) => <UserCard user={user} />,
 *   error: (err) => <ErrorAlert error={err} />,
 * });
 */
export function match<T, E = Error, R = React.ReactNode>(
  state: AsyncState<T, E>,
  handlers: {
    idle: () => R;
    loading: () => R;
    success: (data: T) => R;
    error: (error: E) => R;
  }
): R {
  switch (state.status) {
    case 'idle':
      return handlers.idle();
    case 'loading':
      return handlers.loading();
    case 'success':
      return handlers.success(state.data);
    case 'error':
      return handlers.error(state.error);
    default:
      return assertNever(state);
  }
}

/**
 * Combine multiple async states into a single state
 * Returns loading if any are loading
 * Returns error if any are errors (first error encountered)
 * Returns success with all data if all are success
 *
 * @param states - Array of async states to combine
 *
 * @example
 * const combined = combine([userState, postsState, commentsState]);
 *
 * if (isSuccess(combined)) {
 *   const [user, posts, comments] = combined.data;
 * }
 */
export function combine<T extends readonly AsyncState<unknown, Error>[]>(
  states: T
): AsyncState<
  {
    [K in keyof T]: T[K] extends AsyncState<infer U> ? U : never;
  },
  Error
> {
  // Check for any loading states
  if (states.some(isLoading)) {
    return loading();
  }

  // Check for any error states
  for (const state of states) {
    if (isError(state)) {
      return error(state.error);
    }
  }

  // All must be success or idle
  const data = states.map((state) =>
    isSuccess(state) ? state.data : undefined
  );

  return success(data as any);
}

/**
 * Reset an async state back to idle
 * Useful for retry scenarios or clearing state
 *
 * @param state - The async state to reset
 *
 * @example
 * const newState = reset(state);
 */
export function reset<T, E = Error>(
  state: AsyncState<T, E>
): AsyncState<T, E> {
  return idle();
}

/**
 * Get a user-friendly error message from an error state
 * Falls back to generic message if error has no message property
 *
 * @param state - The async state
 * @param defaultMessage - Fallback message if state is not error
 *
 * @example
 * const message = getErrorMessage(state, 'Something went wrong');
 * console.log(message);
 */
export function getErrorMessage<T, E = Error>(
  state: AsyncState<T, E>,
  defaultMessage: string = 'An error occurred'
): string {
  if (isError(state)) {
    if (state.error instanceof Error) {
      return state.error.message;
    }
    return String(state.error);
  }
  return defaultMessage;
}

/**
 * Retry helper - resets state and optionally executes retry logic
 *
 * @param currentState - The current async state
 * @param onRetry - Optional async function to retry
 *
 * @example
 * const retryState = await retryAsync(state, () => fetchUser(userId));
 *
 * // Or just reset to idle:
 * const resetState = retryAsync(state);
 */
export async function retryAsync<T, E = Error>(
  currentState: AsyncState<T, E>,
  onRetry?: () => Promise<T>
): Promise<AsyncState<T, E>> {
  // If no retry function, just reset to idle
  if (!onRetry) {
    return idle();
  }

  // Execute retry function
  try {
    const data = await onRetry();
    return success(data);
  } catch (err) {
    return error(err as E);
  }
}

/**
 * Create a middleware function for use with React hooks or state managers
 * Tracks loading state while executing async functions
 *
 * @param fn - Async function to execute
 *
 * @example
 * const { execute, state } = useAsync(fetchUser);
 *
 * await execute(userId);
 *
 * if (isSuccess(state.value)) {
 *   console.log(state.value.data);
 * }
 */
export function createAsyncExecutor<T, E = Error>(
  fn: (...args: any[]) => Promise<T>
): {
  execute: (...args: Parameters<typeof fn>) => Promise<AsyncState<T, E>>;
} {
  return {
    async execute(...args) {
      try {
        const data = await fn(...args);
        return success(data);
      } catch (err) {
        return error(err as E);
      }
    },
  };
}

/**
 * Check if data exists (regardless of state status)
 * Useful for conditionally rendering cached data while loading
 *
 * @example
 * if (hasData(previousState)) {
 *   return <CachedUserCard user={previousState.data} isLoading />;
 * }
 */
export function hasData<T, E = Error>(
  state: AsyncState<T, E>
): state is { status: 'success'; data: T } | (AsyncState<T, E> & { _cached?: T }) {
  return isSuccess(state);
}

/**
 * Preserve previous data while in loading state
 * Useful for optimistic updates and better UX
 *
 * @param prevState - Previous async state (may have data)
 * @param nextState - New async state to apply
 *
 * @example
 * const state = preserveData(previousState, { status: 'loading' });
 * // Even though loading, state.data might still have the old data
 */
export function preserveData<T, E = Error>(
  prevState: AsyncState<T, E>,
  nextState: AsyncState<T, E>
): AsyncState<T, E> & { _cached?: T } {
  const prevData = getData(prevState);

  if (nextState.status === 'loading' && prevData) {
    return { ...nextState, _cached: prevData } as any;
  }

  return nextState as any;
}

/**
 * Get data from current state or cached data if available
 *
 * @example
 * const user = getDataOrCached(state);
 * if (user) {
 *   return <UserCard user={user} />;
 * }
 */
export function getDataOrCached<T, E = Error>(
  state: (AsyncState<T, E> & { _cached?: T }) | AsyncState<T, E>
): T | undefined {
  const currentData = getData(state);
  if (currentData !== undefined) {
    return currentData;
  }

  // Check for cached data
  if ('_cached' in state && state._cached !== undefined) {
    return state._cached;
  }

  return undefined;
}
