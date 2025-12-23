'use client';

import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { SessionNote, Template } from '@/lib/types';
import { ChevronDown, ChevronUp, Edit, FileText } from 'lucide-react';
import { formatDateTime } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface SessionNoteCardProps {
  note: SessionNote;
  template?: Template | null;
}

const statusColors = {
  draft: 'bg-yellow-100 text-yellow-800 border-yellow-300 dark:bg-yellow-900/30 dark:text-yellow-300',
  completed: 'bg-green-100 text-green-800 border-green-300 dark:bg-green-900/30 dark:text-green-300',
  signed: 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900/30 dark:text-blue-300',
};

const templateTypeLabels = {
  soap: 'SOAP Note',
  dap: 'DAP Note',
  birp: 'BIRP Note',
  progress: 'Progress Note',
  custom: 'Custom Note',
};

export function SessionNoteCard({ note, template }: SessionNoteCardProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  const renderFieldValue = (value: any): React.ReactNode => {
    if (value == null) return <span className="text-muted-foreground italic">Not filled</span>;
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (Array.isArray(value)) return value.join(', ');
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  const renderPreview = () => {
    if (!template) {
      // Show first 3 keys from content
      const keys = Object.keys(note.content).slice(0, 3);
      return (
        <div className="space-y-2">
          {keys.map((key) => (
            <div key={key} className="text-sm">
              <span className="font-medium">{key}: </span>
              <span className="text-muted-foreground">
                {renderFieldValue(note.content[key])}
              </span>
            </div>
          ))}
          {Object.keys(note.content).length > 3 && (
            <p className="text-xs text-muted-foreground">
              +{Object.keys(note.content).length - 3} more fields
            </p>
          )}
        </div>
      );
    }

    // Show first 2-3 fields from template structure
    const firstSection = template.structure.sections[0];
    const previewFields = firstSection?.fields.slice(0, 3) || [];

    return (
      <div className="space-y-2">
        {previewFields.map((field) => {
          const sectionContent = note.content[firstSection.id] as Record<string, unknown> | undefined;
          const value = sectionContent?.[field.id];
          return (
            <div key={field.id} className="text-sm">
              <span className="font-medium">{field.label}: </span>
              <span className="text-muted-foreground">{renderFieldValue(value)}</span>
            </div>
          );
        })}
        {template.structure.sections.length > 1 && (
          <p className="text-xs text-muted-foreground">
            +{template.structure.sections.length - 1} more sections
          </p>
        )}
      </div>
    );
  };

  const renderFullContent = () => {
    if (!template) {
      // Show all content as key-value pairs
      return (
        <div className="space-y-3 mt-4">
          {Object.entries(note.content).map(([key, value]) => (
            <div key={key} className="text-sm">
              <div className="font-medium mb-1">{key}</div>
              <div className="text-muted-foreground pl-3 border-l-2 border-muted">
                {renderFieldValue(value)}
              </div>
            </div>
          ))}
        </div>
      );
    }

    // Show structured content by sections
    return (
      <div className="space-y-6 mt-4">
        {template.structure.sections.map((section) => {
          const sectionData = (note.content[section.id] as Record<string, unknown>) || {};
          return (
            <div key={section.id}>
              <h4 className="font-semibold text-base mb-3">{section.name}</h4>
              <div className="space-y-3 pl-4 border-l-2 border-muted">
                {section.fields.map((field) => {
                  const value = sectionData[field.id];
                  return (
                    <div key={field.id} className="text-sm">
                      <div className="font-medium text-muted-foreground mb-1">
                        {field.label}
                      </div>
                      <div>{renderFieldValue(value)}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              {template && (
                <Badge variant="secondary" className="text-xs">
                  {templateTypeLabels[template.template_type] || 'Note'}
                </Badge>
              )}
              <Badge
                variant="outline"
                className={cn('text-xs', statusColors[note.status])}
              >
                {note.status.charAt(0).toUpperCase() + note.status.slice(1)}
              </Badge>
            </div>
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="w-4 h-4" />
              {template?.name || 'Session Note'}
            </CardTitle>
            <CardDescription className="text-xs mt-1">
              Created {formatDateTime(note.created_at)}
              {note.signed_at && ` • Signed ${formatDateTime(note.signed_at)}`}
            </CardDescription>
          </div>
          {note.status === 'draft' && (
            <Button variant="outline" size="sm">
              <Edit className="w-3 h-3 mr-1" />
              Edit
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {/* Preview (always visible) */}
        {renderPreview()}

        {/* Expand/Collapse button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-3 w-full"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="w-4 h-4 mr-2" />
              Hide Full Note
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4 mr-2" />
              View Full Note
            </>
          )}
        </Button>

        {/* Full content (conditionally visible) */}
        {isExpanded && renderFullContent()}
      </CardContent>
    </Card>
  );
}
