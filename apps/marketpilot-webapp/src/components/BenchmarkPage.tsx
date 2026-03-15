import { useState } from 'react';
import { BenchmarkForm } from './BenchmarkForm';
import { BenchmarkProgress } from './BenchmarkProgress';
import { api } from '@services/api';

type PageState =
  | { phase: 'idle' }
  | { phase: 'submitting' }
  | { phase: 'polling'; jobId: string };

export function BenchmarkPage() {
  const [state, setState] = useState<PageState>({ phase: 'idle' });

  const handleSubmit = async (email: string, companyName: string, companyUrl: string, competitorUrls: string[]) => {
    setState({ phase: 'submitting' });
    try {
      const res = await api.startBenchmark({ email, companyName, companyUrl, competitorUrls });
      setState({ phase: 'polling', jobId: res.id });
    } catch (err) {
      setState({ phase: 'idle' });
      throw err;
    }
  };

  const handleReset = () => {
    setState({ phase: 'idle' });
  };

  if (state.phase === 'polling') {
    return <BenchmarkProgress jobId={state.jobId} onReset={handleReset} />;
  }

  return (
    <BenchmarkForm
      onSubmit={handleSubmit}
      isSubmitting={state.phase === 'submitting'}
    />
  );
}
