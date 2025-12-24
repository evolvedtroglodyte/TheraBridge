# TherapyBridge - Ultra-Detailed Algorithm Pipeline

**Maximum Granularity Mermaid Flowchart - Every Step Documented**

Copy the entire code block below and paste into:
- **mermaid.live** (recommended for viewing this complexity)
- **GitHub/GitLab** (may be very large)
- **VS Code with Mermaid extension**

```mermaid
flowchart TB
    %% ============================================================================
    %% LEGEND
    %% ============================================================================
    subgraph LEGEND[" 🔑 LEGEND "]
        L1[🔵 Upload/Storage]
        L2[🟣 Audio Processing]
        L3[🟠 AI Analysis]
        L4[🟢 Database]
        L5[🔴 Errors]
        L6[🟡 Frontend]
    end

    %% ============================================================================
    %% PHASE 1: UPLOAD & STORAGE
    %% ============================================================================
    START([👤 USER UPLOADS AUDIO FILE]) --> UPLOAD_MODAL[🌐 Frontend: UploadModal Component<br/>File: components/session/UploadModal.tsx]
    UPLOAD_MODAL --> CHECK_AUTH{🔐 User Authenticated?}
    CHECK_AUTH -->|No| ERROR_AUTH[❌ Error: Not authenticated<br/>Redirect to /login]
    CHECK_AUTH -->|Yes| VALIDATE_FILE{📋 Validate File?}

    VALIDATE_FILE --> CHECK_SIZE{📏 Size ≤ 500MB?}
    CHECK_SIZE -->|No| ERROR_SIZE_UPLOAD[❌ Error: File too large<br/>Max 500MB allowed]
    CHECK_SIZE -->|Yes| CHECK_TYPE{📄 Valid Type?<br/>MP3/WAV/M4A/OGG/FLAC}

    CHECK_TYPE -->|No| ERROR_TYPE[❌ Error: Invalid file type<br/>Show supported formats]
    CHECK_TYPE -->|Yes| CHECK_DURATION{⏱️ Duration Check?<br/>API: getDuration}

    CHECK_DURATION --> DURATION_VALID{✅ 1min ≤ dur ≤ 4hrs?}
    DURATION_VALID -->|No| ERROR_DURATION[❌ Error: Duration out of range<br/>Min 1min, Max 4hrs]
    DURATION_VALID -->|Yes| PREPARE_UPLOAD[📦 Prepare Upload<br/>Generate unique filename<br/>Format: patient_id/timestamp.ext]

    PREPARE_UPLOAD --> STORAGE_UPLOAD[☁️ POST Supabase Storage<br/>Bucket: audio-sessions<br/>Path: patient_id/timestamp.ext<br/>Content-Type: audio/mpeg]

    STORAGE_UPLOAD --> UPLOAD_CHECK{✅ Upload Success?<br/>HTTP 200/201?}
    UPLOAD_CHECK -->|No 4xx| ERROR_UPLOAD_CLIENT[❌ Client Error 4xx<br/>Invalid request]
    UPLOAD_CHECK -->|No 5xx| ERROR_UPLOAD_SERVER[❌ Server Error 5xx<br/>Retry eligible]

    ERROR_UPLOAD_SERVER --> RETRY_UPLOAD{🔄 Retry Count < 3?}
    RETRY_UPLOAD -->|Yes| BACKOFF_CALC[⏱️ Calculate Backoff<br/>Power of 2 times 1000ms<br/>Max 8000ms]
    BACKOFF_CALC --> WAIT_BACKOFF[⏸️ Wait Backoff Period]
    WAIT_BACKOFF --> INCREMENT_RETRY[🔢 Increment Retry Count]
    INCREMENT_RETRY --> STORAGE_UPLOAD
    RETRY_UPLOAD -->|No| ERROR_UPLOAD_FINAL[❌ Upload Failed<br/>Max retries exhausted]

    UPLOAD_CHECK -->|Yes 200| GET_PUBLIC_URL[🔗 Get Public URL<br/>Supabase Storage URL]
    GET_PUBLIC_URL --> VALIDATE_URL{✅ Valid URL?<br/>Starts with https?}
    VALIDATE_URL -->|No| ERROR_URL[❌ Error: Invalid storage URL]
    VALIDATE_URL -->|Yes| CREATE_SESSION_REQ[📤 POST /api/sessions<br/>Create Session Record]

    CREATE_SESSION_REQ --> VALIDATE_SESSION_DATA{✅ Validate Request?<br/>patient_id: required<br/>therapist_id: required<br/>audio_file_url: required}
    VALIDATE_SESSION_DATA -->|No| ERROR_VALIDATION[❌ Validation Error<br/>Missing required fields]
    VALIDATE_SESSION_DATA -->|Yes| DB_INSERT[(💾 Database INSERT<br/>therapy_sessions<br/>-----<br/>patient_id: UUID<br/>therapist_id: UUID<br/>audio_file_url: TEXT<br/>session_date: NOW<br/>processing_status: pending<br/>processing_progress: 0<br/>created_at: NOW)]

    DB_INSERT --> DB_INSERT_CHECK{✅ Insert Success?}
    DB_INSERT_CHECK -->|No| ERROR_DB_INSERT[❌ Database Error<br/>Failed to create session]
    DB_INSERT_CHECK -->|Yes| RETURN_SESSION_ID[📋 Return session_id<br/>HTTP 201 Created<br/>JSON: session_id, audio_file_url]

    RETURN_SESSION_ID --> TRIGGER_PROCESS[⚡ Trigger Processing<br/>POST /api/trigger-processing<br/>Fire-and-forget async]

    %% ============================================================================
    %% PHASE 2: AUDIO TRANSCRIPTION PIPELINE
    %% ============================================================================
    TRIGGER_PROCESS --> PROCESS_START[⚙️ POST /api/process<br/>Background Task Start<br/>Max Timeout: 300s]

    PROCESS_START --> FETCH_SESSION[📥 Fetch Session from DB<br/>SELECT * FROM therapy_sessions<br/>WHERE id = session_id]

    FETCH_SESSION --> SESSION_EXISTS{✅ Session Found?}
    SESSION_EXISTS -->|No| ERROR_SESSION_NOT_FOUND[❌ Error: Session not found]
    SESSION_EXISTS -->|Yes| CHECK_ALREADY_PROCESSING{📊 Status Check?<br/>status != processing?}

    CHECK_ALREADY_PROCESSING -->|Already Processing| ERROR_DUPLICATE_PROCESS[❌ Error: Already processing<br/>Prevent duplicate jobs]
    CHECK_ALREADY_PROCESSING -->|OK| UPDATE_STATUS_PROCESSING[(💾 UPDATE<br/>processing_status: processing<br/>processing_progress: 5<br/>updated_at: NOW)]

    UPDATE_STATUS_PROCESSING --> DOWNLOAD_AUDIO[📥 Download Audio<br/>GET audio_file_url<br/>Stream to temp file]

    DOWNLOAD_AUDIO --> DOWNLOAD_CHECK{✅ Download Success?}
    DOWNLOAD_CHECK -->|No| ERROR_DOWNLOAD[❌ Download Failed<br/>Cannot access audio file]
    DOWNLOAD_CHECK -->|Yes| VERIFY_FILE_EXISTS{📁 File Exists on Disk?}

    VERIFY_FILE_EXISTS -->|No| ERROR_FILE_MISSING[❌ File Missing<br/>Download corrupted]
    VERIFY_FILE_EXISTS -->|Yes| UPDATE_PROGRESS_10[(💾 UPDATE<br/>processing_progress: 10)]

    %% Audio Preprocessing Pipeline
    UPDATE_PROGRESS_10 --> PREPROCESS_START[🔧 AudioPreprocessor.preprocess<br/>File: src/pipeline.py]

    PREPROCESS_START --> LOAD_AUDIO[🎵 Load Audio<br/>Library: pydub.AudioSegment<br/>Detect format automatically]

    LOAD_AUDIO --> LOAD_CHECK{✅ Load Success?}
    LOAD_CHECK -->|No| ERROR_CORRUPT_AUDIO[❌ Error: Corrupted audio<br/>Cannot parse file]
    LOAD_CHECK -->|Yes| DETECT_CHANNELS{🔊 Detect Channels?<br/>Mono or Stereo}

    DETECT_CHANNELS --> IS_STEREO{📊 Stereo?}
    IS_STEREO -->|Yes| CONVERT_MONO[🔀 Convert to Mono<br/>Mix channels: L+R/2]
    IS_STEREO -->|No| ALREADY_MONO[✅ Already Mono<br/>Skip conversion]

    CONVERT_MONO --> CHECK_SAMPLE_RATE
    ALREADY_MONO --> CHECK_SAMPLE_RATE[📊 Check Sample Rate]

    CHECK_SAMPLE_RATE --> SAMPLE_RATE_OK{✅ Sample Rate = 16kHz?}
    SAMPLE_RATE_OK -->|No| RESAMPLE[🎚️ Resample to 16kHz<br/>Resampling algorithm: ffmpeg]
    SAMPLE_RATE_OK -->|Yes| DETECT_SILENCE

    RESAMPLE --> DETECT_SILENCE[🔇 Detect Silence<br/>Threshold: -40 dBFS<br/>Min length: 500ms]

    DETECT_SILENCE --> TRIM_START[✂️ Trim Leading Silence<br/>Remove silence from start]
    TRIM_START --> TRIM_END[✂️ Trim Trailing Silence<br/>Remove silence from end]

    TRIM_END --> CHECK_DURATION_AFTER_TRIM{⏱️ Duration > 10s?}
    CHECK_DURATION_AFTER_TRIM -->|No| ERROR_TOO_SHORT[❌ Error: Audio too short<br/>After trimming < 10s]
    CHECK_DURATION_AFTER_TRIM -->|Yes| ANALYZE_VOLUME[📊 Analyze Volume Levels<br/>Calculate dBFS<br/>Find peaks]

    ANALYZE_VOLUME --> VOLUME_TOO_LOW{🔊 Volume < -30 dBFS?}
    VOLUME_TOO_LOW -->|Yes| NORMALIZE_VOLUME[📈 Normalize Volume<br/>Target: -20 dBFS<br/>Headroom: 0.1<br/>effects.normalize]
    VOLUME_TOO_LOW -->|No| VOLUME_OK[✅ Volume OK<br/>Skip normalization]

    NORMALIZE_VOLUME --> CHECK_CLIPPING
    VOLUME_OK --> CHECK_CLIPPING[🔍 Check for Clipping<br/>Peaks > 0 dBFS?]

    CHECK_CLIPPING --> HAS_CLIPPING{⚠️ Clipping Detected?}
    HAS_CLIPPING -->|Yes| APPLY_LIMITER[🛡️ Apply Limiter<br/>Max: -0.1 dBFS<br/>Prevent distortion]
    HAS_CLIPPING -->|No| NO_CLIPPING[✅ No Clipping]

    APPLY_LIMITER --> CONVERT_FORMAT
    NO_CLIPPING --> CONVERT_FORMAT[🎚️ Convert Format<br/>Format: MP3<br/>Bitrate: 64kbps<br/>Codec: libmp3lame]

    CONVERT_FORMAT --> EXPORT_TEMP[💾 Export to Temp File<br/>Location: /tmp/processed.mp3]

    EXPORT_TEMP --> VALIDATE_OUTPUT{✅ Output Valid?}
    VALIDATE_OUTPUT -->|No| ERROR_EXPORT[❌ Export Failed<br/>Cannot write file]
    VALIDATE_OUTPUT -->|Yes| CHECK_OUTPUT_SIZE{📏 Size < 25MB?<br/>Whisper API Limit}

    CHECK_OUTPUT_SIZE -->|No| ERROR_SIZE_WHISPER[❌ Error: File Too Large<br/>Whisper limit 25MB<br/>Suggest: Reduce bitrate]
    CHECK_OUTPUT_SIZE -->|Yes| PREPROCESSED_AUDIO[✅ Preprocessed Audio Ready<br/>Duration: X minutes<br/>Size: Y MB<br/>Format: 16kHz Mono MP3]

    PREPROCESSED_AUDIO --> UPDATE_PROGRESS_20[(💾 UPDATE<br/>processing_progress: 20)]

    %% Parallel Branch: Whisper + Pyannote
    UPDATE_PROGRESS_20 --> PARALLEL_START{⚡ START PARALLEL PROCESSING<br/>Branch 1: Whisper Transcription<br/>Branch 2: Pyannote Diarization}

    %% ============================================================================
    %% BRANCH 1: WHISPER TRANSCRIPTION
    %% ============================================================================
    PARALLEL_START -->|Branch 1| WHISPER_PREPARE[📝 Prepare Whisper Request<br/>Model: whisper-1<br/>Response format: verbose_json<br/>Language: en]

    WHISPER_PREPARE --> WHISPER_CALL[🗣️ POST OpenAI Whisper API<br/>/v1/audio/transcriptions<br/>File: multipart/form-data<br/>Timeout: 120s]

    WHISPER_CALL --> WHISPER_RESPONSE{📡 Response Status?}

    WHISPER_RESPONSE -->|200 Success| WHISPER_PARSE[📊 Parse Whisper Response<br/>Extract segments array<br/>Each: start, end, text]

    WHISPER_RESPONSE -->|429 Rate Limited| WHISPER_RATE_LIMIT[⏱️ Rate Limited<br/>Extract Retry-After header<br/>Default: 60s]

    WHISPER_RATE_LIMIT --> WHISPER_RETRY_COUNT{🔢 Retry Count < 5?}
    WHISPER_RETRY_COUNT -->|No| ERROR_WHISPER_RATE[❌ Whisper Failed<br/>Rate limit retries exhausted]
    WHISPER_RETRY_COUNT -->|Yes| WHISPER_BACKOFF[⏸️ Exponential Backoff<br/>Attempt 1: 1s<br/>Attempt 2: 2s<br/>Attempt 3: 4s<br/>Attempt 4: 8s<br/>Attempt 5: 16s]

    WHISPER_BACKOFF --> WHISPER_WAIT[⏱️ Wait Backoff Period]
    WHISPER_WAIT --> WHISPER_INCREMENT[🔢 Increment Retry]
    WHISPER_INCREMENT --> WHISPER_CALL

    WHISPER_RESPONSE -->|401 Unauthorized| ERROR_WHISPER_AUTH[❌ Whisper Auth Error<br/>Invalid API key]
    WHISPER_RESPONSE -->|400 Bad Request| ERROR_WHISPER_INVALID[❌ Whisper Invalid Request<br/>Check file format]
    WHISPER_RESPONSE -->|5xx Server Error| WHISPER_SERVER_ERROR[⚠️ Whisper Server Error<br/>Retry eligible]

    WHISPER_SERVER_ERROR --> WHISPER_RETRY_COUNT

    WHISPER_PARSE --> WHISPER_VALIDATE{✅ Valid Segments?<br/>Array length > 0?}
    WHISPER_VALIDATE -->|No| ERROR_WHISPER_EMPTY[❌ Whisper Returned Empty<br/>No transcription found]
    WHISPER_VALIDATE -->|Yes| WHISPER_CLEAN[🧹 Clean Transcription<br/>Remove artifacts<br/>Fix timestamps<br/>Merge short segments]

    WHISPER_CLEAN --> WHISPER_SUCCESS[✅ Whisper Complete<br/>Segments: N<br/>Duration: X min<br/>Language: detected]

    %% ============================================================================
    %% BRANCH 2: PYANNOTE DIARIZATION
    %% ============================================================================
    PARALLEL_START -->|Branch 2| PYANNOTE_PREPARE[👥 Prepare Pyannote Pipeline<br/>Model: pyannote/speaker-diarization-3.1<br/>HuggingFace Token required]

    PYANNOTE_PREPARE --> CHECK_PYANNOTE_TOKEN{🔑 HF Token Valid?}
    CHECK_PYANNOTE_TOKEN -->|No| ERROR_PYANNOTE_TOKEN[❌ Error: No HuggingFace token<br/>Required for pyannote]
    CHECK_PYANNOTE_TOKEN -->|Yes| LOAD_PYANNOTE_MODEL[📦 Load Pyannote Model<br/>Download if not cached<br/>~500MB model size]

    LOAD_PYANNOTE_MODEL --> MODEL_LOADED{✅ Model Loaded?}
    MODEL_LOADED -->|No| ERROR_MODEL_LOAD[❌ Model Load Failed<br/>Check disk space, connection]
    MODEL_LOADED -->|Yes| PYANNOTE_PROCESS[🔍 Run Diarization<br/>Identify speaker changes<br/>Min segment: 0.5s<br/>Min speaker: 1, Max: 10]

    PYANNOTE_PROCESS --> PYANNOTE_RUNNING{⏳ Processing...}
    PYANNOTE_RUNNING --> PYANNOTE_COMPLETE[✅ Diarization Complete<br/>Speakers detected: N<br/>Segments: M]

    PYANNOTE_COMPLETE --> PYANNOTE_VALIDATE{✅ Valid Output?<br/>Speakers ≥ 1?}
    PYANNOTE_VALIDATE -->|No| ERROR_PYANNOTE_EMPTY[❌ No speakers detected<br/>Possible silence]
    PYANNOTE_VALIDATE -->|Yes| PYANNOTE_LABEL[🏷️ Label Speakers<br/>SPEAKER_00, SPEAKER_01, ...]

    PYANNOTE_LABEL --> PYANNOTE_SUCCESS[✅ Pyannote Complete<br/>Speaker segments ready]

    %% ============================================================================
    %% MERGE WHISPER + PYANNOTE
    %% ============================================================================
    WHISPER_SUCCESS --> MERGE_WAIT{⏳ Wait for Both<br/>Complete?}
    PYANNOTE_SUCCESS --> MERGE_WAIT

    MERGE_WAIT --> MERGE_START[🔀 Merge Transcription + Diarization<br/>Algorithm: Timestamp Alignment]

    MERGE_START --> MERGE_ITERATE[🔄 For each Whisper segment:<br/>Find overlapping speaker]

    MERGE_ITERATE --> FIND_OVERLAP[🔍 Find Speaker at timestamp<br/>If multiple, use majority]

    FIND_OVERLAP --> ASSIGN_SPEAKER[👤 Assign Speaker Label<br/>segment.speaker = SPEAKER_XX]

    ASSIGN_SPEAKER --> MERGE_CHECK_COMPLETE{✅ All Segments<br/>Assigned?}
    MERGE_CHECK_COMPLETE -->|No| MERGE_ITERATE
    MERGE_CHECK_COMPLETE -->|Yes| MERGED_SEGMENTS[📝 Merged Segments<br/>start, end, speaker, text]

    MERGED_SEGMENTS --> VALIDATE_MERGE{✅ Validate Merge?<br/>No gaps > 5s?<br/>All speakers assigned?}
    VALIDATE_MERGE -->|No| ERROR_MERGE[❌ Merge Failed<br/>Invalid alignment]
    VALIDATE_MERGE -->|Yes| DIARIZED_TRANSCRIPT[📄 Diarized Transcript Ready<br/>Format: DiarizedSegment array]

    DIARIZED_TRANSCRIPT --> UPDATE_PROGRESS_80[(💾 UPDATE<br/>processing_progress: 80)]

    %% ============================================================================
    %% SPEAKER ROLE DETECTION
    %% ============================================================================
    UPDATE_PROGRESS_80 --> ROLE_DETECTION_START[🏷️ Speaker Role Detection<br/>File: lib/speaker-role-detection.ts]

    ROLE_DETECTION_START --> COUNT_SPEAKERS{📊 How Many Speakers?}

    COUNT_SPEAKERS -->|1| SINGLE_SPEAKER[⚠️ Single Speaker<br/>Assign: SPEAKER_00 = Client<br/>Confidence: 0.5 low]

    COUNT_SPEAKERS -->|2| TWO_SPEAKERS[✅ Two Speakers<br/>Run heuristics]

    COUNT_SPEAKERS -->|3+| MULTI_SPEAKERS[⚠️ 3+ Speakers<br/>Complex scenario<br/>Use heuristics on top 2]

    TWO_SPEAKERS --> CALC_STATS[📊 Calculate Speaker Stats]
    MULTI_SPEAKERS --> CALC_STATS

    CALC_STATS --> CALC_SPEAKING_TIME[⏱️ Calculate Speaking Time<br/>Sum duration per speaker]

    CALC_SPEAKING_TIME --> CALC_RATIO[📊 Calculate Speaking Ratio<br/>ratio equals time divided by total_duration]

    CALC_RATIO --> CALC_SEGMENTS[🔢 Count Segments<br/>segments_count per speaker]

    CALC_SEGMENTS --> CALC_AVG_LENGTH[📏 Avg Segment Length<br/>avg equals time divided by segments_count]

    CALC_AVG_LENGTH --> IDENTIFY_FIRST[👤 Identify First Speaker<br/>min start timestamp]

    IDENTIFY_FIRST --> HEURISTIC_1[🔍 Heuristic 1: First Speaker<br/>Assumption: Therapist opens<br/>Confidence: 0.7]

    IDENTIFY_FIRST --> HEURISTIC_2[🔍 Heuristic 2: Speaking Ratio<br/>Therapist: 30-40%<br/>Client: 60-70%]

    HEURISTIC_2 --> RATIO_CHECK{📊 Ratio Match<br/>Therapist Range?}

    RATIO_CHECK -->|SPEAKER_00 in 30-40%| H2_SPEAKER00_THERAPIST[👨‍⚕️ SPEAKER_00 = Therapist<br/>Confidence: 0.75]
    RATIO_CHECK -->|SPEAKER_01 in 30-40%| H2_SPEAKER01_THERAPIST[👨‍⚕️ SPEAKER_01 = Therapist<br/>Confidence: 0.75]
    RATIO_CHECK -->|No Match| H2_UNCERTAIN[⚠️ Ratio Uncertain<br/>Confidence: 0.5]

    HEURISTIC_1 --> COMPARE_HEURISTICS{🤔 Compare Heuristics}
    H2_SPEAKER00_THERAPIST --> COMPARE_HEURISTICS
    H2_SPEAKER01_THERAPIST --> COMPARE_HEURISTICS
    H2_UNCERTAIN --> COMPARE_HEURISTICS

    COMPARE_HEURISTICS --> AGREE{✅ Both Agree?}

    AGREE -->|Yes| HIGH_CONFIDENCE[🎉 High Confidence<br/>Confidence: 0.85<br/>Both heuristics agree]

    AGREE -->|No| CONFLICT_RESOLUTION{⚖️ Resolve Conflict}

    CONFLICT_RESOLUTION --> USE_RATIO_CONF{📊 Ratio Conf > 0.6?}
    USE_RATIO_CONF -->|Yes| USE_RATIO[📊 Use Ratio Method<br/>Confidence: 0.65]
    USE_RATIO_CONF -->|No| USE_FIRST_SPEAKER[👤 Use First Speaker<br/>Confidence: 0.55]

    HIGH_CONFIDENCE --> ASSIGN_ROLES
    USE_RATIO --> ASSIGN_ROLES
    USE_FIRST_SPEAKER --> ASSIGN_ROLES
    SINGLE_SPEAKER --> ASSIGN_ROLES

    ASSIGN_ROLES[🏷️ Assign Final Roles<br/>Map SPEAKER_XX to Therapist/Client]

    ASSIGN_ROLES --> REPLACE_LABELS[🔄 Replace Speaker Labels<br/>SPEAKER_00 → Therapist/Client<br/>SPEAKER_01 → Client/Therapist]

    REPLACE_LABELS --> LABELED_TRANSCRIPT[📝 Labeled Transcript<br/>speaker: Therapist or Client<br/>text, start, end]

    LABELED_TRANSCRIPT --> VALIDATE_LABELS{✅ Validate Labels?<br/>All segments labeled?}
    VALIDATE_LABELS -->|No| ERROR_LABELING[❌ Labeling Failed<br/>Some segments unlabeled]
    VALIDATE_LABELS -->|Yes| CALCULATE_FINAL_STATS[📊 Calculate Final Stats<br/>Duration, word count,<br/>speaker balance]

    %% ============================================================================
    %% QUICK GPT-4o ANALYSIS (Before Wave 1)
    %% ============================================================================
    CALCULATE_FINAL_STATS --> UPDATE_PROGRESS_85[(💾 UPDATE<br/>processing_progress: 85)]

    UPDATE_PROGRESS_85 --> QUICK_AI_START[🤖 Quick GPT-4o Analysis<br/>Generate initial insights]

    QUICK_AI_START --> QUICK_AI_PROMPT[📝 Build Quick Analysis Prompt<br/>Extract:<br/>• Initial mood<br/>• 2-3 topics<br/>• 2-sentence summary]

    QUICK_AI_PROMPT --> QUICK_AI_CALL[🤖 POST OpenAI Chat<br/>Model: gpt-4o<br/>Temperature: 0.3<br/>Response format: json_object]

    QUICK_AI_CALL --> QUICK_AI_CHECK{✅ API Success?}
    QUICK_AI_CHECK -->|No| QUICK_AI_RETRY[🔄 Retry Quick Analysis<br/>Max 2 attempts]
    QUICK_AI_RETRY --> QUICK_AI_RETRY_COUNT{🔢 Retries < 2?}
    QUICK_AI_RETRY_COUNT -->|Yes| QUICK_AI_CALL
    QUICK_AI_RETRY_COUNT -->|No| QUICK_AI_FAILED[⚠️ Quick Analysis Failed<br/>Continue without]

    QUICK_AI_CHECK -->|Yes| QUICK_AI_PARSE[📊 Parse Quick Analysis<br/>mood, topics, summary]

    QUICK_AI_PARSE --> UPDATE_TRANSCRIPT_DB[(💾 UPDATE therapy_sessions<br/>-----<br/>transcript: JSONB array<br/>summary: TEXT<br/>mood: TEXT deprecated<br/>topics: TEXT array<br/>duration_minutes: INTEGER<br/>processing_status: completed<br/>processing_progress: 100<br/>updated_at: NOW)]

    QUICK_AI_FAILED --> UPDATE_TRANSCRIPT_DB

    %% ============================================================================
    %% AUTO-TRIGGER WAVE 1 ANALYSIS
    %% ============================================================================
    UPDATE_TRANSCRIPT_DB --> AUTO_TRIGGER[⚡ Auto-trigger Analysis Pipeline<br/>POST /api/sessions/id/analyze-full-pipeline]

    AUTO_TRIGGER --> ORCHESTRATOR_START[🎯 AnalysisOrchestrator.run<br/>File: services/analysis_orchestrator.py]

    ORCHESTRATOR_START --> CHECK_TRANSCRIPT_COMPLETE{✅ Transcript Complete?<br/>processing_status = completed?}
    CHECK_TRANSCRIPT_COMPLETE -->|No| ERROR_NO_TRANSCRIPT[❌ Error: No transcript<br/>Cannot analyze]
    CHECK_TRANSCRIPT_COMPLETE -->|Yes| UPDATE_WAVE1_STATUS[(💾 UPDATE<br/>analysis_status: wave1_running<br/>updated_at: NOW)]

    UPDATE_WAVE1_STATUS --> WAVE1_PARALLEL{🌊 WAVE 1 PARALLEL EXECUTION<br/>asyncio.gather<br/>3 concurrent tasks}

    %% ============================================================================
    %% WAVE 1 - BRANCH 1: MOOD ANALYSIS
    %% ============================================================================
    WAVE1_PARALLEL -->|Branch 1| MOOD_START[😊 MoodAnalyzer.analyze_session_mood<br/>File: services/mood_analyzer.py]

    MOOD_START --> MOOD_FETCH_SESSION[📥 Fetch Session<br/>SELECT transcript FROM therapy_sessions]

    MOOD_FETCH_SESSION --> MOOD_PARSE_TRANSCRIPT[📊 Parse Transcript JSONB<br/>Extract DiarizedSegment array]

    MOOD_PARSE_TRANSCRIPT --> MOOD_FILTER[🔍 Filter Patient Dialogue<br/>WHERE speaker = Client OR SPEAKER_01]

    MOOD_FILTER --> MOOD_CHECK_SEGMENTS{✅ Patient Segments > 0?}
    MOOD_CHECK_SEGMENTS -->|No| MOOD_ERROR[❌ Error: No patient dialogue<br/>Cannot analyze mood]

    MOOD_CHECK_SEGMENTS -->|Yes| MOOD_FORMAT[📝 Format Patient Dialogue<br/>For each segment:<br/>MM:SS text newline]

    MOOD_FORMAT --> MOOD_COUNT_WORDS{📏 Word Count ≥ 50?}
    MOOD_COUNT_WORDS -->|No| MOOD_WARN_SHORT[⚠️ Warning: Very short dialogue<br/>Mood may be unreliable<br/>Continue anyway]
    MOOD_COUNT_WORDS -->|Yes| MOOD_PROMPT_BUILD
    MOOD_WARN_SHORT --> MOOD_PROMPT_BUILD

    MOOD_PROMPT_BUILD[📝 Build Mood Analysis Prompt<br/>System: Clinical mood scale definition<br/>-----<br/>0.0-2.0: Severe distress crisis SI<br/>2.5-4.0: Significant distress mod-severe<br/>4.5-5.5: Mild distress to neutral<br/>6.0-7.5: Positive baseline stable<br/>8.0-10.0: Very positive thriving<br/>-----<br/>Analyze 10+ dimensions:<br/>• Emotional language<br/>• Self-reported state<br/>• Clinical symptoms sleep appetite energy<br/>• Suicidal/self-harm ideation<br/>• Hopelessness vs hope<br/>• Functioning work school relationships<br/>• Engagement level<br/>• Anxiety markers<br/>• Depression markers<br/>• Positive indicators]

    MOOD_PROMPT_BUILD --> MOOD_API_CALL[🤖 POST OpenAI Chat<br/>Model: gpt-5-nano<br/>Temperature: default<br/>Response format: json_object<br/>Timeout: 60s]

    MOOD_API_CALL --> MOOD_API_RESPONSE{📡 Response Status?}

    MOOD_API_RESPONSE -->|200 Success| MOOD_PARSE[📊 Parse JSON Response<br/>Extract:<br/>mood_score: float<br/>confidence: float<br/>rationale: string<br/>key_indicators: array<br/>emotional_tone: string]

    MOOD_API_RESPONSE -->|429 Rate Limited| MOOD_RATE_LIMIT[⏱️ Rate Limited<br/>Retry after delay]
    MOOD_RATE_LIMIT --> MOOD_RETRY_COUNT{🔢 Retries < 3?}
    MOOD_RETRY_COUNT -->|No| MOOD_FAILED[❌ Mood Analysis Failed<br/>Rate limit exhausted]
    MOOD_RETRY_COUNT -->|Yes| MOOD_BACKOFF[⏸️ Backoff: exponential delay seconds]
    MOOD_BACKOFF --> MOOD_API_CALL

    MOOD_API_RESPONSE -->|401/403 Auth| ERROR_MOOD_AUTH[❌ API Auth Error<br/>Invalid OpenAI key]
    MOOD_API_RESPONSE -->|5xx Server| MOOD_SERVER_ERROR[⚠️ Server Error<br/>Retry eligible]
    MOOD_SERVER_ERROR --> MOOD_RETRY_COUNT

    MOOD_PARSE --> MOOD_VALIDATE_SCORE{✅ Validate mood_score?<br/>0.0 ≤ score ≤ 10.0?}
    MOOD_VALIDATE_SCORE -->|No| MOOD_CLAMP[⚖️ Clamp to Valid Range<br/>If < 0: 0.0<br/>If > 10: 10.0]
    MOOD_VALIDATE_SCORE -->|Yes| MOOD_ROUND

    MOOD_CLAMP --> MOOD_ROUND[🔢 Round to Nearest 0.5<br/>Formula: round score times 2 divided by 2]

    MOOD_ROUND --> MOOD_VALIDATE_CONFIDENCE{✅ Validate confidence?<br/>0.0 ≤ conf ≤ 1.0?}
    MOOD_VALIDATE_CONFIDENCE -->|No| MOOD_DEFAULT_CONF[⚙️ Default Confidence = 0.7]
    MOOD_VALIDATE_CONFIDENCE -->|Yes| MOOD_CHECK_INDICATORS

    MOOD_DEFAULT_CONF --> MOOD_CHECK_INDICATORS{✅ key_indicators<br/>is array?}
    MOOD_CHECK_INDICATORS -->|No| MOOD_DEFAULT_INDICATORS[⚙️ Default: empty array]
    MOOD_CHECK_INDICATORS -->|Yes| MOOD_STORE_PREPARE

    MOOD_DEFAULT_INDICATORS --> MOOD_STORE_PREPARE[📦 Prepare Storage Object<br/>MoodAnalysis object]

    MOOD_STORE_PREPARE --> MOOD_STORE[(💾 UPDATE therapy_sessions<br/>SET<br/>mood_score = X.X<br/>mood_confidence = 0.XX<br/>mood_rationale = TEXT<br/>mood_indicators = JSONB array<br/>emotional_tone = TEXT<br/>mood_analyzed_at = NOW<br/>WHERE id = session_id)]

    MOOD_STORE --> MOOD_LOG[📝 Log Analysis Complete<br/>INSERT analysis_processing_log<br/>wave: mood<br/>status: completed<br/>duration_ms: X]

    MOOD_LOG --> MOOD_COMPLETE[✅ Mood Analysis Complete]

    %% ============================================================================
    %% WAVE 1 - BRANCH 2: TOPIC EXTRACTION
    %% ============================================================================
    WAVE1_PARALLEL -->|Branch 2| TOPIC_START[📋 TopicExtractor.extract_metadata<br/>File: services/topic_extractor.py]

    TOPIC_START --> TOPIC_FETCH[📥 Fetch Session<br/>SELECT transcript]

    TOPIC_FETCH --> TOPIC_PARSE_TRANSCRIPT[📊 Parse Transcript JSONB]

    TOPIC_PARSE_TRANSCRIPT --> TOPIC_FORMAT[📝 Format Full Conversation<br/>Include BOTH Therapist + Client<br/>Format: MM:SS Speaker: text newline]

    TOPIC_FORMAT --> TOPIC_VALIDATE_LENGTH{📏 Conversation<br/>Word Count ≥ 100?}
    TOPIC_VALIDATE_LENGTH -->|No| TOPIC_WARN[⚠️ Warning: Short conversation<br/>Topics may be generic]
    TOPIC_VALIDATE_LENGTH -->|Yes| TOPIC_LOAD_LIBRARY
    TOPIC_WARN --> TOPIC_LOAD_LIBRARY

    TOPIC_LOAD_LIBRARY[📚 Load Technique Library<br/>File: services/technique_library.py<br/>350+ techniques across modalities:<br/>• CBT 80+ techniques<br/>• DBT 60+ techniques<br/>• ACT 40+ techniques<br/>• Mindfulness 30+ techniques<br/>• Motivational Interviewing 25+<br/>• EMDR 20+<br/>• Psychodynamic 50+<br/>• Solution-Focused 25+<br/>• Narrative 20+]

    TOPIC_LOAD_LIBRARY --> TOPIC_PROMPT_BUILD[📝 Build Topic Extraction Prompt<br/>System: Clinical metadata extraction<br/>-----<br/>Extract exactly:<br/>• Topics: 1-2 main clinical topics<br/>  Format: Specific & clinical<br/>  Examples: Panic attacks, Grief processing<br/>  NOT generic: Anxiety, Depression<br/>• Action items: 2 concrete homework tasks<br/>  Format: Actionable, specific<br/>  Examples: Practice TIPP daily, Call psychiatrist<br/>• Technique: 1 therapeutic technique used<br/>  Must match library<br/>  Format: MODALITY - TECHNIQUE<br/>• Summary: 2 sentences max 150 chars<br/>  Format: Active voice, direct<br/>  NO phrases: The session focused on<br/>-----<br/>User: Full conversation transcript]

    TOPIC_PROMPT_BUILD --> TOPIC_API_CALL[🤖 POST OpenAI Chat<br/>Model: gpt-5-mini<br/>Response format: json_object<br/>Timeout: 90s]

    TOPIC_API_CALL --> TOPIC_API_RESPONSE{📡 Response Status?}

    TOPIC_API_RESPONSE -->|200 Success| TOPIC_PARSE[📊 Parse JSON Response<br/>Extract:<br/>topics: array<br/>action_items: array<br/>technique: string<br/>summary: string<br/>confidence: float]

    TOPIC_API_RESPONSE -->|429 Rate Limited| TOPIC_RATE_LIMIT[⏱️ Rate Limited]
    TOPIC_RATE_LIMIT --> TOPIC_RETRY_COUNT{🔢 Retries < 3?}
    TOPIC_RETRY_COUNT -->|No| TOPIC_FAILED[❌ Topic Extraction Failed]
    TOPIC_RETRY_COUNT -->|Yes| TOPIC_BACKOFF[⏸️ Backoff delay]
    TOPIC_BACKOFF --> TOPIC_API_CALL

    TOPIC_API_RESPONSE -->|5xx Server| TOPIC_SERVER_ERROR[⚠️ Server Error]
    TOPIC_SERVER_ERROR --> TOPIC_RETRY_COUNT

    TOPIC_PARSE --> TOPIC_VALIDATE_TOPICS{✅ Validate topics?<br/>Array with 1-2 items?}
    TOPIC_VALIDATE_TOPICS -->|No| TOPIC_DEFAULT_TOPICS[⚙️ Default Topics<br/>Array: General session]
    TOPIC_VALIDATE_TOPICS -->|Yes| TOPIC_VALIDATE_ACTIONS

    TOPIC_DEFAULT_TOPICS --> TOPIC_VALIDATE_ACTIONS{✅ Validate action_items?<br/>Array with items?}
    TOPIC_VALIDATE_ACTIONS -->|No| TOPIC_DEFAULT_ACTIONS[⚙️ Default Actions<br/>Array: Continue practicing techniques]
    TOPIC_VALIDATE_ACTIONS -->|Yes| TOPIC_VALIDATE_TECHNIQUE

    TOPIC_DEFAULT_ACTIONS --> TOPIC_VALIDATE_TECHNIQUE{✅ Validate technique?<br/>Non-empty string?}
    TOPIC_VALIDATE_TECHNIQUE -->|No| TOPIC_MATCH_LIBRARY[🔍 Attempt Library Match<br/>Search library for keywords<br/>Fuzzy matching threshold: 0.7]
    TOPIC_VALIDATE_TECHNIQUE -->|Yes| TOPIC_MATCH_LIBRARY

    TOPIC_MATCH_LIBRARY --> TOPIC_MATCH_FOUND{✅ Match Found?}
    TOPIC_MATCH_FOUND -->|No| TOPIC_DEFAULT_TECHNIQUE[⚙️ Default Technique<br/>Unknown - General therapy]
    TOPIC_MATCH_FOUND -->|Yes| TOPIC_STANDARDIZE[📐 Standardize Technique<br/>Format: MODALITY - TECHNIQUE<br/>Example: CBT - Cognitive Restructuring]

    TOPIC_DEFAULT_TECHNIQUE --> TOPIC_VALIDATE_SUMMARY
    TOPIC_STANDARDIZE --> TOPIC_VALIDATE_SUMMARY{✅ Validate summary?<br/>Length > 0?}

    TOPIC_VALIDATE_SUMMARY -->|No| TOPIC_DEFAULT_SUMMARY[⚙️ Default Summary<br/>Therapy session completed]
    TOPIC_VALIDATE_SUMMARY -->|Yes| TOPIC_CHECK_LENGTH{📏 Length > 150 chars?}

    TOPIC_CHECK_LENGTH -->|Yes| TOPIC_TRUNCATE[✂️ Truncate Summary<br/>Find word boundary ≤ 147 chars<br/>Add ... ellipsis<br/>Total: 150 chars]
    TOPIC_CHECK_LENGTH -->|No| TOPIC_SUMMARY_OK[✅ Summary Length OK]

    TOPIC_DEFAULT_SUMMARY --> TOPIC_STORE_PREPARE
    TOPIC_TRUNCATE --> TOPIC_STORE_PREPARE
    TOPIC_SUMMARY_OK --> TOPIC_STORE_PREPARE

    TOPIC_STORE_PREPARE[📦 Prepare Storage Object<br/>SessionMetadata object]

    TOPIC_STORE_PREPARE --> TOPIC_STORE[(💾 UPDATE therapy_sessions<br/>SET<br/>topics = TEXT array<br/>action_items = TEXT array<br/>technique = TEXT<br/>summary = TEXT max 150 chars<br/>extraction_confidence = 0.XX<br/>raw_meta_summary = JSONB full response<br/>topics_extracted_at = NOW<br/>WHERE id = session_id)]

    TOPIC_STORE --> TOPIC_LOG[📝 Log Analysis Complete<br/>INSERT analysis_processing_log<br/>wave: topics<br/>status: completed]

    TOPIC_LOG --> TOPIC_COMPLETE[✅ Topic Extraction Complete]

    %% ============================================================================
    %% WAVE 1 - BRANCH 3: BREAKTHROUGH DETECTION
    %% ============================================================================
    WAVE1_PARALLEL -->|Branch 3| BREAKTHROUGH_START[💡 BreakthroughDetector.analyze_session<br/>File: services/breakthrough_detector.py]

    BREAKTHROUGH_START --> BREAKTHROUGH_FETCH[📥 Fetch Session + Topics<br/>SELECT transcript, topics, summary]

    BREAKTHROUGH_FETCH --> BREAKTHROUGH_PARSE[📊 Parse Transcript<br/>Extract conversation turns]

    BREAKTHROUGH_PARSE --> BREAKTHROUGH_GROUP[🔀 Group Consecutive Speakers<br/>Merge adjacent segments<br/>from same speaker]

    BREAKTHROUGH_GROUP --> BREAKTHROUGH_CHECK_LENGTH{📏 Conversation<br/>Turns ≥ 10?}
    BREAKTHROUGH_CHECK_LENGTH -->|No| BREAKTHROUGH_TOO_SHORT[⚠️ Too Short<br/>Unlikely to have breakthrough<br/>Skip analysis]
    BREAKTHROUGH_CHECK_LENGTH -->|Yes| BREAKTHROUGH_PROMPT_BUILD

    BREAKTHROUGH_PROMPT_BUILD[📝 Build Breakthrough Detection Prompt<br/>System: ULTRA-STRICT CRITERIA<br/>-----<br/>✅ IS a Breakthrough:<br/>• Root cause discovery<br/>  Patient realizes WHY pattern exists<br/>• Pattern recognition<br/>  Patient sees recurring theme across situations<br/>• Identity insight<br/>  Patient reframes self-concept<br/>• Reframe revelation<br/>  Patient discovers new perspective<br/>-----<br/>❌ NOT a Breakthrough:<br/>• Emotional releases crying, anger<br/>• Routine CBT work challenging thoughts<br/>• Skill application using techniques<br/>• Progress updates feeling better<br/>• Values clarification identifying values<br/>• External realizations about others<br/>-----<br/>Requirements:<br/>• NEW realization not discussed before<br/>• POSITIVE discovery not trauma recall<br/>• About SELF not about others<br/>• TRANSFORMATIVE changes perspective<br/>• Confidence ≥ 0.8 high certainty<br/>-----<br/>If breakthrough detected:<br/>• type: Positive Discovery only<br/>• description: What patient realized<br/>• label: 2-3 words Major Insight<br/>• evidence: Key quotes from dialogue<br/>• confidence: 0.0-1.0<br/>• timestamps: start + end of moment<br/>-----<br/>User: Conversation turns]

    BREAKTHROUGH_PROMPT_BUILD --> BREAKTHROUGH_API_CALL[🤖 POST OpenAI Chat<br/>Model: gpt-5 o1-preview<br/>Highest reasoning capability<br/>Response format: json_object<br/>Timeout: 120s longer for reasoning]

    BREAKTHROUGH_API_CALL --> BREAKTHROUGH_API_RESPONSE{📡 Response Status?}

    BREAKTHROUGH_API_RESPONSE -->|200 Success| BREAKTHROUGH_PARSE_RESPONSE[📊 Parse JSON Response<br/>Extract:<br/>has_breakthrough: boolean<br/>breakthrough: object or null]

    BREAKTHROUGH_API_RESPONSE -->|429 Rate Limited| BREAKTHROUGH_RATE_LIMIT[⏱️ Rate Limited]
    BREAKTHROUGH_RATE_LIMIT --> BREAKTHROUGH_RETRY_COUNT{🔢 Retries < 3?}
    BREAKTHROUGH_RETRY_COUNT -->|No| BREAKTHROUGH_FAILED[❌ Breakthrough Detection Failed]
    BREAKTHROUGH_RETRY_COUNT -->|Yes| BREAKTHROUGH_BACKOFF[⏸️ Backoff delay]
    BREAKTHROUGH_BACKOFF --> BREAKTHROUGH_API_CALL

    BREAKTHROUGH_API_RESPONSE -->|5xx Server| BREAKTHROUGH_SERVER_ERROR[⚠️ Server Error]
    BREAKTHROUGH_SERVER_ERROR --> BREAKTHROUGH_RETRY_COUNT

    BREAKTHROUGH_PARSE_RESPONSE --> BREAKTHROUGH_HAS_BREAKTHROUGH{💡 has_breakthrough<br/>= true?}

    BREAKTHROUGH_HAS_BREAKTHROUGH -->|No| BREAKTHROUGH_NONE[(💾 UPDATE<br/>has_breakthrough = false<br/>breakthrough_data = null<br/>breakthrough_label = null<br/>breakthrough_analyzed_at = NOW)]

    BREAKTHROUGH_HAS_BREAKTHROUGH -->|Yes| BREAKTHROUGH_VALIDATE_OBJECT{✅ breakthrough<br/>object valid?}

    BREAKTHROUGH_VALIDATE_OBJECT -->|No| BREAKTHROUGH_NONE
    BREAKTHROUGH_VALIDATE_OBJECT -->|Yes| BREAKTHROUGH_CHECK_CONFIDENCE{📊 Confidence ≥ 0.8?<br/>Enforce strict threshold}

    BREAKTHROUGH_CHECK_CONFIDENCE -->|No| BREAKTHROUGH_LOW_CONF[⚠️ Low Confidence Breakthrough<br/>Treat as no breakthrough<br/>Prevents false positives]
    BREAKTHROUGH_LOW_CONF --> BREAKTHROUGH_NONE

    BREAKTHROUGH_CHECK_CONFIDENCE -->|Yes| BREAKTHROUGH_VALIDATE_TYPE{✅ type =<br/>Positive Discovery?}
    BREAKTHROUGH_VALIDATE_TYPE -->|No| BREAKTHROUGH_INVALID_TYPE[⚠️ Invalid Type<br/>Must be Positive Discovery<br/>Reject breakthrough]
    BREAKTHROUGH_INVALID_TYPE --> BREAKTHROUGH_NONE

    BREAKTHROUGH_VALIDATE_TYPE -->|Yes| BREAKTHROUGH_EXTRACT[✨ Extract Breakthrough Data<br/>• type: Positive Discovery<br/>• description: string<br/>• label: 2-3 words<br/>• evidence: array of quotes<br/>• confidence: float 0.8-1.0<br/>• timestamp_start: float seconds<br/>• timestamp_end: float seconds]

    BREAKTHROUGH_EXTRACT --> BREAKTHROUGH_VALIDATE_TIMESTAMPS{✅ Valid Timestamps?<br/>0 ≤ start < end?}
    BREAKTHROUGH_VALIDATE_TIMESTAMPS -->|No| BREAKTHROUGH_FIX_TIMESTAMPS[🔧 Fix Timestamps<br/>Use first/last turn if invalid]
    BREAKTHROUGH_VALIDATE_TIMESTAMPS -->|Yes| BREAKTHROUGH_EXTRACT_DIALOGUE

    BREAKTHROUGH_FIX_TIMESTAMPS --> BREAKTHROUGH_EXTRACT_DIALOGUE[📝 Extract Dialogue Excerpt<br/>Find segments in timestamp range<br/>Format as quote with speaker labels]

    BREAKTHROUGH_EXTRACT_DIALOGUE --> BREAKTHROUGH_VALIDATE_LABEL{✅ Label length<br/>2-15 words?}
    BREAKTHROUGH_VALIDATE_LABEL -->|No| BREAKTHROUGH_DEFAULT_LABEL[⚙️ Default Label<br/>Major Insight]
    BREAKTHROUGH_VALIDATE_LABEL -->|Yes| BREAKTHROUGH_LABEL_OK[✅ Label OK]

    BREAKTHROUGH_DEFAULT_LABEL --> BREAKTHROUGH_STORE_PREPARE
    BREAKTHROUGH_LABEL_OK --> BREAKTHROUGH_STORE_PREPARE

    BREAKTHROUGH_STORE_PREPARE[📦 Prepare Storage Object<br/>BreakthroughAnalysis object]

    BREAKTHROUGH_STORE_PREPARE --> BREAKTHROUGH_STORE[(💾 UPDATE therapy_sessions<br/>SET<br/>has_breakthrough = true<br/>breakthrough_data = JSONB object<br/>  type, description, label,<br/>  evidence, confidence,<br/>  timestamp_start, timestamp_end,<br/>  dialogue_excerpt<br/>breakthrough_label = TEXT short label<br/>breakthrough_analyzed_at = NOW<br/>WHERE id = session_id)]

    BREAKTHROUGH_STORE --> BREAKTHROUGH_LOG[📝 Log Analysis Complete<br/>INSERT analysis_processing_log<br/>wave: breakthrough<br/>status: completed]

    BREAKTHROUGH_TOO_SHORT --> BREAKTHROUGH_NONE
    BREAKTHROUGH_LOG --> BREAKTHROUGH_COMPLETE[✅ Breakthrough Detection Complete]

    %% ============================================================================
    %% WAVE 1 COMPLETION CHECK
    %% ============================================================================
    MOOD_COMPLETE --> WAVE1_CHECK{✔️ All 3 Wave 1<br/>Analyses Complete?}
    MOOD_FAILED --> WAVE1_CHECK
    TOPIC_COMPLETE --> WAVE1_CHECK
    TOPIC_FAILED --> WAVE1_CHECK
    BREAKTHROUGH_COMPLETE --> WAVE1_CHECK
    BREAKTHROUGH_NONE --> WAVE1_CHECK
    BREAKTHROUGH_FAILED --> WAVE1_CHECK

    WAVE1_CHECK --> WAVE1_COUNT[🔢 Count Completed<br/>mood_analyzed_at != null<br/>topics_extracted_at != null<br/>breakthrough_analyzed_at != null]

    WAVE1_COUNT --> WAVE1_ALL_DONE{✅ All 3 Complete?}

    WAVE1_ALL_DONE -->|Yes| MARK_WAVE1_COMPLETE[(💾 UPDATE<br/>analysis_status = wave1_complete<br/>wave1_completed_at = NOW)]

    WAVE1_ALL_DONE -->|No| WAVE1_PARTIAL_CHECK{📊 Any Complete?}
    WAVE1_PARTIAL_CHECK -->|Yes| WAVE1_PARTIAL[⚠️ Wave 1 Partial Success<br/>Some analyses completed<br/>Some failed<br/>Proceed to Wave 2 anyway]
    WAVE1_PARTIAL_CHECK -->|No| WAVE1_TOTAL_FAIL[❌ Wave 1 Total Failure<br/>All 3 analyses failed<br/>Cannot proceed to Wave 2]

    WAVE1_PARTIAL --> MARK_WAVE1_COMPLETE
    WAVE1_TOTAL_FAIL --> MARK_ANALYSIS_FAILED[(💾 UPDATE<br/>analysis_status = failed<br/>error: Wave 1 total failure)]

    %% ============================================================================
    %% WAVE 2: DEEP CLINICAL ANALYSIS
    %% ============================================================================
    MARK_WAVE1_COMPLETE --> UPDATE_WAVE2_STATUS[(💾 UPDATE<br/>analysis_status = wave2_running)]

    UPDATE_WAVE2_STATUS --> WAVE2_START[🧠 DeepAnalyzer.analyze_session<br/>File: services/deep_analyzer.py]

    WAVE2_START --> DEEP_VERIFY_WAVE1{✅ Verify Wave 1<br/>wave1_completed_at != null?}
    DEEP_VERIFY_WAVE1 -->|No| DEEP_ERROR[❌ Error: Wave 1 Not Complete<br/>Cannot run Wave 2]
    DEEP_VERIFY_WAVE1 -->|Yes| DEEP_GATHER_START[📚 Gather Patient Context<br/>Comprehensive data collection]

    DEEP_GATHER_START --> DEEP_FETCH_HISTORY[📥 Fetch Patient History<br/>SELECT * FROM therapy_sessions<br/>WHERE patient_id = X<br/>ORDER BY session_date DESC<br/>LIMIT 10]

    DEEP_FETCH_HISTORY --> DEEP_HISTORY_COUNT{📊 Sessions Found?}
    DEEP_HISTORY_COUNT -->|0| DEEP_FIRST_SESSION[⚠️ First Session<br/>Limited context available]
    DEEP_HISTORY_COUNT -->|1-3| DEEP_EARLY_TREATMENT[📌 Early Treatment<br/>Building context]
    DEEP_HISTORY_COUNT -->|4+| DEEP_ESTABLISHED[✅ Established Treatment<br/>Rich context available]

    DEEP_FIRST_SESSION --> DEEP_MOOD_ANALYSIS
    DEEP_EARLY_TREATMENT --> DEEP_MOOD_ANALYSIS
    DEEP_ESTABLISHED --> DEEP_MOOD_ANALYSIS

    DEEP_MOOD_ANALYSIS[😊 Analyze Mood History<br/>Extract mood_score from each session<br/>Calculate:<br/>• Recent avg: last 3 sessions<br/>• Older avg: sessions 4-10<br/>• Trend: compare recent vs older<br/>  - Improving: recent > older + 0.5<br/>  - Declining: recent < older - 0.5<br/>  - Stable: within ±0.5<br/>  - Variable: high std dev]

    DEEP_MOOD_ANALYSIS --> DEEP_TOPIC_PATTERNS[📋 Analyze Topic Patterns<br/>Extract all topics from history<br/>Calculate frequency:<br/>• Count occurrences per topic<br/>• Find recurring themes<br/>• Identify new vs persistent topics]

    DEEP_TOPIC_PATTERNS --> DEEP_BREAKTHROUGH_TIMELINE[💡 Build Breakthrough Timeline<br/>Filter: has_breakthrough = true<br/>Extract:<br/>• All breakthrough dates<br/>• Breakthrough types<br/>• Labels and descriptions<br/>Sort chronologically]

    DEEP_BREAKTHROUGH_TIMELINE --> DEEP_TECHNIQUE_HISTORY[🛠️ Analyze Technique History<br/>Extract all techniques used<br/>Calculate:<br/>• Frequency per technique<br/>• Modality distribution<br/>• Technique evolution over time]

    DEEP_TECHNIQUE_HISTORY --> DEEP_FETCH_GOALS[🎯 Fetch Active Goals<br/>SELECT * FROM treatment_goals<br/>WHERE patient_id = X<br/>AND status = active]

    DEEP_FETCH_GOALS --> DEEP_CONSISTENCY[📊 Calculate Session Consistency<br/>Metrics:<br/>• Total sessions count<br/>• Average gap between sessions<br/>• Longest streak<br/>• Missed weeks count<br/>• Attendance rate]

    DEEP_CONSISTENCY --> DEEP_SYNTHESIZE_START[🧠 Start GPT-4o Synthesis]

    DEEP_SYNTHESIZE_START --> DEEP_PROMPT_BUILD[📝 Build Comprehensive Prompt<br/>System: You are clinical psychologist<br/>analyzing patient progress<br/>-----<br/>Context Sections:<br/>1. Current Session Wave 1 Results:<br/>   • Mood score + rationale<br/>   • Topics extracted<br/>   • Technique used<br/>   • Breakthrough if any<br/>   • Summary<br/>2. Patient History 10 sessions:<br/>   • Mood trend analysis<br/>   • Topic patterns<br/>   • Breakthrough timeline<br/>   • Technique usage<br/>3. Treatment Context:<br/>   • Active goals<br/>   • Session consistency<br/>   • Total sessions count<br/>-----<br/>Analyze and provide:<br/>• Progress assessment<br/>  overall_direction: improving/stable/declining<br/>  mood_trend: detailed analysis<br/>  engagement_level: high/medium/low<br/>• Clinical insights: array of key observations<br/>• Skills learned: array of demonstrated skills<br/>• Recommendations: array for next session<br/>• Therapeutic relationship: quality assessment<br/>• Confidence score: 0.0-1.0<br/>-----<br/>Response format: JSON object]

    DEEP_PROMPT_BUILD --> DEEP_API_CALL[🤖 POST OpenAI Chat<br/>Model: gpt-4o<br/>Temperature: 0.5 balanced<br/>Max tokens: 2000 comprehensive<br/>Response format: json_object<br/>Timeout: 120s]

    DEEP_API_CALL --> DEEP_API_RESPONSE{📡 Response Status?}

    DEEP_API_RESPONSE -->|200 Success| DEEP_PARSE[📊 Parse Deep Analysis<br/>Extract:<br/>• progress_assessment: object<br/>• clinical_insights: array<br/>• skills_learned: array<br/>• recommendations: array<br/>• therapeutic_relationship: string<br/>• confidence_score: float]

    DEEP_API_RESPONSE -->|429 Rate Limited| DEEP_RATE_LIMIT[⏱️ Rate Limited]
    DEEP_RATE_LIMIT --> DEEP_RETRY_COUNT{🔢 Retries < 3?}
    DEEP_RETRY_COUNT -->|No| DEEP_ANALYSIS_FAILED[❌ Deep Analysis Failed]
    DEEP_RETRY_COUNT -->|Yes| DEEP_BACKOFF[⏸️ Backoff delay]
    DEEP_BACKOFF --> DEEP_API_CALL

    DEEP_API_RESPONSE -->|5xx Server| DEEP_SERVER_ERROR[⚠️ Server Error]
    DEEP_SERVER_ERROR --> DEEP_RETRY_COUNT

    DEEP_PARSE --> DEEP_VALIDATE{✅ Validate Structure?<br/>All required fields present?}
    DEEP_VALIDATE -->|No| DEEP_FIX_STRUCTURE[🔧 Fix Structure<br/>Add default values<br/>for missing fields]
    DEEP_VALIDATE -->|Yes| DEEP_VALIDATE_CONFIDENCE

    DEEP_FIX_STRUCTURE --> DEEP_VALIDATE_CONFIDENCE{✅ Confidence<br/>0.0 ≤ conf ≤ 1.0?}
    DEEP_VALIDATE_CONFIDENCE -->|No| DEEP_DEFAULT_CONF[⚙️ Default = 0.7]
    DEEP_VALIDATE_CONFIDENCE -->|Yes| DEEP_STORE_PREPARE

    DEEP_DEFAULT_CONF --> DEEP_STORE_PREPARE[📦 Prepare Storage<br/>DeepAnalysis object]

    DEEP_STORE_PREPARE --> DEEP_STORE[(💾 UPDATE therapy_sessions<br/>SET<br/>deep_analysis = JSONB object<br/>  progress_assessment,<br/>  clinical_insights,<br/>  skills_learned,<br/>  recommendations,<br/>  therapeutic_relationship<br/>analysis_confidence = 0.XX<br/>deep_analyzed_at = NOW<br/>WHERE id = session_id)]

    DEEP_STORE --> DEEP_LOG[📝 Log Analysis Complete<br/>INSERT analysis_processing_log<br/>wave: deep<br/>status: completed]

    DEEP_LOG --> MARK_COMPLETE[(💾 UPDATE<br/>analysis_status = complete<br/>updated_at = NOW)]

    %% ============================================================================
    %% PHASE 4: FRONTEND DISPLAY & POLLING
    %% ============================================================================
    MARK_COMPLETE --> FRONTEND_POLL_START[🔄 Frontend: Start Polling<br/>Component: ProcessingContext.tsx<br/>Hook: use-processing-status.ts<br/>GET /api/sessions/id/analysis-status<br/>Interval: 2000ms]

    FRONTEND_POLL_START --> POLL_STATUS[📡 Check Status<br/>Fetch analysis_status field]

    POLL_STATUS --> STATUS_CHECK{📊 Status?}

    STATUS_CHECK -->|pending| POLL_WAIT[⏱️ Wait 2 seconds<br/>Continue polling]
    STATUS_CHECK -->|wave1_running| POLL_WAIT
    STATUS_CHECK -->|wave1_complete| POLL_WAIT
    STATUS_CHECK -->|wave2_running| POLL_WAIT
    STATUS_CHECK -->|processing| POLL_WAIT

    POLL_WAIT --> POLL_STATUS

    STATUS_CHECK -->|complete| STOP_POLLING[🛑 Stop Polling<br/>Analysis Pipeline Complete<br/>Clear interval]

    STATUS_CHECK -->|failed| SHOW_ERROR[❌ Show Error to User<br/>Display: Analysis failed<br/>Retry option available]

    STOP_POLLING --> REFRESH_DASHBOARD[🔄 Trigger Dashboard Refresh<br/>Invalidate SWR cache<br/>Refetch session data]

    REFRESH_DASHBOARD --> FETCH_SESSION[📡 GET /api/sessions/id<br/>Fetch complete session with:<br/>• Transcript<br/>• Mood analysis<br/>• Topics<br/>• Breakthrough<br/>• Deep analysis<br/>• All metadata]

    FETCH_SESSION --> UPDATE_UI[📱 Update React Components<br/>Re-render with new data]

    UPDATE_UI --> SESSION_CARD[📋 SessionCard Component<br/>File: components/SessionCard.tsx<br/>Display:<br/>• session_date formatted<br/>• summary max 150 chars<br/>• topics badges<br/>• technique badge<br/>• mood_score with color<br/>  - 0-4: rose red<br/>  - 4-6: blue neutral<br/>  - 6-10: green positive<br/>• breakthrough amber star if present]

    UPDATE_UI --> PROGRESS_CARD[📈 ProgressPatternsCard Component<br/>File: components/ProgressPatternsCard.tsx<br/>Display:<br/>• Mood history line chart<br/>  - X-axis: session dates<br/>  - Y-axis: mood_score 0-10<br/>• Trend indicator:<br/>  - ↗️ Improving green arrow<br/>  - → Stable blue dash<br/>  - ↘️ Declining rose arrow<br/>• Latest mood score large<br/>• Trend description text]

    UPDATE_UI --> NOTES_CARD[📝 NotesGoalsCard Component<br/>File: components/NotesGoalsCard.tsx<br/>Display:<br/>• Action items from session<br/>  - Checkbox interactive<br/>  - Text from action_items array<br/>• Active treatment goals<br/>  - Progress bar visual<br/>  - Target date<br/>  - Status badge]

    UPDATE_UI --> BREAKTHROUGH_CARD[💡 TherapistBridgeCard Component<br/>File: components/TherapistBridgeCard.tsx<br/>If has_breakthrough = true:<br/>Display:<br/>• Amber star icon glow<br/>• breakthrough_label as title<br/>• Description excerpt<br/>• View Details button<br/>  → Opens MajorEventModal<br/>• Evidence quotes<br/>• Confidence score bar]

    SESSION_CARD --> USER_VIEW([👤 USER VIEWS<br/>COMPLETE ANALYSIS<br/>All AI insights displayed])
    PROGRESS_CARD --> USER_VIEW
    NOTES_CARD --> USER_VIEW
    BREAKTHROUGH_CARD --> USER_VIEW

    USER_VIEW --> END_SUCCESS([✅ END: Pipeline Complete<br/>Duration: ~3 minutes<br/>Cost: ~$0.42])

    %% ============================================================================
    %% ERROR PATHS TO END
    %% ============================================================================
    ERROR_AUTH --> END_FAILED([❌ END: Pipeline Failed])
    ERROR_TYPE --> END_FAILED
    ERROR_SIZE_UPLOAD --> END_FAILED
    ERROR_DURATION --> END_FAILED
    ERROR_UPLOAD_CLIENT --> END_FAILED
    ERROR_UPLOAD_FINAL --> END_FAILED
    ERROR_URL --> END_FAILED
    ERROR_VALIDATION --> END_FAILED
    ERROR_DB_INSERT --> END_FAILED
    ERROR_SESSION_NOT_FOUND --> END_FAILED
    ERROR_DUPLICATE_PROCESS --> END_FAILED
    ERROR_DOWNLOAD --> END_FAILED
    ERROR_FILE_MISSING --> END_FAILED
    ERROR_CORRUPT_AUDIO --> END_FAILED
    ERROR_TOO_SHORT --> END_FAILED
    ERROR_EXPORT --> END_FAILED
    ERROR_SIZE_WHISPER --> END_FAILED
    ERROR_WHISPER_RATE --> END_FAILED
    ERROR_WHISPER_AUTH --> END_FAILED
    ERROR_WHISPER_INVALID --> END_FAILED
    ERROR_WHISPER_EMPTY --> END_FAILED
    ERROR_PYANNOTE_TOKEN --> END_FAILED
    ERROR_MODEL_LOAD --> END_FAILED
    ERROR_PYANNOTE_EMPTY --> END_FAILED
    ERROR_MERGE --> END_FAILED
    ERROR_LABELING --> END_FAILED
    ERROR_NO_TRANSCRIPT --> END_FAILED
    MOOD_ERROR --> MARK_ANALYSIS_FAILED
    ERROR_MOOD_AUTH --> MARK_ANALYSIS_FAILED
    DEEP_ERROR --> MARK_ANALYSIS_FAILED
    DEEP_ANALYSIS_FAILED --> MARK_ANALYSIS_FAILED
    MARK_ANALYSIS_FAILED --> SHOW_ERROR
    SHOW_ERROR --> END_FAILED

    %% ============================================================================
    %% STYLING
    %% ============================================================================
    classDef uploadClass fill:#E3F2FD,stroke:#1976D2,stroke-width:2px,color:#000
    classDef pipelineClass fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#000
    classDef aiClass fill:#FFF3E0,stroke:#F57C00,stroke-width:2px,color:#000
    classDef dbClass fill:#E8F5E9,stroke:#388E3C,stroke-width:2px,color:#000
    classDef errorClass fill:#FFEBEE,stroke:#C62828,stroke-width:2px,color:#000
    classDef frontendClass fill:#E0F2F1,stroke:#00796B,stroke-width:2px,color:#000
    classDef successClass fill:#C8E6C9,stroke:#388E3C,stroke-width:3px,color:#000
    classDef legendClass fill:#FFF9C4,stroke:#F9A825,stroke-width:1px,color:#000

    class START,UPLOAD_MODAL,CHECK_AUTH,VALIDATE_FILE,CHECK_SIZE,CHECK_TYPE,CHECK_DURATION,DURATION_VALID,PREPARE_UPLOAD,STORAGE_UPLOAD,UPLOAD_CHECK,GET_PUBLIC_URL,VALIDATE_URL,CREATE_SESSION_REQ,VALIDATE_SESSION_DATA uploadClass

    class PREPROCESS_START,LOAD_AUDIO,DETECT_CHANNELS,CONVERT_MONO,CHECK_SAMPLE_RATE,RESAMPLE,DETECT_SILENCE,TRIM_START,TRIM_END,ANALYZE_VOLUME,NORMALIZE_VOLUME,CHECK_CLIPPING,APPLY_LIMITER,CONVERT_FORMAT,EXPORT_TEMP,VALIDATE_OUTPUT,PREPROCESSED_AUDIO,WHISPER_CALL,WHISPER_PARSE,WHISPER_CLEAN,WHISPER_SUCCESS,PYANNOTE_CALL,PYANNOTE_PROCESS,PYANNOTE_COMPLETE,PYANNOTE_LABEL,PYANNOTE_SUCCESS,MERGE_START,MERGE_ITERATE,FIND_OVERLAP,ASSIGN_SPEAKER,MERGED_SEGMENTS,DIARIZED_TRANSCRIPT,ROLE_DETECTION_START,CALC_STATS,CALC_SPEAKING_TIME,CALC_RATIO,CALC_SEGMENTS,CALC_AVG_LENGTH,IDENTIFY_FIRST,HEURISTIC_1,HEURISTIC_2,ASSIGN_ROLES,REPLACE_LABELS,LABELED_TRANSCRIPT,CALCULATE_FINAL_STATS pipelineClass

    class QUICK_AI_START,QUICK_AI_PROMPT,QUICK_AI_CALL,QUICK_AI_PARSE,MOOD_PROMPT_BUILD,MOOD_API_CALL,MOOD_PARSE,TOPIC_PROMPT_BUILD,TOPIC_API_CALL,TOPIC_PARSE,BREAKTHROUGH_PROMPT_BUILD,BREAKTHROUGH_API_CALL,BREAKTHROUGH_PARSE_RESPONSE,BREAKTHROUGH_EXTRACT,DEEP_PROMPT_BUILD,DEEP_API_CALL,DEEP_PARSE aiClass

    class DB_INSERT,UPDATE_STATUS_PROCESSING,UPDATE_PROGRESS_10,UPDATE_PROGRESS_20,UPDATE_PROGRESS_80,UPDATE_PROGRESS_85,UPDATE_TRANSCRIPT_DB,UPDATE_WAVE1_STATUS,UPDATE_WAVE2_STATUS,MOOD_STORE,TOPIC_STORE,BREAKTHROUGH_STORE,BREAKTHROUGH_NONE,DEEP_STORE,MARK_WAVE1_COMPLETE,MARK_COMPLETE dbClass

    class ERROR_AUTH,ERROR_TYPE,ERROR_SIZE_UPLOAD,ERROR_DURATION,ERROR_UPLOAD_CLIENT,ERROR_UPLOAD_SERVER,ERROR_UPLOAD_FINAL,ERROR_URL,ERROR_VALIDATION,ERROR_DB_INSERT,ERROR_SESSION_NOT_FOUND,ERROR_DUPLICATE_PROCESS,ERROR_DOWNLOAD,ERROR_FILE_MISSING,ERROR_CORRUPT_AUDIO,ERROR_TOO_SHORT,ERROR_EXPORT,ERROR_SIZE_WHISPER,ERROR_WHISPER_RATE,ERROR_WHISPER_AUTH,ERROR_WHISPER_INVALID,ERROR_WHISPER_EMPTY,ERROR_PYANNOTE_TOKEN,ERROR_MODEL_LOAD,ERROR_PYANNOTE_EMPTY,ERROR_MERGE,ERROR_LABELING,ERROR_NO_TRANSCRIPT,MOOD_ERROR,ERROR_MOOD_AUTH,MOOD_FAILED,TOPIC_FAILED,BREAKTHROUGH_FAILED,DEEP_ERROR,DEEP_ANALYSIS_FAILED,MARK_ANALYSIS_FAILED,SHOW_ERROR errorClass

    class FRONTEND_POLL_START,POLL_STATUS,STATUS_CHECK,STOP_POLLING,REFRESH_DASHBOARD,FETCH_SESSION,UPDATE_UI,SESSION_CARD,PROGRESS_CARD,NOTES_CARD,BREAKTHROUGH_CARD frontendClass

    class END_SUCCESS,USER_VIEW successClass

    class L1,L2,L3,L4,L5,L6 legendClass
```

---

## Flowchart Statistics

- **Total Nodes:** 400+ nodes (ultra-detailed)
- **Decision Points:** 80+ conditional branches
- **Error Paths:** 35+ error handling flows
- **Retry Logic:** 8 retry mechanisms with exponential backoff
- **Database Operations:** 25+ UPDATE/INSERT operations
- **API Calls:** 7 external API integrations (OpenAI, Supabase, Pyannote)
- **Validation Steps:** 50+ validation checks
- **Phases:** 6 major phases with sub-phases

## Key Features

✅ **Every validation step** explicitly shown
✅ **All retry logic** with backoff calculations
✅ **Complete error paths** leading to failure states
✅ **Database schema details** in UPDATE nodes
✅ **API response codes** 200, 429, 401, 5xx handled
✅ **Confidence thresholds** for AI decisions
✅ **Data transformations** documented
✅ **File paths** included in service nodes
✅ **Timeout values** specified
✅ **Color-coded by phase** for easy navigation

## How to View

**Best Option:** Paste into **mermaid.live** (handles large diagrams best)

1. Copy the entire ` ```mermaid ... ``` ` block above
2. Go to https://mermaid.live
3. Paste into editor
4. Zoom out to see full diagram
5. Export as SVG/PNG if needed

**Alternative:** GitHub/GitLab (may need horizontal scrolling)

## Legend

- 🔵 **Blue** - Upload/Storage operations
- 🟣 **Purple** - Audio processing (Whisper, Pyannote)
- 🟠 **Orange** - AI analysis (GPT models)
- 🟢 **Green** - Database operations
- 🔴 **Red** - Errors and failures
- 🟡 **Yellow** - Frontend display/polling

---

**This is the most detailed algorithmic flowchart possible** - every decision, every retry, every validation, every error path documented.
