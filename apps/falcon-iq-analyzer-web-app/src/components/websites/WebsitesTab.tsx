import { useState, useEffect, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { LocalSite } from '@app-types/api';
import { api } from '@services/api';
import { useSites } from '@hooks/use-sites';
import { useAnalyses } from '@hooks/use-analyses';
import { AddSiteForm } from './AddSiteForm';
import { SiteCard } from './SiteCard';
import { EmptyState } from '@components/shared/EmptyState';

export function WebsitesTab() {
  const [localSites, setLocalSites] = useState<LocalSite[]>([]);
  const queryClient = useQueryClient();

  const { data: apiSites } = useSites();
  const { data: analyses = [] } = useAnalyses();

  // Merge API sites into local state on first load
  useEffect(() => {
    if (!apiSites) return;
    setLocalSites((prev) => {
      const next = [...prev];
      apiSites.forEach((s) => {
        const exists = next.find(
          (e) => e.domain === s.domain && e.directory === s.directory,
        );
        if (!exists) {
          next.push({
            url: 'https://' + s.domain,
            domain: s.domain,
            directory: s.directory,
            page_count: s.page_count,
            status: 'crawled',
            maxPages: s.page_count,
          });
        }
      });
      return next;
    });
  }, [apiSites]);

  const handleAddSite = useCallback((url: string, maxPages: number) => {
    let domain: string;
    try {
      domain = new URL(url).hostname;
    } catch {
      alert('Please enter a valid URL');
      return;
    }
    setLocalSites((prev) => {
      if (prev.find((s) => s.domain === domain)) {
        alert('This domain is already in the list');
        return prev;
      }
      return [
        ...prev,
        { url, domain, directory: null, page_count: 0, status: 'pending', maxPages },
      ];
    });
  }, []);

  const handleUpdateSite = useCallback((domain: string, updates: Partial<LocalSite>) => {
    setLocalSites((prev) =>
      prev.map((s) => (s.domain === domain ? { ...s, ...updates } : s)),
    );
  }, []);

  const handleRemoveSite = useCallback(
    async (domain: string) => {
      const site = localSites.find((s) => s.domain === domain);
      if (!site) return;

      if (site.status !== 'pending' && site.domain) {
        try {
          await api.deleteSite(site.domain);
        } catch (e) {
          alert('Failed to delete: ' + (e as Error).message);
          return;
        }
      }
      setLocalSites((prev) => prev.filter((s) => s.domain !== domain));
      queryClient.invalidateQueries({ queryKey: ['sites'] });
    },
    [localSites, queryClient],
  );

  const handleAnalysisDeleted = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['analyses'] });
  }, [queryClient]);

  return (
    <div>
      <AddSiteForm onAdd={handleAddSite} />
      {localSites.length === 0 ? (
        <EmptyState
          icon="🌐"
          title="No websites yet"
          message="Add a URL above or wait for previously crawled sites to load"
        />
      ) : (
        localSites.map((site) => (
          <SiteCard
            key={site.domain}
            site={site}
            analyses={analyses}
            onUpdate={handleUpdateSite}
            onRemove={handleRemoveSite}
            onAnalysisDeleted={handleAnalysisDeleted}
          />
        ))
      )}
    </div>
  );
}
