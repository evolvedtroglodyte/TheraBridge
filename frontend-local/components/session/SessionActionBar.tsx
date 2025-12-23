'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Trash2, Download, Share2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';
import { useDeleteSession } from '@/hooks/use-delete-session';

interface SessionActionBarProps {
  sessionId: string;
  patientName?: string;
  sessionDate?: string;
}

export function SessionActionBar({
  sessionId,
  patientName = 'Unknown Patient',
  sessionDate
}: SessionActionBarProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const router = useRouter();

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
  };

  const handleConfirmDelete = async () => {
    setIsDeleting(true);
    try {
      const response = await fetch(`/api/sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete session');
      }

      // Redirect to therapist dashboard after deletion
      router.push('/therapist');
    } catch (error) {
      setIsDeleting(false);
      throw error;
    }
  };

  const handleDownload = () => {
    // TODO: Implement download transcript/notes functionality
    console.log('Download not yet implemented');
  };

  const handleShare = () => {
    // TODO: Implement share functionality
    console.log('Share not yet implemented');
  };

  return (
    <>
      <div className="flex gap-2">
        <Button
          variant="outline"
          onClick={handleDownload}
          title="Download session notes and transcript"
        >
          <Download className="w-4 h-4 mr-2" />
          Download
        </Button>
        <Button
          variant="outline"
          onClick={handleShare}
          title="Share session with colleagues"
        >
          <Share2 className="w-4 h-4 mr-2" />
          Share
        </Button>
        <Button
          variant="destructive"
          onClick={handleDeleteClick}
          title="Permanently delete this session"
        >
          <Trash2 className="w-4 h-4 mr-2" />
          Delete Session
        </Button>
      </div>

      <ConfirmationDialog
        isOpen={showDeleteConfirm}
        onOpenChange={setShowDeleteConfirm}
        title="Delete Session?"
        description={`Are you sure you want to delete the session for ${patientName}${sessionDate ? ` on ${sessionDate}` : ''}?`}
        warning="This action is permanent and cannot be undone. All session data, transcript, and extracted notes will be deleted."
        onConfirm={handleConfirmDelete}
        confirmLabel="Delete Session"
        cancelLabel="Keep Session"
        variant="destructive"
        isDangerous={true}
        isLoading={isDeleting}
      />
    </>
  );
}

export type { SessionActionBarProps };
