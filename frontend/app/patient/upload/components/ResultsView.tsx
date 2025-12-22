'use client';

import { useEffect, useState } from 'react';
import { CheckCircle, Download, RotateCcw } from 'lucide-react';

interface ResultsViewProps {
  sessionId: string;
  uploadedFile: File;
  onReset: () => void;
}

export default function ResultsView({ sessionId, uploadedFile, onReset }: ResultsViewProps) {
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch final results
    fetch(`/api/status/${sessionId}`)
      .then(res => res.json())
      .then(data => {
        setResults(data.results);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch results:', err);
        setLoading(false);
      });
  }, [sessionId]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white border border-gray-200 rounded-lg p-8 shadow-sm text-center">
          <p className="text-gray-600">Loading results...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white border border-gray-200 rounded-lg p-8 shadow-sm">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <CheckCircle className="h-8 w-8 text-green-600" />
            <h2 className="text-2xl font-semibold">Processing Complete!</h2>
          </div>
          <button
            onClick={onReset}
            className="px-4 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition-colors flex items-center gap-2"
          >
            <RotateCcw className="h-4 w-4" />
            Upload Another
          </button>
        </div>

        {/* File Info */}
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <p className="text-sm text-gray-600">File: <span className="font-medium text-gray-900">{uploadedFile.name}</span></p>
          {results?.duration_minutes && (
            <p className="text-sm text-gray-600 mt-1">Duration: <span className="font-medium text-gray-900">{results.duration_minutes} minutes</span></p>
          )}
        </div>

        {/* Results Sections */}
        <div className="space-y-6">
          {/* Mood */}
          {results?.mood && (
            <div>
              <h3 className="text-lg font-semibold mb-2">Session Mood</h3>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-blue-900 font-medium">{results.mood}</p>
              </div>
            </div>
          )}

          {/* Topics */}
          {results?.topics && results.topics.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-2">Topics Discussed</h3>
              <div className="flex flex-wrap gap-2">
                {results.topics.map((topic: string, index: number) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Key Insights */}
          {results?.key_insights && results.key_insights.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-2">Key Insights</h3>
              <ul className="space-y-2">
                {results.key_insights.map((insight: string, index: number) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="text-blue-600 mt-1">•</span>
                    <span className="text-gray-700">{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Items */}
          {results?.action_items && results.action_items.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-2">Action Items</h3>
              <ul className="space-y-2">
                {results.action_items.map((item: string, index: number) => (
                  <li key={index} className="flex items-start gap-2">
                    <input type="checkbox" className="mt-1" />
                    <span className="text-gray-700">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Summary */}
          {results?.summary && (
            <div>
              <h3 className="text-lg font-semibold mb-2">Summary</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-gray-700 whitespace-pre-wrap">{results.summary}</p>
              </div>
            </div>
          )}

          {/* Transcript */}
          {results?.transcript && results.transcript.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-2">Transcript</h3>
              <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                <div className="space-y-3">
                  {results.transcript.map((segment: any, index: number) => (
                    <div key={index} className="flex gap-3">
                      <span className="font-medium text-blue-600 min-w-[80px]">
                        {segment.speaker}:
                      </span>
                      <span className="text-gray-700">{segment.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Export Button */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <button className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2">
            <Download className="h-4 w-4" />
            Export Results
          </button>
        </div>
      </div>
    </div>
  );
}
