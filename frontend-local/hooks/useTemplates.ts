import { useSWRTyped, type UseSWRHookReturn } from '@/lib/swr-wrapper';
import { fetcher, type ApiError } from '@/lib/api';
import type { Template, TemplateType } from '@/lib/types';

/**
 * Configuration options for the useTemplates hook
 */
export interface UseTemplatesOptions {
  /** Filter by template type (soap, dap, birp, progress, custom) */
  templateType?: TemplateType | null;
  /** Include shared templates from other users (default: true) */
  includeShared?: boolean;
}

/**
 * Extended return type for useTemplates
 */
export interface UseTemplatesReturn extends UseSWRHookReturn<Template[], ApiError> {
  /** The templates data (alias for `data`) */
  templates: Template[] | undefined;
}

/**
 * Fetches the list of available note templates for the current user
 *
 * Returns system templates + user's custom templates + shared templates (if requested).
 * Templates are sorted with system templates first, then by creation date (newest first).
 *
 * @param options - Configuration options (template type filter, include shared)
 * @returns Hook return with templates data, loading state, error state, and refresh function
 *
 * @example
 * ```ts
 * // Fetch all templates
 * const { templates, isLoading } = useTemplates();
 *
 * // Fetch only SOAP templates
 * const { templates } = useTemplates({ templateType: 'soap' });
 *
 * // Fetch only system + user's templates (exclude shared)
 * const { templates } = useTemplates({ includeShared: false });
 * ```
 */
export function useTemplates(
  options?: UseTemplatesOptions
): UseTemplatesReturn {
  // Build query string
  const params = new URLSearchParams();
  if (options?.templateType) {
    params.append('template_type', options.templateType);
  }
  if (options?.includeShared !== undefined) {
    params.append('include_shared', String(options.includeShared));
  }

  const queryString = params.toString();
  const url = `/api/v1/templates${queryString ? `?${queryString}` : ''}`;

  const swr = useSWRTyped<Template[], ApiError>(url, fetcher, {
    // Cache for 5 minutes - templates don't change frequently
    dedupingInterval: 300000,
    // Revalidate on focus to pick up changes from other tabs
    revalidateOnFocus: true,
    // Revalidate on reconnect for network resilience
    revalidateOnReconnect: true,
  });

  return {
    templates: swr.data,
    data: swr.data,
    isLoading: swr.isLoading,
    isError: !!swr.error,
    error: swr.error,
    refresh: swr.mutate,
  };
}
