-- Storage Bucket Policies for audio-sessions
-- Run this in Supabase SQL Editor to allow uploads and downloads

-- Allow anyone to upload files (INSERT policy)
CREATE POLICY "Allow all uploads to audio-sessions"
ON storage.objects
FOR INSERT
TO public
WITH CHECK (bucket_id = 'audio-sessions');

-- Allow anyone to read files (SELECT policy)
CREATE POLICY "Allow all reads from audio-sessions"
ON storage.objects
FOR SELECT
TO public
USING (bucket_id = 'audio-sessions');

-- Allow anyone to update files (UPDATE policy - optional)
CREATE POLICY "Allow all updates to audio-sessions"
ON storage.objects
FOR UPDATE
TO public
USING (bucket_id = 'audio-sessions');

-- Allow anyone to delete files (DELETE policy - optional)
CREATE POLICY "Allow all deletes from audio-sessions"
ON storage.objects
FOR DELETE
TO public
USING (bucket_id = 'audio-sessions');
