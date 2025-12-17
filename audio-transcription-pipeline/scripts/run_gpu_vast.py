#!/usr/bin/env python3
"""
Automated Vast.ai GPU Pipeline Executor
Handles: instance creation, file transfer, execution, result download, cleanup
"""

import os
import sys
import time
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Optional, Tuple


class VastAIGPUPipeline:
    """Automates GPU transcription pipeline on Vast.ai"""

    def __init__(self, api_key: Optional[str] = None, verbose: bool = True):
        """
        Initialize Vast.ai automation

        Args:
            api_key: Vast.ai API key (defaults to VAST_API_KEY env var)
            verbose: Print detailed progress
        """
        # Try to load from .env file FIRST (for both VAST_API_KEY and HF_TOKEN)
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass  # python-dotenv not installed, continue

        self.api_key = api_key or os.getenv('VAST_API_KEY')
        if not self.api_key:
            raise ValueError(
                "VAST_API_KEY not found. Set it via environment variable or pass directly.\n"
                "Get your API key at: https://cloud.vast.ai/cli/"
            )

        os.environ['VAST_API_KEY'] = self.api_key
        self.verbose = verbose
        self.instance_id = None
        self.ssh_info = {}

        # Verify vastai CLI is installed
        self._verify_cli()

    def _verify_cli(self):
        """Verify vastai CLI is installed"""
        try:
            subprocess.run(['vastai', '--version'],
                         capture_output=True, check=True)
            self._log("✓ Vast.ai CLI found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "Vast.ai CLI not installed. Install with:\n"
                "  pip install vastai"
            )

    def _log(self, message: str):
        """Print if verbose"""
        if self.verbose:
            print(message)

    def _run_cmd(self, cmd: str, check: bool = True, stream_output: bool = False) -> Tuple[str, str, int]:
        """
        Run shell command and return output

        Args:
            cmd: Command to run
            check: Raise error on non-zero exit
            stream_output: Stream output in real-time (for long-running commands)
        """
        self._log(f"$ {cmd}")

        if stream_output:
            # Stream output in real-time for long-running commands
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )

            stdout_lines = []
            stderr_lines = []

            # Read output as it comes
            import select
            while True:
                # Check if process is done
                if process.poll() is not None:
                    # Read any remaining output
                    remaining_out = process.stdout.read()
                    remaining_err = process.stderr.read()
                    if remaining_out:
                        stdout_lines.append(remaining_out)
                        print(remaining_out, end='', flush=True)
                    if remaining_err:
                        stderr_lines.append(remaining_err)
                        print(remaining_err, end='', flush=True)
                    break

                # Read available output
                try:
                    line = process.stdout.readline()
                    if line:
                        stdout_lines.append(line)
                        print(line, end='', flush=True)
                except:
                    pass

            stdout = ''.join(stdout_lines)
            stderr = ''.join(stderr_lines)
            returncode = process.returncode

        else:
            # Original buffered approach for fast commands
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=False,  # Get bytes instead of text
                check=False
            )

            # Decode with error handling
            stdout = result.stdout.decode('utf-8', errors='replace') if result.stdout else ''
            stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ''
            returncode = result.returncode

        if check and returncode != 0:
            raise RuntimeError(f"Command failed: {cmd}\n{stderr}")

        return stdout, stderr, returncode

    def search_instances(self,
                        gpu_ram_min: int = 16,
                        cuda_version_min: float = 12.0,
                        disk_min: int = 50,
                        bandwidth_min: int = 500,
                        max_price_per_hour: Optional[float] = None) -> list:
        """
        Search for suitable GPU instances

        Args:
            gpu_ram_min: Minimum GPU RAM in GB
            cuda_version_min: Minimum CUDA version
            disk_min: Minimum disk space in GB
            bandwidth_min: Minimum download bandwidth in Mbps
            max_price_per_hour: Maximum price per hour (optional)

        Returns:
            List of available offers sorted by price
        """
        self._log("\n=== Searching for GPU instances ===")

        query_parts = [
            f'gpu_ram>={gpu_ram_min}',
            f'cuda_vers>={cuda_version_min}',
            f'disk_space>={disk_min}',
            f'inet_down>={bandwidth_min}',
            'rented=False',
            'reliability>0.95'
        ]

        if max_price_per_hour:
            query_parts.append(f'dph<={max_price_per_hour}')

        query = ' '.join(query_parts)

        stdout, _, _ = self._run_cmd(
            f'vastai search offers "{query}" -o "dph+" --raw'
        )

        data = json.loads(stdout)
        offers = data if isinstance(data, list) else []

        self._log(f"Found {len(offers)} suitable offers")

        if offers and self.verbose:
            # Show top 3 offers
            for i, offer in enumerate(offers[:3]):
                gpu_name = offer.get('gpu_name', 'Unknown')
                gpu_ram = offer.get('gpu_ram', 0)
                dph = offer.get('dph_total', 0)
                reliability = offer.get('reliability2', 0)
                self._log(f"  {i+1}. {gpu_name} ({gpu_ram}GB) - ${dph:.3f}/hr - {reliability:.1%} reliable")

        return offers

    def create_instance(self,
                       offer_id: int,
                       image: str = "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime",
                       disk_gb: int = 64,
                       label: Optional[str] = None) -> str:
        """
        Create GPU instance

        Args:
            offer_id: Offer ID from search results
            image: Docker image to use
            disk_gb: Disk size in GB
            label: Custom label for instance

        Returns:
            Instance ID
        """
        self._log("\n=== Creating GPU instance ===")

        if not label:
            label = f"audio-pipeline-{int(time.time())}"

        cmd = (
            f'vastai create instance {offer_id} '
            f'--image {image} '
            f'--disk {disk_gb} '
            f'--ssh '
            f'--direct '
            f'--label "{label}"'
        )

        stdout, _, _ = self._run_cmd(cmd)

        # Parse instance ID from output
        # Output format: "Started. {instance_id}" or just the ID
        lines = stdout.strip().split('\n')

        # Try to find instance ID in output
        import re
        for line in lines:
            # Look for numeric ID (possibly with trailing characters)
            match = re.search(r'(\d+)', line)
            if match:
                self.instance_id = match.group(1)
                break

        if not self.instance_id:
            raise RuntimeError(f"Failed to parse instance ID from: {stdout}")

        self._log(f"✓ Created instance: {self.instance_id}")

        # Auto-start the instance (in case it's not auto-started)
        self._log("Ensuring instance is started...")
        self._run_cmd(f'vastai start instance {self.instance_id}', check=False)

        return self.instance_id

    def wait_for_ssh(self, instance_id: str, timeout: int = 180) -> Dict:
        """
        Wait for instance to be SSH-ready

        Args:
            instance_id: Instance ID
            timeout: Maximum wait time in seconds

        Returns:
            SSH connection info dict
        """
        self._log("\n=== Waiting for SSH connection ===")

        start = time.time()
        attempts = 0

        while time.time() - start < timeout:
            attempts += 1

            try:
                stdout, _, code = self._run_cmd(
                    f'vastai show instance {instance_id} --raw',
                    check=False
                )

                if code == 0:
                    data = json.loads(stdout)

                    ssh_host = data.get('ssh_host')
                    ssh_port = data.get('ssh_port')
                    actual_status = data.get('actual_status')

                    if ssh_host and ssh_port and actual_status == 'running':
                        self.ssh_info = {
                            'host': ssh_host,
                            'port': ssh_port,
                            'user': 'root'
                        }

                        # Test SSH connection
                        test_cmd = f'ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -p {ssh_port} root@{ssh_host} "echo ready"'
                        stdout, _, code = self._run_cmd(test_cmd, check=False)

                        if code == 0 and 'ready' in stdout:
                            elapsed = time.time() - start
                            self._log(f"✓ SSH ready at {ssh_host}:{ssh_port} (took {elapsed:.1f}s)")
                            return self.ssh_info

            except (json.JSONDecodeError, KeyError):
                pass

            if attempts % 6 == 0:  # Every 30 seconds
                self._log(f"  Waiting... ({int(time.time() - start)}s elapsed)")

            time.sleep(5)

        raise TimeoutError(f"Instance {instance_id} didn't become SSH-ready within {timeout}s")

    def execute_remote(self, command: str, cwd: str = "/workspace/pipeline", stream_output: bool = False) -> Tuple[str, str, int]:
        """
        Execute command on remote instance via SSH

        Args:
            command: Command to execute
            cwd: Working directory (default: /workspace/pipeline)
            stream_output: Stream output in real-time (for long-running commands)

        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        if not self.ssh_info:
            raise RuntimeError("No SSH connection established")

        ssh_cmd = (
            f'ssh -o StrictHostKeyChecking=no '
            f'-p {self.ssh_info["port"]} '
            f'{self.ssh_info["user"]}@{self.ssh_info["host"]} '
            f'"cd {cwd} && {command}"'
        )

        return self._run_cmd(ssh_cmd, check=False, stream_output=stream_output)

    def copy_to_instance(self, local_path: str, remote_path: str):
        """
        Upload files to instance using rsync via SSH

        Args:
            local_path: Local file or directory path
            remote_path: Remote destination path
        """
        self._log(f"\n=== Uploading: {local_path} → {remote_path} ===")

        if not self.ssh_info:
            raise RuntimeError("No SSH connection established")

        # Create remote directory first
        remote_dir = str(Path(remote_path).parent) if '.' in Path(remote_path).name else remote_path
        self.execute_remote(f'mkdir -p {remote_dir}', cwd='/')

        # Use rsync for reliable file transfer with proper space handling
        local_path_obj = Path(local_path)
        is_dir = local_path_obj.is_dir()

        # Escape spaces in remote path for rsync
        remote_path_escaped = remote_path.replace(' ', '\\ ')

        rsync_cmd = (
            f'rsync -avz --progress '
            f'-e "ssh -o StrictHostKeyChecking=no -p {self.ssh_info["port"]}" '
            f'"{local_path}{"/" if is_dir else ""}" '
            f'{self.ssh_info["user"]}@{self.ssh_info["host"]}:{remote_path_escaped}'
        )

        stdout, stderr, _ = self._run_cmd(rsync_cmd)

        self._log(f"✓ Upload complete")

    def copy_from_instance(self, remote_path: str, local_path: str):
        """
        Download files from instance using rsync via SSH

        Args:
            remote_path: Remote file or directory path
            local_path: Local destination path
        """
        self._log(f"\n=== Downloading: {remote_path} → {local_path} ===")

        if not self.ssh_info:
            raise RuntimeError("No SSH connection established")

        # Ensure local directory exists
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        # Use rsync for reliable file transfer
        rsync_cmd = (
            f'rsync -avz --progress '
            f'-e "ssh -o StrictHostKeyChecking=no -p {self.ssh_info["port"]}" '
            f'{self.ssh_info["user"]}@{self.ssh_info["host"]}:{remote_path} '
            f'"{local_path}"'
        )

        stdout, stderr, _ = self._run_cmd(rsync_cmd)

        self._log(f"✓ Download complete")

    def destroy_instance(self, instance_id: Optional[str] = None):
        """
        Destroy instance and stop all charges

        Args:
            instance_id: Instance ID (uses self.instance_id if None)
        """
        instance_id = instance_id or self.instance_id

        if not instance_id:
            self._log("No instance to destroy")
            return

        self._log(f"\n=== Destroying instance {instance_id} ===")

        self._run_cmd(f'vastai destroy instance {instance_id}')

        self._log("✓ Instance destroyed - all charges stopped")

    def run_pipeline(self,
                    audio_file: str,
                    num_speakers: int = 2,
                    whisper_model: str = "large-v3",
                    cleanup: bool = True,
                    ssh_timeout: int = 300) -> Dict:
        """
        Run complete GPU pipeline workflow on Vast.ai

        Args:
            audio_file: Path to audio file to process
            num_speakers: Number of speakers for diarization
            whisper_model: Whisper model size
            cleanup: Destroy instance after completion
            ssh_timeout: SSH connection timeout in seconds (default: 300)

        Returns:
            Processing results dict
        """
        audio_path = Path(audio_file)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        # Get pipeline directory
        pipeline_dir = Path(__file__).parent.parent

        try:
            # 1. Search for instances
            offers = self.search_instances()
            if not offers:
                raise RuntimeError("No suitable GPU instances available")

            # Use cheapest offer
            offer_id = offers[0]['id']
            offer_price = offers[0].get('dph_total', 0)
            self._log(f"\nUsing offer {offer_id} (${offer_price:.3f}/hr)")

            # 2. Create instance
            self.create_instance(offer_id)

            # 3. Wait for SSH
            self.wait_for_ssh(self.instance_id, timeout=ssh_timeout)

            # 4. Upload pipeline code
            self.copy_to_instance(
                str(pipeline_dir),
                "/workspace/pipeline"
            )

            # 5. Upload audio file
            self.copy_to_instance(
                str(audio_path),
                f"/workspace/audio/{audio_path.name}"
            )

            # 6. Install dependencies
            self._log("\n=== Installing dependencies ===")
            stdout, stderr, code = self.execute_remote(
                "pip install -q -r requirements_gpu.txt"
            )
            if code != 0:
                self._log(f"WARNING: Dependency installation issues:\n{stderr}")
            else:
                self._log("✓ Dependencies installed")

            # 7. Set environment variables
            hf_token = os.getenv('HF_TOKEN')
            if hf_token:
                self._log("\n=== Setting HF_TOKEN ===")
                self.execute_remote(f'echo "export HF_TOKEN={hf_token}" >> ~/.bashrc')
            else:
                self._log("\n⚠️  WARNING: HF_TOKEN not found. Diarization will fail.")
                self._log("Set HF_TOKEN in .env file or environment variable.")

            # 8. Run GPU pipeline
            self._log(f"\n=== Running GPU pipeline on {audio_path.name} ===")
            self._log("Streaming output from GPU instance...\n")

            start_time = time.time()

            # Only set HF_TOKEN in command if it exists
            hf_env = f'export HF_TOKEN={hf_token} && ' if hf_token else ''
            cmd = (
                f'{hf_env}'
                f'python src/pipeline_gpu.py '
                f'/workspace/audio/{audio_path.name} '
                f'--num-speakers {num_speakers}'
            )

            # Stream output in real-time so user can see progress
            stdout, stderr, code = self.execute_remote(cmd, stream_output=True)

            elapsed = time.time() - start_time

            if code != 0:
                self._log(f"\n❌ Pipeline failed (exit code {code})")
                if stderr:
                    self._log(f"Error: {stderr}")
                raise RuntimeError(f"Pipeline execution failed: {stderr}")

            self._log(f"\n✓ Pipeline completed in {elapsed:.1f}s")

            # 9. Download results
            results_dir = pipeline_dir / "outputs" / "vast_results"
            results_dir.mkdir(parents=True, exist_ok=True)

            self.copy_from_instance(
                "/workspace/pipeline/transcription_result.json",
                str(results_dir / f"{audio_path.stem}_result.json")
            )

            # Load results
            result_file = results_dir / f"{audio_path.stem}_result.json"
            with open(result_file) as f:
                results = json.load(f)

            results['vast_processing_time'] = elapsed
            results['vast_instance_id'] = self.instance_id

            # Save updated results
            with open(result_file, 'w') as f:
                json.dump(results, f, indent=2)

            self._log(f"\n✓ Results saved to: {result_file}")

            return results

        finally:
            # 10. Cleanup
            if cleanup and self.instance_id:
                self.destroy_instance()


def main():
    """CLI interface"""
    parser = argparse.ArgumentParser(
        description="Run GPU audio transcription pipeline on Vast.ai"
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
        '--no-cleanup',
        action='store_true',
        help='Keep instance running after completion'
    )
    parser.add_argument(
        '--api-key',
        help='Vast.ai API key (or set VAST_API_KEY env var)'
    )
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum retry attempts for SSH timeout (default: 3)'
    )
    parser.add_argument(
        '--ssh-timeout',
        type=int,
        default=300,
        help='SSH connection timeout in seconds (default: 300)'
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print("Vast.ai GPU Pipeline Automation")
    print("="*60 + "\n")

    max_retries = args.max_retries
    retry_count = 0

    while retry_count < max_retries:
        try:
            pipeline = VastAIGPUPipeline(api_key=args.api_key, verbose=True)

            results = pipeline.run_pipeline(
                audio_file=args.audio_file,
                num_speakers=args.num_speakers,
                whisper_model=args.whisper_model,
                cleanup=not args.no_cleanup,
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

        except TimeoutError as e:
            retry_count += 1
            if retry_count < max_retries:
                print(f"\n⚠️  Timeout error (attempt {retry_count}/{max_retries})")
                print(f"Retrying with a different instance...\n")
                time.sleep(5)  # Brief pause before retry
            else:
                print(f"\n❌ Failed after {max_retries} attempts: {e}")
                return 1

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            return 130
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            return 1

    return 1


if __name__ == '__main__':
    sys.exit(main())
