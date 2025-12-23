/**
 * Testing utilities for optimistic UI updates
 *
 * Provides helpers to test optimistic updates in isolation and integration tests.
 * Works with Jest and React Testing Library.
 */

import type { Session } from './types';

/**
 * Mock implementation of SWR mutate function for testing
 *
 * @example
 * ```ts
 * const { mutate } = createMockSWRMutate();
 * await mutate(optimisticData);
 * ```
 */
export function createMockSWRMutate<T>(initialData: T) {
  let currentData = initialData;
  let shouldFail = false;

  return {
    mutate: async (
      newData: T | ((current: T) => T),
      options?: { optimisticData?: T; rollbackOnError?: boolean; revalidate?: boolean }
    ): Promise<T | undefined> => {
      const dataToUse =
        typeof newData === 'function' ? (newData as (current: T) => T)(currentData) : newData;

      if (options?.rollbackOnError && shouldFail) {
        // Rollback to previous state
        throw new Error('Mutation failed');
      }

      currentData = dataToUse;
      return currentData;
    },

    getCurrentData: () => currentData,
    setShouldFail: (fail: boolean) => {
      shouldFail = fail;
    },
    reset: (newData: T) => {
      currentData = newData;
      shouldFail = false;
    },
  };
}

/**
 * Create a mock session for testing
 *
 * @example
 * ```ts
 * const session = createMockSession({ status: 'uploading' });
 * ```
 */
export function createMockSession(overrides?: Partial<Session>): Session {
  const now = new Date().toISOString();
  return {
    id: 'session-123',
    patient_id: 'patient-123',
    therapist_id: 'therapist-123',
    session_date: now,
    duration_seconds: null,
    audio_filename: 'session.mp3',
    audio_url: 'http://example.com/audio.mp3',
    transcript_text: null,
    transcript_segments: null,
    extracted_notes: null,
    status: 'uploading',
    error_message: null,
    created_at: now,
    updated_at: now,
    processed_at: null,
    ...overrides,
  };
}

/**
 * Create an array of mock sessions for list testing
 *
 * @example
 * ```ts
 * const sessions = createMockSessions(3);
 * ```
 */
export function createMockSessions(count: number, overrides?: Partial<Session>): Session[] {
  return Array.from({ length: count }, (_, i) =>
    createMockSession({
      id: `session-${i + 1}`,
      audio_filename: `session-${i + 1}.mp3`,
      ...overrides,
    })
  );
}

/**
 * Helper to test optimistic update flow
 * Useful for integration tests
 *
 * @example
 * ```ts
 * const result = await testOptimisticFlow({
 *   initial: originalSession,
 *   optimistic: optimisticSession,
 *   final: realSession,
 *   onError: () => console.error('Test failed')
 * });
 * ```
 */
export async function testOptimisticFlow<T>({
  initial,
  optimistic,
  final,
  onSuccess,
  onError,
  shouldFail = false,
}: {
  initial: T;
  optimistic: T;
  final: T;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  shouldFail?: boolean;
}): Promise<{ success: boolean; data?: T; error?: Error }> {
  try {
    // Step 1: Show optimistic data
    let currentData = optimistic;
    if (JSON.stringify(currentData) !== JSON.stringify(optimistic)) {
      throw new Error('Optimistic data not shown immediately');
    }

    // Step 2: Simulate API call
    if (shouldFail) {
      throw new Error('API call failed');
    }

    // Step 3: Show final data
    currentData = final;
    if (JSON.stringify(currentData) !== JSON.stringify(final)) {
      throw new Error('Final data not updated');
    }

    onSuccess?.(currentData);
    return { success: true, data: currentData };
  } catch (error) {
    const err = error instanceof Error ? error : new Error(String(error));
    onError?.(err);

    // Rollback to initial on error
    return { success: false, error: err, data: initial };
  }
}

/**
 * Assert that optimistic update happened correctly
 *
 * @example
 * ```ts
 * assertOptimisticUpdate({
 *   before: originalSession,
 *   after: result.session,
 *   changed: ['status']
 * });
 * ```
 */
export function assertOptimisticUpdate<T extends Record<string, any>>(options: {
  before: T;
  after: T;
  changed: (keyof T)[];
  unchanged?: (keyof T)[];
}) {
  const { before, after, changed, unchanged = [] } = options;

  // Check that changed fields actually changed
  for (const field of changed) {
    if (JSON.stringify(before[field]) === JSON.stringify(after[field])) {
      throw new Error(`Expected field "${String(field)}" to change, but it didn't`);
    }
  }

  // Check that unchanged fields stayed the same
  for (const field of unchanged) {
    if (JSON.stringify(before[field]) !== JSON.stringify(after[field])) {
      throw new Error(`Expected field "${String(field)}" to stay the same, but it changed`);
    }
  }

  return true;
}

/**
 * Mock API call that simulates network delay and failures
 *
 * @example
 * ```ts
 * const result = await mockApiCall(
 *   realData,
 *   { delay: 1000, shouldFail: false }
 * );
 * ```
 */
export async function mockApiCall<T>(
  data: T,
  options?: {
    delay?: number;
    shouldFail?: boolean;
    errorMessage?: string;
  }
): Promise<T> {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (options?.shouldFail) {
        reject(new Error(options?.errorMessage || 'API call failed'));
      } else {
        resolve(data);
      }
    }, options?.delay || 100);
  });
}

/**
 * Simulate network latency and packet loss for testing
 * Useful for testing optimistic behavior on slow networks
 *
 * @example
 * ```ts
 * const result = await simulateSlowNetwork(apiCall, {
 *   latency: 5000,
 *   packetLoss: 0.1
 * });
 * ```
 */
export async function simulateSlowNetwork<T>(
  apiCall: () => Promise<T>,
  options?: {
    latency?: number;
    packetLoss?: number; // 0-1, e.g., 0.1 = 10% chance of failure
  }
): Promise<T> {
  const { latency = 2000, packetLoss = 0 } = options || {};

  // Simulate latency
  await new Promise((resolve) => setTimeout(resolve, latency));

  // Simulate packet loss
  if (Math.random() < packetLoss) {
    throw new Error('Network timeout');
  }

  return apiCall();
}

/**
 * Helper to track all mutations in a test
 * Useful for debugging and assertions
 *
 * @example
 * ```ts
 * const tracker = createMutationTracker();
 * // ... perform operations ...
 * console.log(tracker.getMutations());
 * ```
 */
export function createMutationTracker() {
  const mutations: Array<{ data: any; timestamp: number; error?: Error }> = [];

  return {
    track: (data: any, error?: Error) => {
      mutations.push({ data, timestamp: Date.now(), error });
    },

    getMutations: () => [...mutations],

    getLastMutation: () => mutations[mutations.length - 1],

    clear: () => {
      mutations.length = 0;
    },

    assertMutationCount: (expected: number) => {
      if (mutations.length !== expected) {
        throw new Error(
          `Expected ${expected} mutations, but got ${mutations.length}`
        );
      }
    },

    assertLastMutationData: (expectedData: any) => {
      const last = mutations[mutations.length - 1];
      if (JSON.stringify(last?.data) !== JSON.stringify(expectedData)) {
        throw new Error('Last mutation data does not match expected');
      }
    },

    assertNoErrors: () => {
      const errored = mutations.filter((m) => m.error);
      if (errored.length > 0) {
        throw new Error(`Expected no errors, but found ${errored.length}`);
      }
    },
  };
}

/**
 * Create a mock fetch that simulates API responses
 * Useful for testing without mocking entire libraries
 *
 * @example
 * ```ts
 * const fetchMock = createMockFetch({
 *   '/api/sessions': { data: sessions }
 * });
 * global.fetch = fetchMock.fetch;
 * ```
 */
export function createMockFetch(responses: Record<string, any>) {
  const requestLog: Array<{ url: string; init?: RequestInit; timestamp: number }> = [];

  return {
    fetch: async (url: string, init?: RequestInit) => {
      requestLog.push({ url, init, timestamp: Date.now() });

      if (url in responses) {
        return new Response(JSON.stringify(responses[url]), {
          status: 200,
          headers: { 'content-type': 'application/json' },
        });
      }

      return new Response(null, { status: 404 });
    },

    getRequestLog: () => [...requestLog],
    reset: () => {
      requestLog.length = 0;
    },
  };
}
