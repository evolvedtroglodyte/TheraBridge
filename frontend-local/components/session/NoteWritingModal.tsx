'use client';

import * as React from 'react';
import { Dialog } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { TemplateSelector } from '@/components/templates/TemplateSelector';
import { TemplateEditor } from '@/components/templates/TemplateEditor';
import type { Template, AutofillResponse } from '@/lib/types';
import { ArrowLeft, Save, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface NoteWritingModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  onNoteSaved?: () => void;
}

type Step = 'select' | 'edit';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function NoteWritingModal({
  isOpen,
  onClose,
  sessionId,
  onNoteSaved,
}: NoteWritingModalProps) {
  const [step, setStep] = React.useState<Step>('select');
  const [selectedTemplate, setSelectedTemplate] = React.useState<Template | null>(null);
  const [noteContent, setNoteContent] = React.useState<Record<string, any>>({});
  const [isSaving, setIsSaving] = React.useState(false);
  const [isAutoFilling, setIsAutoFilling] = React.useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = React.useState(false);

  // Reset state when modal closes
  React.useEffect(() => {
    if (!isOpen) {
      setStep('select');
      setSelectedTemplate(null);
      setNoteContent({});
      setHasUnsavedChanges(false);
    }
  }, [isOpen]);

  const handleSelectTemplate = (template: Template) => {
    setSelectedTemplate(template);
    setStep('edit');
  };

  const handleBackToSelection = () => {
    if (hasUnsavedChanges) {
      const confirmed = window.confirm(
        'You have unsaved changes. Are you sure you want to go back?'
      );
      if (!confirmed) return;
    }
    setStep('select');
    setSelectedTemplate(null);
    setNoteContent({});
    setHasUnsavedChanges(false);
  };

  const handleContentChange = (content: Record<string, any>) => {
    setNoteContent(content);
    setHasUnsavedChanges(true);
  };

  const handleAutoFill = async () => {
    if (!selectedTemplate) return;

    setIsAutoFilling(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/sessions/${sessionId}/notes/autofill`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            template_type: selectedTemplate.template_type,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to auto-fill template');
      }

      const data: AutofillResponse = await response.json();

      // Merge auto-filled content with existing content
      setNoteContent((prev) => ({
        ...data.auto_filled_content,
        ...prev, // Keep user's manual edits
      }));

      toast.success('Auto-fill complete', {
        description: 'Template has been filled with AI-extracted data',
      });
    } catch (error) {
      console.error('Auto-fill error:', error);
      toast.error('Auto-fill failed', {
        description: 'Could not auto-fill template. Please fill manually.',
      });
    } finally {
      setIsAutoFilling(false);
    }
  };

  const handleSave = async () => {
    if (!selectedTemplate) return;

    setIsSaving(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/sessions/${sessionId}/notes`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            template_id: selectedTemplate.id,
            content: noteContent,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to save note');
      }

      toast.success('Note saved', {
        description: 'Your session note has been saved successfully',
      });

      setHasUnsavedChanges(false);
      onNoteSaved?.();
      onClose();
    } catch (error) {
      console.error('Save error:', error);
      toast.error('Save failed', {
        description: 'Could not save note. Please try again.',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleClose = () => {
    if (hasUnsavedChanges) {
      const confirmed = window.confirm(
        'You have unsaved changes. Are you sure you want to close?'
      );
      if (!confirmed) return;
    }
    onClose();
  };

  return (
    <Dialog
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) handleClose();
      }}
      title={step === 'select' ? 'Write Session Note' : selectedTemplate?.name}
      description={
        step === 'select'
          ? 'Choose a template to document this session'
          : 'Fill out the template fields'
      }
      size={step === 'select' ? 'lg' : 'xl'}
      showClose={true}
    >
      <div className="space-y-6">
        {/* Step 1: Template Selection */}
        {step === 'select' && (
          <>
            <TemplateSelector
              onSelectTemplate={handleSelectTemplate}
              selectedTemplateId={selectedTemplate?.id}
            />
            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button variant="outline" onClick={onClose}>
                Cancel
              </Button>
            </div>
          </>
        )}

        {/* Step 2: Template Editor */}
        {step === 'edit' && selectedTemplate && (
          <>
            <TemplateEditor
              template={selectedTemplate}
              initialContent={noteContent}
              onContentChange={handleContentChange}
              onAutoFill={handleAutoFill}
              isAutoFilling={isAutoFilling}
              showAutoFill={true}
            />
            <div className="flex justify-between gap-3 pt-4 border-t">
              <Button
                variant="outline"
                onClick={handleBackToSelection}
                disabled={isSaving || isAutoFilling}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Templates
              </Button>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={handleClose}
                  disabled={isSaving || isAutoFilling}
                >
                  Cancel
                </Button>
                <Button onClick={handleSave} disabled={isSaving || isAutoFilling}>
                  {isSaving ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Save Note
                    </>
                  )}
                </Button>
              </div>
            </div>
          </>
        )}
      </div>
    </Dialog>
  );
}
