'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';
import { Code2 } from 'lucide-react';

export function ConfirmationDialogDemo() {
  const [showDefault, setShowDefault] = useState(false);
  const [showDestructive, setShowDestructive] = useState(false);
  const [showWarning, setShowWarning] = useState(false);
  const [showWithWarningText, setShowWithWarningText] = useState(false);

  const handleSimpleConfirm = async () => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    console.log('Confirmed!');
  };

  const handleDangerousConfirm = async () => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    console.log('Session deleted!');
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Confirmation Dialog Examples</h2>
        <p className="text-muted-foreground">
          Interactive examples of confirmation dialogs for destructive and important actions.
        </p>
      </div>

      {/* Default Dialog */}
      <Card>
        <CardHeader>
          <CardTitle>Default Confirmation</CardTitle>
          <CardDescription>For standard confirmations</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button onClick={() => setShowDefault(true)}>
            Open Default Dialog
          </Button>

          <div className="bg-muted p-4 rounded-lg border">
            <p className="text-sm font-mono text-muted-foreground mb-2">Usage:</p>
            <code className="text-xs text-foreground block whitespace-pre-wrap break-words">
{`<ConfirmationDialog
  isOpen={showDialog}
  onOpenChange={setShowDialog}
  title="Confirm Action"
  description="Are you sure?"
  onConfirm={() => handleAction()}
  confirmLabel="Confirm"
  cancelLabel="Cancel"
/>`}
            </code>
          </div>
        </CardContent>
      </Card>

      {/* Destructive Dialog */}
      <Card>
        <CardHeader>
          <CardTitle>Destructive Action</CardTitle>
          <CardDescription>For deleting or dangerous operations</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button variant="destructive" onClick={() => setShowDestructive(true)}>
            Open Destructive Dialog
          </Button>

          <div className="bg-muted p-4 rounded-lg border">
            <p className="text-sm font-mono text-muted-foreground mb-2">Usage:</p>
            <code className="text-xs text-foreground block whitespace-pre-wrap break-words">
{`<ConfirmationDialog
  isOpen={showDialog}
  onOpenChange={setShowDialog}
  title="Delete Session?"
  description="Are you sure you want to delete?"
  onConfirm={() => handleDelete()}
  variant="destructive"
  isDangerous={true}
  confirmLabel="Delete"
  cancelLabel="Cancel"
/>`}
            </code>
          </div>
        </CardContent>
      </Card>

      {/* Warning Dialog with Warning Text */}
      <Card>
        <CardHeader>
          <CardTitle>Warning with Additional Context</CardTitle>
          <CardDescription>With warning text for destructive actions</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button variant="outline" onClick={() => setShowWithWarningText(true)}>
            Open Warning Dialog
          </Button>

          <div className="bg-muted p-4 rounded-lg border">
            <p className="text-sm font-mono text-muted-foreground mb-2">Usage:</p>
            <code className="text-xs text-foreground block whitespace-pre-wrap break-words">
{`<ConfirmationDialog
  isOpen={showDialog}
  onOpenChange={setShowDialog}
  title="Delete Session?"
  description="Delete the session for Jane Doe?"
  warning="This action is permanent and cannot be undone."
  onConfirm={() => handleDelete()}
  variant="destructive"
  isDangerous={true}
  confirmLabel="Delete"
/>`}
            </code>
          </div>
        </CardContent>
      </Card>

      {/* Dialog Dialogs */}
      <ConfirmationDialog
        isOpen={showDefault}
        onOpenChange={setShowDefault}
        title="Confirm Action"
        description="Are you sure you want to proceed with this action?"
        onConfirm={handleSimpleConfirm}
        confirmLabel="Confirm"
        cancelLabel="Cancel"
        variant="default"
      />

      <ConfirmationDialog
        isOpen={showDestructive}
        onOpenChange={setShowDestructive}
        title="Delete Session?"
        description="Are you sure you want to delete this session?"
        onConfirm={handleDangerousConfirm}
        variant="destructive"
        isDangerous={true}
        confirmLabel="Delete Session"
        cancelLabel="Keep Session"
      />

      <ConfirmationDialog
        isOpen={showWithWarningText}
        onOpenChange={setShowWithWarningText}
        title="Delete Session?"
        description="Are you sure you want to delete the session for Jane Doe?"
        warning="This action is permanent and cannot be undone. All session data, transcript, and extracted notes will be deleted."
        onConfirm={handleDangerousConfirm}
        variant="destructive"
        isDangerous={true}
        confirmLabel="Delete Session"
        cancelLabel="Keep Session"
      />
    </div>
  );
}
