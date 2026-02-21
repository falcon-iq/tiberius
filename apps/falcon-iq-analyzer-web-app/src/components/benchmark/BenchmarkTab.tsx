import { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { BenchmarkResult } from '@app-types/api';
import { useAnalyses } from '@hooks/use-analyses';
import { useBenchmarks } from '@hooks/use-benchmarks';
import { useBenchmarkJob } from '@hooks/use-benchmark-job';
import { api } from '@services/api';
import { NewBenchmarkForm } from './NewBenchmarkForm';
import { BenchmarkHistory } from './BenchmarkHistory';
import { BenchmarkDashboard } from './BenchmarkDashboard';
import { EmptyState } from '@components/shared/EmptyState';

export function BenchmarkTab() {
  const [activeBenchmarkJobId, setActiveBenchmarkJobId] = useState<string | null>(null);
  const [benchmarkError, setBenchmarkError] = useState<string | null>(null);
  const [viewingResult, setViewingResult] = useState<BenchmarkResult | null>(null);
  const queryClient = useQueryClient();

  const { data: analyses = [] } = useAnalyses();
  const { data: benchmarks = [] } = useBenchmarks();
  const { data: activeJobData } = useBenchmarkJob(activeBenchmarkJobId);

  // React to benchmark job completion
  const activeStatus = activeJobData?.status;
  useEffect(() => {
    if (!activeStatus) return;
    if (activeStatus === 'completed') {
      setActiveBenchmarkJobId(null);
      setBenchmarkError(null);
      if (activeJobData?.result) {
        setViewingResult(activeJobData.result);
      }
      queryClient.invalidateQueries({ queryKey: ['benchmarks'] });
    } else if (activeStatus === 'failed') {
      setActiveBenchmarkJobId(null);
      setBenchmarkError(activeJobData?.error ?? 'Benchmark failed');
    }
  }, [activeStatus]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleStartBenchmark = async (jobIdA: string, jobIdB: string, numPrompts: number) => {
    setBenchmarkError(null);
    setViewingResult(null);
    try {
      const { job_id } = await api.startBenchmark(jobIdA, jobIdB, numPrompts);
      setActiveBenchmarkJobId(job_id);
    } catch (e) {
      setBenchmarkError((e as Error).message);
    }
  };

  const handleViewBenchmark = async (jobId: string) => {
    try {
      const data = await api.getBenchmarkJob(jobId);
      if (data.status === 'completed' && data.result) {
        setViewingResult(data.result);
        // Scroll to result
        setTimeout(() => {
          document.getElementById('benchmark-result')?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    } catch (e) {
      alert('Failed to load benchmark: ' + (e as Error).message);
    }
  };

  const handleDeleteBenchmark = async (jobId: string) => {
    if (!confirm('Delete this benchmark? This cannot be undone.')) return;
    try {
      await api.deleteBenchmark(jobId);
      queryClient.invalidateQueries({ queryKey: ['benchmarks'] });
      setViewingResult(null);
    } catch (e) {
      alert('Failed to delete: ' + (e as Error).message);
    }
  };

  // Benchmark job progress
  const benchmarkStepMatch = activeJobData?.progress?.match(/Step\s+(\d+)\/(\d+)/);
  const benchmarkPct = activeJobData
    ? activeJobData.status === 'completed'
      ? 100
      : benchmarkStepMatch
        ? Math.min(95, (parseInt(benchmarkStepMatch[1]) / parseInt(benchmarkStepMatch[2])) * 100)
        : 10
    : 0;

  return (
    <div>
      <NewBenchmarkForm
        analyses={analyses}
        isRunning={!!activeBenchmarkJobId}
        benchmarkPct={benchmarkPct}
        benchmarkMessage={activeJobData?.progress ?? null}
        benchmarkError={benchmarkError}
        onStartBenchmark={handleStartBenchmark}
      />

      {benchmarks.length === 0 ? (
        <EmptyState
          icon="📊"
          title="No benchmarks yet"
          message="Run a benchmark above to compare two companies"
        />
      ) : (
        <BenchmarkHistory
          benchmarks={benchmarks}
          onView={handleViewBenchmark}
          onDelete={handleDeleteBenchmark}
        />
      )}

      {viewingResult && (
        <div id="benchmark-result" className="mt-5">
          <BenchmarkDashboard result={viewingResult} />
        </div>
      )}
    </div>
  );
}
