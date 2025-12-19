"""
Example usage of ProgressCalculator for audio processing pipeline

This demonstrates how to integrate the progress calculator into your
session processing endpoints.
"""

from app.services.progress_calculator import (
    ProgressCalculator,
    ProcessingStage,
    get_progress_calculator
)
import time


def example_basic_usage():
    """Basic usage: Calculate progress at different stages"""
    calc = get_progress_calculator()

    print("=== Basic Progress Calculation ===\n")

    # Stage 1: Uploading (0-5%)
    progress = calc.calculate_progress(ProcessingStage.UPLOADING, sub_progress=0.0)
    print(f"Upload started: {progress}%")

    progress = calc.calculate_progress(ProcessingStage.UPLOADING, sub_progress=0.5)
    print(f"Upload 50% complete: {progress}%")

    progress = calc.calculate_progress(ProcessingStage.UPLOADING, sub_progress=1.0)
    print(f"Upload finished: {progress}%")

    # Stage 2: Transcribing (15-55%, largest weight)
    progress = calc.calculate_progress(ProcessingStage.TRANSCRIBING, sub_progress=0.0)
    print(f"\nTranscription started: {progress}%")

    progress = calc.calculate_progress(ProcessingStage.TRANSCRIBING, sub_progress=0.5)
    print(f"Transcription 50% complete: {progress}%")

    progress = calc.calculate_progress(ProcessingStage.TRANSCRIBING, sub_progress=1.0)
    print(f"Transcription finished: {progress}%")


def example_time_estimation():
    """Example: Estimate time remaining during processing"""
    calc = get_progress_calculator()

    print("\n=== Time Estimation ===\n")

    # Scenario: 2 minutes elapsed, 35% complete
    elapsed_seconds = 120
    current_progress = 35

    remaining = calc.estimate_time_remaining(current_progress, elapsed_seconds)

    if remaining:
        minutes = remaining // 60
        seconds = remaining % 60
        print(f"Current progress: {current_progress}%")
        print(f"Time elapsed: {elapsed_seconds}s")
        print(f"Estimated time remaining: {minutes}m {seconds}s")
    else:
        print("Not enough progress data for estimation yet")


def example_stage_info():
    """Example: Get detailed information about stages"""
    calc = get_progress_calculator()

    print("\n=== Stage Information ===\n")

    # Get info for a specific stage
    info = calc.get_stage_info(ProcessingStage.TRANSCRIBING)
    print(f"Stage: {info['stage']}")
    print(f"Progress range: {info['start_percent']}% - {info['end_percent']}%")
    print(f"Weight: {info['weight_percent']}%")
    print(f"Description: {info['description']}")

    # Get info for all stages
    print("\n=== All Stages ===\n")
    all_stages = calc.get_all_stages_info()
    for stage_info in all_stages:
        print(f"{stage_info['stage']:20} | "
              f"{stage_info['start_percent']:3}% - {stage_info['end_percent']:3}% | "
              f"Weight: {stage_info['weight_percent']:2}%")


def example_realistic_pipeline_simulation():
    """
    Realistic example: Simulate full pipeline with progress updates

    This shows how you would integrate progress tracking into your
    actual session processing workflow.
    """
    calc = get_progress_calculator()

    print("\n=== Realistic Pipeline Simulation ===\n")

    start_time = time.time()

    def update_progress(stage: ProcessingStage, sub_progress: float):
        """Helper to print progress updates"""
        progress = calc.calculate_progress(stage, sub_progress)
        elapsed = time.time() - start_time
        remaining = calc.estimate_time_remaining(progress, elapsed)

        info = calc.get_stage_info(stage)
        print(f"[{elapsed:5.1f}s] {info['description']:50} | "
              f"Progress: {progress:3}% | ", end="")

        if remaining:
            print(f"ETA: {remaining}s remaining")
        else:
            print("ETA: Calculating...")

    # Simulate pipeline progression
    update_progress(ProcessingStage.UPLOADING, 0.0)
    time.sleep(0.2)
    update_progress(ProcessingStage.UPLOADING, 0.5)
    time.sleep(0.2)
    update_progress(ProcessingStage.UPLOADING, 1.0)

    update_progress(ProcessingStage.PREPROCESSING, 0.0)
    time.sleep(0.2)
    update_progress(ProcessingStage.PREPROCESSING, 0.5)
    time.sleep(0.2)
    update_progress(ProcessingStage.PREPROCESSING, 1.0)

    update_progress(ProcessingStage.TRANSCRIBING, 0.0)
    time.sleep(0.2)
    update_progress(ProcessingStage.TRANSCRIBING, 0.25)
    time.sleep(0.2)
    update_progress(ProcessingStage.TRANSCRIBING, 0.5)
    time.sleep(0.2)
    update_progress(ProcessingStage.TRANSCRIBING, 0.75)
    time.sleep(0.2)
    update_progress(ProcessingStage.TRANSCRIBING, 1.0)

    update_progress(ProcessingStage.DIARIZING, 0.0)
    time.sleep(0.2)
    update_progress(ProcessingStage.DIARIZING, 0.5)
    time.sleep(0.2)
    update_progress(ProcessingStage.DIARIZING, 1.0)

    update_progress(ProcessingStage.GENERATING_NOTES, 0.0)
    time.sleep(0.2)
    update_progress(ProcessingStage.GENERATING_NOTES, 0.5)
    time.sleep(0.2)
    update_progress(ProcessingStage.GENERATING_NOTES, 1.0)

    update_progress(ProcessingStage.SAVING, 0.0)
    time.sleep(0.1)
    update_progress(ProcessingStage.SAVING, 1.0)

    total_elapsed = time.time() - start_time
    print(f"\n✓ Pipeline complete in {total_elapsed:.1f}s")


def example_fastapi_integration():
    """
    Example: How to integrate with FastAPI endpoint

    This shows a typical pattern for updating progress in a database
    during session processing.
    """
    print("\n=== FastAPI Integration Example ===\n")

    code = """
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.progress_calculator import get_progress_calculator, ProcessingStage
import time

router = APIRouter()

async def process_audio_with_progress(
    session_id: int,
    audio_path: str,
    db: Session
):
    '''Background task that processes audio and updates progress'''
    calc = get_progress_calculator()
    start_time = time.time()

    def update_db_progress(stage: ProcessingStage, sub_progress: float):
        '''Update session progress in database'''
        progress = calc.calculate_progress(stage, sub_progress)
        elapsed = time.time() - start_time
        remaining = calc.estimate_time_remaining(progress, elapsed)

        # Update database
        db.execute(
            "UPDATE therapy_sessions SET "
            "processing_progress = :progress, "
            "processing_stage = :stage, "
            "estimated_time_remaining = :remaining "
            "WHERE id = :session_id",
            {
                'progress': progress,
                'stage': stage.value,
                'remaining': remaining,
                'session_id': session_id
            }
        )
        db.commit()

    try:
        # Stage 1: Upload (already done when this starts)
        update_db_progress(ProcessingStage.UPLOADING, 1.0)

        # Stage 2: Preprocessing
        update_db_progress(ProcessingStage.PREPROCESSING, 0.0)
        preprocessed_audio = await preprocess_audio(audio_path)
        update_db_progress(ProcessingStage.PREPROCESSING, 1.0)

        # Stage 3: Transcription (with incremental updates)
        update_db_progress(ProcessingStage.TRANSCRIBING, 0.0)
        # Whisper API doesn't give sub-progress, but you can estimate
        # based on file duration vs. expected processing time
        transcription = await transcribe_audio(preprocessed_audio)
        update_db_progress(ProcessingStage.TRANSCRIBING, 1.0)

        # Stage 4: Diarization
        update_db_progress(ProcessingStage.DIARIZING, 0.0)
        diarization = await diarize_audio(preprocessed_audio)
        update_db_progress(ProcessingStage.DIARIZING, 1.0)

        # Stage 5: Note generation
        update_db_progress(ProcessingStage.GENERATING_NOTES, 0.0)
        notes = await generate_notes(transcription)
        update_db_progress(ProcessingStage.GENERATING_NOTES, 1.0)

        # Stage 6: Save results
        update_db_progress(ProcessingStage.SAVING, 0.0)
        await save_results(session_id, transcription, diarization, notes, db)
        update_db_progress(ProcessingStage.SAVING, 1.0)

        # Mark as completed
        db.execute(
            "UPDATE therapy_sessions SET "
            "processing_status = :status, "
            "processing_progress = 100 "
            "WHERE id = :session_id",
            {'status': ProcessingStage.COMPLETED.value, 'session_id': session_id}
        )
        db.commit()

    except Exception as e:
        # Mark as failed
        db.execute(
            "UPDATE therapy_sessions SET "
            "processing_status = :status "
            "WHERE id = :session_id",
            {'status': ProcessingStage.FAILED.value, 'session_id': session_id}
        )
        db.commit()
        raise


@router.post("/sessions/{session_id}/process")
async def process_session(
    session_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    '''Endpoint to start audio processing with progress tracking'''
    # Get audio path from database
    result = db.execute(
        "SELECT audio_file_path FROM therapy_sessions WHERE id = :id",
        {'id': session_id}
    ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    audio_path = result[0]

    # Start background processing
    background_tasks.add_task(process_audio_with_progress, session_id, audio_path, db)

    return {
        "status": "processing_started",
        "session_id": session_id,
        "message": "Audio processing started. Poll /sessions/{id}/progress for updates."
    }


@router.get("/sessions/{session_id}/progress")
async def get_processing_progress(session_id: int, db: Session = Depends(get_db)):
    '''Endpoint to poll current progress'''
    result = db.execute(
        "SELECT processing_progress, processing_stage, estimated_time_remaining "
        "FROM therapy_sessions WHERE id = :id",
        {'id': session_id}
    ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    progress, stage, eta = result

    calc = get_progress_calculator()
    stage_info = calc.get_stage_info(ProcessingStage(stage))

    return {
        "session_id": session_id,
        "progress": progress,
        "stage": stage,
        "stage_description": stage_info['description'],
        "estimated_time_remaining": eta
    }
"""

    print(code)


if __name__ == "__main__":
    example_basic_usage()
    example_time_estimation()
    example_stage_info()
    example_realistic_pipeline_simulation()
    example_fastapi_integration()
