'use client';

import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useTemplates } from '@/hooks/useTemplates';
import type { Template, TemplateType } from '@/lib/types';
import { FileText, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TemplateSelectorProps {
  onSelectTemplate: (template: Template) => void;
  selectedTemplateId?: string | null;
}

const templateTypeInfo: Record<
  TemplateType,
  { name: string; description: string; badge: string }
> = {
  soap: {
    name: 'SOAP Note',
    description: 'Subjective, Objective, Assessment, Plan - Standard clinical note format',
    badge: 'Clinical',
  },
  dap: {
    name: 'DAP Note',
    description: 'Data, Assessment, Plan - Focused clinical note format',
    badge: 'Clinical',
  },
  birp: {
    name: 'BIRP Note',
    description: 'Behavior, Intervention, Response, Plan - Behavioral health format',
    badge: 'Behavioral',
  },
  progress: {
    name: 'Progress Note',
    description: 'General progress note for ongoing treatment',
    badge: 'General',
  },
  custom: {
    name: 'Custom Template',
    description: 'User-defined template structure',
    badge: 'Custom',
  },
};

export function TemplateSelector({
  onSelectTemplate,
  selectedTemplateId,
}: TemplateSelectorProps) {
  const { templates, isLoading, isError } = useTemplates();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        <p className="ml-3 text-muted-foreground">Loading templates...</p>
      </div>
    );
  }

  if (isError || !templates) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-4">
        <AlertCircle className="w-12 h-12 text-destructive" />
        <p className="text-lg text-muted-foreground">Failed to load templates</p>
        <p className="text-sm text-muted-foreground">Please try again later</p>
      </div>
    );
  }

  if (templates.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 gap-4">
        <FileText className="w-12 h-12 text-muted-foreground" />
        <p className="text-lg text-muted-foreground">No templates available</p>
        <p className="text-sm text-muted-foreground">
          Contact your administrator to set up note templates
        </p>
      </div>
    );
  }

  // Group templates by type
  const groupedTemplates = templates.reduce((acc, template) => {
    if (!acc[template.template_type]) {
      acc[template.template_type] = [];
    }
    acc[template.template_type].push(template);
    return acc;
  }, {} as Record<TemplateType, Template[]>);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2">Choose a Template</h3>
        <p className="text-sm text-muted-foreground">
          Select a note template to begin documenting this session
        </p>
      </div>

      <div className="space-y-4">
        {Object.entries(groupedTemplates).map(([type, typeTemplates]) => {
          const info = templateTypeInfo[type as TemplateType];

          return (
            <div key={type} className="space-y-3">
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-medium">{info.name}</h4>
                <Badge variant="outline" className="text-xs">
                  {info.badge}
                </Badge>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                {typeTemplates.map((template) => (
                  <Card
                    key={template.id}
                    className={cn(
                      'cursor-pointer transition-all hover:border-primary hover:shadow-md',
                      selectedTemplateId === template.id &&
                        'border-primary bg-primary/5 shadow-md'
                    )}
                    onClick={() => onSelectTemplate(template)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-base flex items-center gap-2">
                            {template.name}
                            {template.is_system && (
                              <Badge variant="secondary" className="text-xs">
                                System
                              </Badge>
                            )}
                            {template.is_shared && !template.is_system && (
                              <Badge variant="secondary" className="text-xs">
                                Shared
                              </Badge>
                            )}
                          </CardTitle>
                          {template.description && (
                            <CardDescription className="text-xs mt-1">
                              {template.description}
                            </CardDescription>
                          )}
                        </div>
                        {selectedTemplateId === template.id && (
                          <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0" />
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="pb-3">
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{template.structure.sections.length} sections</span>
                        <Button
                          variant={
                            selectedTemplateId === template.id ? 'default' : 'outline'
                          }
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectTemplate(template);
                          }}
                        >
                          {selectedTemplateId === template.id ? 'Selected' : 'Select'}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
