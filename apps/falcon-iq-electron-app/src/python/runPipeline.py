#!/usr/bin/env python3
"""
PR Data Pipeline Runner

This script orchestrates the execution of the complete PR data pipeline:
1. Task Generation (prTaskGenerator.py) - Generate PR tasks for users
2. PR Search (prSearchTaskExecutor.py) - Download PR lists from GitHub
3. PR Details Download (prDownloadExecutor.py) - Download full PR details
4. OKR Mapping (prOKRMapper.py) - Map OKRs to PRs with intelligent classification
5. Comment Generation (prCommentFileGenerator.py) - Extract PR comments
6. Comment Classification (prCommentClassification.py) - Classify comments using AI
7. PR Stats Aggregation (prStatsAggregator.py) - Aggregate PR stats into CSV files
8. Write Stats to DB (prStatsWriteToDB.py) - Write PR stats to SQLite database

Usage:
    python runPipeline.py                                      # Run full pipeline from step 1
    python runPipeline.py --base-dir /path/to/data             # Use custom base directory
    python runPipeline.py --start-from 2                       # Start from PR search step
    python runPipeline.py --start-from 3 --base-dir /custom    # Custom dir + start from step 3
    python runPipeline.py --steps 1,2                          # Run only specific steps
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
import common


class PipelineRunner:
    """Orchestrates the execution of PR data pipeline scripts."""
    
    STEPS = {
        1: {
            "name": "Task Generation",
            "script": "prTaskGenerator.py",
            "description": "Generate PR tasks for users based on date ranges"
        },
        2: {
            "name": "PR Search",
            "script": "prSearchTaskExecutor.py",
            "description": "Download PR lists from GitHub using search API"
        },
        3: {
            "name": "PR Details Download",
            "script": "prDownloadExecutor.py",
            "description": "Download full PR details (meta, comments, files)"
        },
        4: {
            "name": "OKR Mapping",
            "script": "prOKRMapper.py",
            "description": "Map OKRs to PRs with intelligent classification and fallback"
        },
        5: {
            "name": "Comment Generation",
            "script": "prCommentFileGenerator.py",
            "description": "Extract and organize PR comments (authored/reviewed)"
        },
        6: {
            "name": "Comment Classification",
            "script": "prCommentClassification.py",
            "description": "Classify PR comments using OpenAI into feedback categories"
        },
        7: {
            "name": "PR Stats Aggregation",
            "script": "prStatsAggregator.py",
            "description": "Aggregate PR statistics for each user into CSV files"
        },
        8: {
            "name": "Write Stats to DB",
            "script": "prStatsWriteToDB.py",
            "description": "Import PR statistics from CSV files into SQLite database"
        }
    }
    
    def __init__(self, start_from: int = 1, specific_steps: list = None, base_dir: str = None, is_dev: bool = True):
        """
        Initialize pipeline runner.
        
        Args:
            start_from: Step number to start from (1-8)
            specific_steps: List of specific step numbers to run (overrides start_from)
            base_dir: Override base directory (optional)
            is_dev: Flag indicating if running in development mode
        """
        self.start_from = start_from
        self.specific_steps = specific_steps
        self.base_dir = base_dir
        self.is_dev = is_dev
        self.script_dir = Path(__file__).parent
        self.results = {}
        
        # Set global base_dir if provided
        if base_dir:
            common.set_base_dir(base_dir)

        common.set_env(is_dev)
        
    def print_header(self):
        """Print pipeline header."""
        print("=" * 80)
        print("🚀 PR DATA PIPELINE RUNNER")
        print("=" * 80)
        
        # Show base_dir being used
        if self.base_dir:
            print(f"📁 Using custom base directory: {self.base_dir}")
        else:
            print(f"📁 Using base directory from pipeline_config.json")
        
        print()
        
    def print_step_header(self, step_num: int):
        """Print header for a pipeline step."""
        step = self.STEPS[step_num]
        print()
        print("=" * 80)
        print(f"📍 STEP {step_num}/{len(self.STEPS)}: {step['name']}")
        print(f"   Script: {step['script']}")
        print(f"   Description: {step['description']}")
        print("=" * 80)
        print()
        
    def run_script(self, script_name: str) -> dict:
        """
        Run a Python script and return execution results.
        
        Args:
            script_name: Name of the script to run
            
        Returns:
            Dict with success status, duration, and output
        """
        script_path = self.script_dir / script_name
        
        if not script_path.exists():
            return {
                "success": False,
                "error": f"Script not found: {script_path}",
                "duration": 0
            }
        
        start_time = datetime.now()
        
        try:
            # Prepare environment variables
            env = os.environ.copy()
            
            # Pass base_dir override to subprocess if set
            if self.base_dir:
                env['FALCON_BASE_DIR'] = self.base_dir
            
            # Pass IS_DEV flag to subprocess
            env['FALCON_IS_DEV'] = '1' if self.is_dev else '0'
            
            # Run the script using the same Python interpreter
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=self.script_dir,
                capture_output=True,
                text=True,
                timeout=18000,  # 5 hour timeout per script
                env=env  # Pass environment variables
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Print the output in real-time style
            if result.stdout:
                print(result.stdout)
            
            if result.stderr:
                print("STDERR:", result.stderr, file=sys.stderr)
            
            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "error": "Script execution timed out (5 hours)",
                "duration": duration
            }
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "error": str(e),
                "duration": duration
            }
    
    def get_steps_to_run(self) -> list:
        """Determine which steps to run based on configuration."""
        if self.specific_steps:
            return sorted(self.specific_steps)
        else:
            return list(range(self.start_from, len(self.STEPS) + 1))
    
    def run(self):
        """Execute the pipeline."""
        self.print_header()
        
        steps_to_run = self.get_steps_to_run()
        
        print(f"📋 Pipeline Configuration:")
        if self.specific_steps:
            print(f"   Running specific steps: {', '.join(map(str, steps_to_run))}")
        else:
            print(f"   Starting from step: {self.start_from}")
            print(f"   Steps to run: {', '.join(map(str, steps_to_run))}")
        print(f"   Total steps: {len(steps_to_run)}")
        print()
        
        total_start_time = datetime.now()
        
        for step_num in steps_to_run:
            if step_num not in self.STEPS:
                print(f"❌ Invalid step number: {step_num}")
                continue
            
            step = self.STEPS[step_num]
            self.print_step_header(step_num)
            
            print(f"⏳ Running {step['script']}...")
            print()
            
            result = self.run_script(step['script'])
            self.results[step_num] = result
            
            print()
            if result['success']:
                print(f"✅ Step {step_num} completed successfully in {result['duration']:.2f}s")
            else:
                print(f"❌ Step {step_num} failed!")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
                elif 'return_code' in result:
                    print(f"   Return code: {result['return_code']}")
                
                # Log failure and stop pipeline
                print()
                print(f"⏹️  Pipeline stopped due to failure in step {step_num}")
                break
        
        total_duration = (datetime.now() - total_start_time).total_seconds()
        
        # Print summary
        print()
        print("=" * 80)
        print("📊 PIPELINE SUMMARY")
        print("=" * 80)
        print()
        
        successful_steps = sum(1 for r in self.results.values() if r['success'])
        failed_steps = len(self.results) - successful_steps
        
        for step_num, result in self.results.items():
            step = self.STEPS[step_num]
            status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
            print(f"   Step {step_num} ({step['name']}): {status} - {result['duration']:.2f}s")
        
        print()
        print(f"   Total Steps Run: {len(self.results)}")
        print(f"   Successful: {successful_steps}")
        print(f"   Failed: {failed_steps}")
        print(f"   Total Duration: {total_duration:.2f}s")
        print()
        
        if failed_steps == 0:
            print("🎉 Pipeline completed successfully!")
        else:
            print("⚠️  Pipeline completed with errors")
        
        print("=" * 80)
        
        return failed_steps == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run the PR data pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                        Run full pipeline (all steps)
  %(prog)s --base-dir /path/to/data               Use custom base directory
  %(prog)s --base_dir /path/to/data               Use custom base directory (underscore)
  %(prog)s --BASE-DIR /path/to/data               Case insensitive format
  %(prog)s --start-from 2                         Start from step 2 (PR search)
  %(prog)s --start-from 3                         Start from step 3 (PR download)
  %(prog)s --steps 1,3                            Run only steps 1 and 3
  %(prog)s --base_dir /custom --steps 2,3         Custom dir + specific steps
  %(prog)s --list                                 List all available steps

Pipeline Steps:
  1. Task Generation - Generate PR tasks for users
  2. PR Search - Download PR lists from GitHub
  3. PR Details Download - Download full PR details
  4. OKR Mapping - Map OKRs to PRs with intelligent classification
  5. Comment Generation - Extract PR comments
  6. Comment Classification - Classify comments using AI
  7. PR Stats Aggregation - Aggregate PR statistics into CSV files
  8. Write Stats to DB - Write PR stats to SQLite database
        """
    )
    
    parser.add_argument(
        '--base-dir', '--base_dir',
        '--BASE-DIR', '--BASE_DIR',
        '--Base-Dir', '--Base_Dir',
        dest='base_dir',
        type=str,
        help='Override base directory (uses pipeline_config.json if not specified)'
    )
    
    parser.add_argument(
        '--start-from',
        type=int,
        choices=[1, 2, 3, 4, 5, 6, 7, 8],
        default=1,
        help='Step number to start from (default: 1)'
    )
    
    parser.add_argument(
        '--steps',
        type=str,
        help='Comma-separated list of specific steps to run (e.g., "1,3")'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available pipeline steps'
    )
    
    args = parser.parse_args()
    
    # Handle --list flag
    if args.list:
        print("Available Pipeline Steps:")
        print()
        for step_num, step in PipelineRunner.STEPS.items():
            print(f"  {step_num}. {step['name']}")
            print(f"     Script: {step['script']}")
            print(f"     Description: {step['description']}")
            print()
        return 0
    
    # Validate base_dir if provided
    if args.base_dir:
        base_dir_path = Path(args.base_dir).expanduser()
        if not base_dir_path.exists():
            print(f"❌ Error: Base directory does not exist: {base_dir_path}")
            print("   Please create the directory or provide a valid path.")
            return 1
    
    # Parse specific steps if provided
    specific_steps = None
    if args.steps:
        try:
            specific_steps = [int(s.strip()) for s in args.steps.split(',')]
            # Validate step numbers
            invalid_steps = [s for s in specific_steps if s not in PipelineRunner.STEPS]
            if invalid_steps:
                print(f"❌ Invalid step numbers: {invalid_steps}")
                print(f"Valid steps are: {list(PipelineRunner.STEPS.keys())}")
                return 1
        except ValueError:
            print("❌ Invalid --steps format. Use comma-separated numbers (e.g., '1,3')")
            return 1
    
    # Run the pipeline
    runner = PipelineRunner(
        start_from=args.start_from,
        specific_steps=specific_steps,
        base_dir=args.base_dir
    )
    
    success = runner.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
