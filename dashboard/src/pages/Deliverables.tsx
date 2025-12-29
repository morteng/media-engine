import { useState } from 'react';
import { useApi } from '@/hooks/useApi';
import { DeliverableGrid } from '@/components/publications';
import { ExpandableSection, Spinner } from '@/components/ui';
import { Package, RefreshCw, FolderOpen } from 'lucide-react';
import type { BuildOutputsResponse } from '@/api/types';

export default function Deliverables() {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['recent', 'all'])
  );

  const { data, isLoading, refetch } = useApi<BuildOutputsResponse>('/api/build/outputs');

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  const handleDownload = (path: string) => {
    // Trigger download via API
    window.open(`/api/build/download?path=${encodeURIComponent(path)}`, '_blank');
  };

  const handlePreview = (path: string) => {
    // Open HTML preview
    window.open(`/api/build/preview?path=${encodeURIComponent(path)}`, '_blank');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" className="text-primary" />
      </div>
    );
  }

  const outputs = data?.outputs || [];

  // Group outputs
  const recentOutputs = outputs
    .sort((a, b) => new Date(b.modified).getTime() - new Date(a.modified).getTime())
    .slice(0, 6);

  // Group by publication
  const byPublication = outputs.reduce((acc, output) => {
    const pubName = output.name.split('_')[0] || 'Other';
    if (!acc[pubName]) acc[pubName] = [];
    acc[pubName].push(output);
    return acc;
  }, {} as Record<string, typeof outputs>);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Package className="w-6 h-6 text-primary" />
            Deliverables
          </h1>
          <p className="text-base-content/60 mt-1">
            Generated outputs ready for distribution
          </p>
        </div>
        <div className="flex gap-2">
          <button
            className="btn btn-ghost btn-sm gap-1"
            onClick={() => refetch()}
          >
            <RefreshCw size={14} />
            Refresh
          </button>
          <button className="btn btn-ghost btn-sm gap-1">
            <FolderOpen size={14} />
            Open Folder
          </button>
        </div>
      </div>

      {/* Summary stats */}
      {outputs.length > 0 && (
        <div className="stats stats-horizontal bg-base-200 shadow w-full">
          <div className="stat">
            <div className="stat-title">Total Files</div>
            <div className="stat-value text-2xl">{outputs.length}</div>
          </div>
          <div className="stat">
            <div className="stat-title">PDF</div>
            <div className="stat-value text-2xl text-red-500">
              {outputs.filter((o) => o.format === 'pdf').length}
            </div>
          </div>
          <div className="stat">
            <div className="stat-title">HTML</div>
            <div className="stat-value text-2xl text-blue-500">
              {outputs.filter((o) => o.format === 'html').length}
            </div>
          </div>
          <div className="stat">
            <div className="stat-title">PPTX</div>
            <div className="stat-value text-2xl text-orange-500">
              {outputs.filter((o) => o.format === 'pptx').length}
            </div>
          </div>
        </div>
      )}

      {/* Recent outputs */}
      {recentOutputs.length > 0 && (
        <ExpandableSection
          title={`Recent Outputs (${recentOutputs.length})`}
          isExpanded={expandedSections.has('recent')}
          onToggle={() => toggleSection('recent')}
        >
          <DeliverableGrid
            outputs={recentOutputs}
            onDownload={handleDownload}
            onPreview={handlePreview}
          />
        </ExpandableSection>
      )}

      {/* All outputs by publication */}
      <ExpandableSection
        title={`All Deliverables (${outputs.length})`}
        isExpanded={expandedSections.has('all')}
        onToggle={() => toggleSection('all')}
      >
        {outputs.length === 0 ? (
          <div className="text-center py-12">
            <Package size={48} className="mx-auto text-base-content/30 mb-4" />
            <p className="text-base-content/60">No deliverables yet</p>
            <p className="text-sm text-base-content/40 mt-1">
              Build a publication to generate outputs
            </p>
          </div>
        ) : (
          <DeliverableGrid
            outputs={outputs}
            groupByFormat
            onDownload={handleDownload}
            onPreview={handlePreview}
          />
        )}
      </ExpandableSection>

      {/* By publication */}
      {Object.keys(byPublication).length > 1 && (
        <ExpandableSection
          title="By Publication"
          isExpanded={expandedSections.has('by-pub')}
          onToggle={() => toggleSection('by-pub')}
        >
          <div className="space-y-6">
            {Object.entries(byPublication).map(([pubName, pubOutputs]) => (
              <div key={pubName}>
                <h3 className="text-sm font-semibold text-base-content/70 mb-3 uppercase tracking-wide">
                  {pubName}
                  <span className="badge badge-sm ml-2">{pubOutputs.length}</span>
                </h3>
                <DeliverableGrid
                  outputs={pubOutputs}
                  onDownload={handleDownload}
                  onPreview={handlePreview}
                />
              </div>
            ))}
          </div>
        </ExpandableSection>
      )}
    </div>
  );
}
