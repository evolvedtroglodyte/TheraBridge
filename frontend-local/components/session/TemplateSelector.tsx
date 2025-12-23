'use client';

import { useTemplates } from '@/hooks/useTemplates';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, FileText, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Template, TemplateType } from '@/lib/types';

/**
 * Props for the TemplateSelector component
 */
export interface TemplateSelectorProps {
  /** Currently selected template ID (null if none selected) */
  value: string | null;
  /** Callback when a template is selected */
  onChange: (templateId: string, templateType: TemplateType) => void;
  /** Optional session ID for context */
  sessionId?: string;
}

/**
 * Returns a human-readable label for a template type
 */
function getTemplateTypeLabel(type: TemplateType): string {
  const labels: Record<TemplateType, string> = {
    soap: 'SOAP',
    dap: 'DAP',
    birp: 'BIRP',
    progress: 'Progress Note',
    custom: 'Custom',
  };
  return labels[type] || type.toUpperCase();
}

/**
 * Returns the badge variant for template type
 */
function getTemplateTypeBadgeVariant(type: TemplateType): 'default' | 'secondary' | 'outline' {
  // Standard clinical templates get primary color
  if (type === 'soap' || type === 'dap' || type === 'birp' || type === 'progress') {
    return 'default';
  }
  // Custom templates get secondary color
  return 'secondary';
}

/**
 * TemplateSelector Component
 *
 * Displays a grid of available note templates for selection.
 * Groups templates by system vs custom, showing template type, description,
 * and section count. Highlights the currently selected template.
 *
 * @example
 * ```tsx
 * <TemplateSelector
 *   value={selectedTemplateId}
 *   onChange={(id, type) => setSelectedTemplate({ id, type })}
 *   sessionId={session.id}
 * />
 * ```
 */
export function TemplateSelector({ value, onChange, sessionId }: TemplateSelectorProps) {
  const { templates, isLoading, isError, error } = useTemplates();

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">Loading templates...</span>
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Failed to Load Templates</CardTitle>
          <CardDescription>
            {error?.message || 'Unable to fetch available templates. Please try again.'}
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Empty state
  if (!templates || templates.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No Templates Available</CardTitle>
          <CardDescription>
            No note templates are currently available. Please contact your administrator.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Separate system and custom templates
  const systemTemplates = templates.filter((t) => t.is_system);
  const customTemplates = templates.filter((t) => !t.is_system);

  return (
    <div className="space-y-6">
      {/* System Templates Section */}
      {systemTemplates.length > 0 && (
        <div className="space-y-3">
          <div>
            <h3 className="text-lg font-semibold">System Templates</h3>
            <p className="text-sm text-muted-foreground">
              Standard clinical note templates
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {systemTemplates.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                isSelected={value === template.id}
                onSelect={() => onChange(template.id, template.template_type)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Custom Templates Section */}
      {customTemplates.length > 0 && (
        <div className="space-y-3">
          <div>
            <h3 className="text-lg font-semibold">Custom Templates</h3>
            <p className="text-sm text-muted-foreground">
              Templates created by you or shared by colleagues
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {customTemplates.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                isSelected={value === template.id}
                onSelect={() => onChange(template.id, template.template_type)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Individual template card component
 */
interface TemplateCardProps {
  template: Template;
  isSelected: boolean;
  onSelect: () => void;
}

function TemplateCard({ template, isSelected, onSelect }: TemplateCardProps) {
  const sectionCount = template.structure.sections.length;

  return (
    <Card
      className={cn(
        'cursor-pointer transition-all hover:shadow-md',
        isSelected && 'border-primary ring-2 ring-primary ring-offset-2'
      )}
      onClick={onSelect}
    >
      <CardHeader className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-muted-foreground shrink-0" />
            <CardTitle className="text-base line-clamp-1">{template.name}</CardTitle>
          </div>
          {isSelected && (
            <CheckCircle2 className="w-5 h-5 text-primary shrink-0" />
          )}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant={getTemplateTypeBadgeVariant(template.template_type)}>
            {getTemplateTypeLabel(template.template_type)}
          </Badge>
          {template.is_system && (
            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
              System
            </Badge>
          )}
          {!template.is_system && template.is_shared && (
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
              Shared
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-2">
        {template.description && (
          <CardDescription className="line-clamp-2 text-xs">
            {template.description}
          </CardDescription>
        )}
        <div className="flex items-center justify-between pt-2 border-t">
          <span className="text-xs text-muted-foreground">
            {sectionCount} {sectionCount === 1 ? 'section' : 'sections'}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
