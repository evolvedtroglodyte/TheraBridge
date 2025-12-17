#!/usr/bin/env python3
"""
Parallel GPU Racing Strategy for Vast.ai
Spins up multiple instances simultaneously, uses first to complete, destroys stragglers
"""

import os
import sys
import time
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional

# Import the existing VastAI automation
from run_gpu_vast import VastAIGPUPipeline


class ParallelGPURacer:
    """
    Runs multiple GPU instances in parallel, returns first successful result
    Automatically destroys slower instances to minimize cost
    """

    def __init__(self, num_racers: int = 2, verbose: bool = True):
        """
        Initialize parallel GPU racer

        Args:
            num_racers: Number of instances to spin up in parallel (2-5 recommended)
            verbose: Print detailed progress
        """
        self.num_racers = num_racers
        self.verbose = verbose
        self.active_instances = []

    def _log(self, message: str):
        """Print if verbose"""
        if self.verbose:
            print(message)

    def _run_single_pipeline(self,
                            racer_id: int,
                            audio_file: str,
                            num_speakers: int,
                            whisper_model: str,
                            ssh_timeout: int) -> Dict:
        """
        Run pipeline on a single GPU instance (for parallel execution)

        Args:
            racer_id: Unique ID for this racer
            audio_file: Path to audio file
            num_speakers: Number of speakers
            whisper_model: Whisper model name
            ssh_timeout: SSH connection timeout

        Returns:
            Dict with results and metadata
        """
        try:
            self._log(f"\n[Racer {racer_id}] Starting pipeline...")

            pipeline = VastAIGPUPipeline(verbose=self.verbose)

            # Track this instance
            start_time = time.time()

            results = pipeline.run_pipeline(
                audio_file=audio_file,
                num_speakers=num_speakers,
                whisper_model=whisper_model,
                cleanup=False,  # Don't auto-cleanup - we'll manage manually
                ssh_timeout=ssh_timeout
            )

            elapsed = time.time() - start_time

            return {
                'racer_id': racer_id,
                'instance_id': pipeline.instance_id,
                'results': results,
                'elapsed_time': elapsed,
                'success': True,
                'pipeline': pipeline
            }

        except Exception as e:
            self._log(f"[Racer {racer_id}] Failed: {e}")
            return {
                'racer_id': racer_id,
                'instance_id': getattr(pipeline, 'instance_id', None) if 'pipeline' in locals() else None,
                'error': str(e),
                'success': False,
                'pipeline': pipeline if 'pipeline' in locals() else None
            }

    def race(self,
             audio_file: str,
             num_speakers: int = 2,
             whisper_model: str = "large-v3",
             ssh_timeout: int = 300) -> Dict:
        """
        Run parallel GPU race

        Args:
            audio_file: Path to audio file
            num_speakers: Number of speakers
            whisper_model: Whisper model name
            ssh_timeout: SSH connection timeout per instance

        Returns:
            Results from fastest successful pipeline
        """
        self._log(f"\n{'='*60}")
        self._log(f"Parallel GPU Race - {self.num_racers} instances")
        self._log(f"{'='*60}\n")

        winner = None
        all_pipelines = []

        # Launch all racers in parallel
        with ThreadPoolExecutor(max_workers=self.num_racers) as executor:
            futures = {
                executor.submit(
                    self._run_single_pipeline,
                    racer_id=i,
                    audio_file=audio_file,
                    num_speakers=num_speakers,
                    whisper_model=whisper_model,
                    ssh_timeout=ssh_timeout
                ): i for i in range(1, self.num_racers + 1)
            }

            # Wait for first success
            for future in as_completed(futures):
                result = future.result()
                all_pipelines.append(result)

                if result['success'] and winner is None:
                    winner = result
                    self._log(f"\n🏆 [Racer {result['racer_id']}] WINNER!")
                    self._log(f"Instance: {result['instance_id']}")
                    self._log(f"Time: {result['elapsed_time']:.1f}s")

                    # Cancel remaining futures (they may still complete, but we don't wait)
                    for f in futures:
                        f.cancel()

                    break

        # Cleanup: Destroy all instances except winner
        self._log(f"\n{'='*60}")
        self._log("Cleanup - Destroying slower instances")
        self._log(f"{'='*60}\n")

        for result in all_pipelines:
            pipeline = result.get('pipeline')
            instance_id = result.get('instance_id')

            if pipeline and instance_id:
                if result == winner:
                    # Destroy winner instance too (we already downloaded results)
                    self._log(f"[Racer {result['racer_id']}] Destroying winner instance {instance_id}")
                    try:
                        pipeline.destroy_instance(instance_id)
                    except Exception as e:
                        self._log(f"Warning: Failed to destroy winner: {e}")
                else:
                    # Destroy losers
                    self._log(f"[Racer {result['racer_id']}] Destroying slower instance {instance_id}")
                    try:
                        pipeline.destroy_instance(instance_id)
                    except Exception as e:
                        self._log(f"Warning: Failed to destroy loser: {e}")

        if not winner:
            raise RuntimeError("All GPU instances failed. Try again or check configuration.")

        return winner['results']


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(
        description="Run GPU pipeline with parallel racing strategy"
    )
    parser.add_argument(
        'audio_file',
        help='Path to audio file to process'
    )
    parser.add_argument(
        '--num-speakers',
        type=int,
        default=2,
        help='Number of speakers for diarization (default: 2)'
    )
    parser.add_argument(
        '--whisper-model',
        default='large-v3',
        help='Whisper model size (default: large-v3)'
    )
    parser.add_argument(
        '--num-racers',
        type=int,
        default=2,
        help='Number of parallel instances to race (default: 2)'
    )
    parser.add_argument(
        '--ssh-timeout',
        type=int,
        default=300,
        help='SSH connection timeout in seconds (default: 300)'
    )

    args = parser.parse_args()

    try:
        racer = ParallelGPURacer(num_racers=args.num_racers, verbose=True)

        results = racer.race(
            audio_file=args.audio_file,
            num_speakers=args.num_speakers,
            whisper_model=args.whisper_model,
            ssh_timeout=args.ssh_timeout
        )

        print("\n" + "="*60)
        print("SUCCESS!")
        print("="*60)
        print(f"Duration: {results.get('duration', 0):.1f}s")
        print(f"Segments: {len(results.get('segments', []))}")
        print(f"Provider: {results.get('provider', 'unknown')}")
        print("="*60 + "\n")

        return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
