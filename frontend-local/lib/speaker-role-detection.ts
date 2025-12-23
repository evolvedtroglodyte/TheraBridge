/**
 * Speaker Role Detection
 *
 * Assigns "Therapist" or "Client" roles to SPEAKER_00/SPEAKER_01 labels
 * from the audio transcription pipeline.
 *
 * Detection Strategy (Multi-heuristic):
 * 1. First speaker = Therapist (therapy sessions typically start with therapist)
 * 2. Speaking ratio validation (therapists usually speak 30-40%, clients 60-70%)
 * 3. Confidence scoring to handle edge cases
 *
 * The combined approach provides reliable detection even with unusual sessions.
 */

export interface DiarizedSegment {
  start: number;
  end: number;
  text: string;
  speaker: string;
}

export interface RoleAssignment {
  speakerId: string;
  role: 'Therapist' | 'Client';
  confidence: number; // 0-1
  speakingTime: number; // seconds
  segmentCount: number;
}

export interface RoleDetectionResult {
  assignments: Map<string, RoleAssignment>;
  segments: DiarizedSegment[];
  method: 'first_speaker' | 'speaking_ratio' | 'combined';
  overallConfidence: number;
}

/**
 * Detect and assign speaker roles based on multiple heuristics
 *
 * @param segments - Raw diarized segments from pipeline
 * @returns Role assignments and updated segments with role labels
 */
export function detectSpeakerRoles(
  segments: DiarizedSegment[]
): RoleDetectionResult {
  if (segments.length === 0) {
    return {
      assignments: new Map(),
      segments: [],
      method: 'first_speaker',
      overallConfidence: 0,
    };
  }

  // Step 1: Gather speaker statistics
  const speakerStats = calculateSpeakerStats(segments);
  const speakerIds = Array.from(speakerStats.keys()).filter(
    (id) => id !== 'UNKNOWN'
  );

  if (speakerIds.length === 0) {
    // All segments are UNKNOWN - can't determine roles
    return {
      assignments: new Map(),
      segments,
      method: 'first_speaker',
      overallConfidence: 0,
    };
  }

  if (speakerIds.length === 1) {
    // Only one speaker detected - assume it's the client (monologue/self-recording)
    const singleSpeakerId = speakerIds[0];
    const stats = speakerStats.get(singleSpeakerId)!;

    const assignments = new Map<string, RoleAssignment>();
    assignments.set(singleSpeakerId, {
      speakerId: singleSpeakerId,
      role: 'Client',
      confidence: 0.7,
      speakingTime: stats.totalTime,
      segmentCount: stats.count,
    });

    return {
      assignments,
      segments: applyRoleLabels(segments, assignments),
      method: 'first_speaker',
      overallConfidence: 0.7,
    };
  }

  // Step 2: Apply first-speaker heuristic
  const firstSpeaker = findFirstSpeaker(segments);

  // Step 3: Apply speaking ratio heuristic
  const ratioResult = applySpeakingRatioHeuristic(speakerStats, speakerIds);

  // Step 4: Combine heuristics
  const { assignments, confidence, method } = combineHeuristics(
    firstSpeaker,
    ratioResult,
    speakerStats,
    speakerIds
  );

  // Step 5: Apply role labels to segments
  const labeledSegments = applyRoleLabels(segments, assignments);

  return {
    assignments,
    segments: labeledSegments,
    method,
    overallConfidence: confidence,
  };
}

/**
 * Calculate speaking statistics for each speaker
 */
function calculateSpeakerStats(
  segments: DiarizedSegment[]
): Map<string, { totalTime: number; count: number; firstAppearance: number }> {
  const stats = new Map<
    string,
    { totalTime: number; count: number; firstAppearance: number }
  >();

  segments.forEach((segment, index) => {
    const speaker = segment.speaker;
    const duration = segment.end - segment.start;

    if (!stats.has(speaker)) {
      stats.set(speaker, {
        totalTime: 0,
        count: 0,
        firstAppearance: index,
      });
    }

    const speakerStats = stats.get(speaker)!;
    speakerStats.totalTime += duration;
    speakerStats.count += 1;
  });

  return stats;
}

/**
 * Find the first non-UNKNOWN speaker
 */
function findFirstSpeaker(segments: DiarizedSegment[]): string | null {
  for (const segment of segments) {
    if (segment.speaker !== 'UNKNOWN') {
      return segment.speaker;
    }
  }
  return null;
}

/**
 * Apply speaking ratio heuristic
 * Therapists typically speak 30-40% of the session
 */
function applySpeakingRatioHeuristic(
  stats: Map<string, { totalTime: number; count: number; firstAppearance: number }>,
  speakerIds: string[]
): { therapistId: string | null; confidence: number } {
  if (speakerIds.length !== 2) {
    return { therapistId: null, confidence: 0 };
  }

  const [speaker1, speaker2] = speakerIds;
  const stats1 = stats.get(speaker1)!;
  const stats2 = stats.get(speaker2)!;

  const totalTime = stats1.totalTime + stats2.totalTime;
  if (totalTime === 0) {
    return { therapistId: null, confidence: 0 };
  }

  const ratio1 = stats1.totalTime / totalTime;
  const ratio2 = stats2.totalTime / totalTime;

  // Ideal therapist range: 25-45%
  const idealTherapistMin = 0.25;
  const idealTherapistMax = 0.45;

  const isRatio1Therapist =
    ratio1 >= idealTherapistMin && ratio1 <= idealTherapistMax;
  const isRatio2Therapist =
    ratio2 >= idealTherapistMin && ratio2 <= idealTherapistMax;

  if (isRatio1Therapist && !isRatio2Therapist) {
    // Speaker 1 has therapist-like ratio
    const distanceToIdeal = Math.abs(ratio1 - 0.35);
    const confidence = 1 - distanceToIdeal * 2;
    return { therapistId: speaker1, confidence: Math.max(0.5, confidence) };
  }

  if (isRatio2Therapist && !isRatio1Therapist) {
    // Speaker 2 has therapist-like ratio
    const distanceToIdeal = Math.abs(ratio2 - 0.35);
    const confidence = 1 - distanceToIdeal * 2;
    return { therapistId: speaker2, confidence: Math.max(0.5, confidence) };
  }

  // If both or neither match, use lesser speaker (therapist speaks less)
  const lesserSpeaker = ratio1 < ratio2 ? speaker1 : speaker2;
  const lesserRatio = Math.min(ratio1, ratio2);

  // Confidence based on how distinct the ratios are
  const ratioDiff = Math.abs(ratio1 - ratio2);
  const confidence = Math.min(0.7, ratioDiff * 1.5);

  return { therapistId: lesserSpeaker, confidence };
}

/**
 * Combine first-speaker and speaking-ratio heuristics
 */
function combineHeuristics(
  firstSpeaker: string | null,
  ratioResult: { therapistId: string | null; confidence: number },
  stats: Map<string, { totalTime: number; count: number; firstAppearance: number }>,
  speakerIds: string[]
): {
  assignments: Map<string, RoleAssignment>;
  confidence: number;
  method: 'first_speaker' | 'speaking_ratio' | 'combined';
} {
  const assignments = new Map<string, RoleAssignment>();

  // Case 1: Both heuristics agree
  if (firstSpeaker && ratioResult.therapistId === firstSpeaker) {
    const therapistId = firstSpeaker;
    const clientId = speakerIds.find((id) => id !== therapistId)!;

    const therapistStats = stats.get(therapistId)!;
    const clientStats = stats.get(clientId)!;

    assignments.set(therapistId, {
      speakerId: therapistId,
      role: 'Therapist',
      confidence: Math.min(0.95, 0.8 + ratioResult.confidence * 0.15),
      speakingTime: therapistStats.totalTime,
      segmentCount: therapistStats.count,
    });

    assignments.set(clientId, {
      speakerId: clientId,
      role: 'Client',
      confidence: Math.min(0.95, 0.8 + ratioResult.confidence * 0.15),
      speakingTime: clientStats.totalTime,
      segmentCount: clientStats.count,
    });

    return {
      assignments,
      confidence: Math.min(0.95, 0.8 + ratioResult.confidence * 0.15),
      method: 'combined',
    };
  }

  // Case 2: Ratio heuristic is confident (>0.6)
  if (ratioResult.therapistId && ratioResult.confidence > 0.6) {
    const therapistId = ratioResult.therapistId;
    const clientId = speakerIds.find((id) => id !== therapistId)!;

    const therapistStats = stats.get(therapistId)!;
    const clientStats = stats.get(clientId)!;

    assignments.set(therapistId, {
      speakerId: therapistId,
      role: 'Therapist',
      confidence: ratioResult.confidence,
      speakingTime: therapistStats.totalTime,
      segmentCount: therapistStats.count,
    });

    assignments.set(clientId, {
      speakerId: clientId,
      role: 'Client',
      confidence: ratioResult.confidence,
      speakingTime: clientStats.totalTime,
      segmentCount: clientStats.count,
    });

    return {
      assignments,
      confidence: ratioResult.confidence,
      method: 'speaking_ratio',
    };
  }

  // Case 3: Fall back to first-speaker heuristic
  if (firstSpeaker) {
    const therapistId = firstSpeaker;
    const clientId = speakerIds.find((id) => id !== therapistId);

    const therapistStats = stats.get(therapistId)!;

    assignments.set(therapistId, {
      speakerId: therapistId,
      role: 'Therapist',
      confidence: 0.7,
      speakingTime: therapistStats.totalTime,
      segmentCount: therapistStats.count,
    });

    if (clientId) {
      const clientStats = stats.get(clientId)!;
      assignments.set(clientId, {
        speakerId: clientId,
        role: 'Client',
        confidence: 0.7,
        speakingTime: clientStats.totalTime,
        segmentCount: clientStats.count,
      });
    }

    return {
      assignments,
      confidence: 0.7,
      method: 'first_speaker',
    };
  }

  // Case 4: No clear determination - use speaking ratio as tie-breaker
  const [speaker1, speaker2] = speakerIds;
  const stats1 = stats.get(speaker1)!;
  const stats2 = stats.get(speaker2)!;

  // Lesser speaker = therapist
  const therapistId = stats1.totalTime < stats2.totalTime ? speaker1 : speaker2;
  const clientId = therapistId === speaker1 ? speaker2 : speaker1;

  const therapistStats = stats.get(therapistId)!;
  const clientStats = stats.get(clientId)!;

  assignments.set(therapistId, {
    speakerId: therapistId,
    role: 'Therapist',
    confidence: 0.5,
    speakingTime: therapistStats.totalTime,
    segmentCount: therapistStats.count,
  });

  assignments.set(clientId, {
    speakerId: clientId,
    role: 'Client',
    confidence: 0.5,
    speakingTime: clientStats.totalTime,
    segmentCount: clientStats.count,
  });

  return {
    assignments,
    confidence: 0.5,
    method: 'speaking_ratio',
  };
}

/**
 * Apply role labels to segments, replacing SPEAKER_XX with Therapist/Client
 */
function applyRoleLabels(
  segments: DiarizedSegment[],
  assignments: Map<string, RoleAssignment>
): DiarizedSegment[] {
  return segments.map((segment) => {
    const assignment = assignments.get(segment.speaker);
    if (assignment) {
      return {
        ...segment,
        speaker: assignment.role,
      };
    }
    // Keep UNKNOWN as-is
    return segment;
  });
}

/**
 * Format detection result for logging/debugging
 */
export function formatDetectionResult(result: RoleDetectionResult): string {
  const lines: string[] = ['Speaker Role Detection Results:'];
  lines.push(`  Method: ${result.method}`);
  lines.push(`  Confidence: ${(result.overallConfidence * 100).toFixed(1)}%`);
  lines.push('  Assignments:');

  result.assignments.forEach((assignment) => {
    const minutes = (assignment.speakingTime / 60).toFixed(1);
    lines.push(
      `    ${assignment.speakerId} → ${assignment.role} (${minutes} min, ${assignment.segmentCount} segments)`
    );
  });

  return lines.join('\n');
}
