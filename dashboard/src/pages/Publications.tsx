import { useState } from 'react';
import { usePublicationsStatus, usePublicationTranslations } from '@/hooks/useApi';
import { Book, Globe, CheckCircle, AlertCircle, Clock, ChevronRight } from 'lucide-react';
import type {
  PublicationsStatusResponse,
  PublicationTranslationsResponse,
  PublicationStatusItem,
} from '@/api/types';
import { ExpandableSection, Spinner } from '@/components/ui';
import { getPublicationTypeIcon, getItemTypeIcon } from '@/utils/iconMappings';
import { getPublicationStatusBadge, FORMAT_LABELS } from '@/utils/statusMappings';
import { CARD_STYLES } from '@/utils/styles';

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`badge badge-sm ${getPublicationStatusBadge(status)}`}>
      {status.replace('_', ' ')}
    </span>
  );
}

function ValidationBadge({ isValid, issueCount }: { isValid: boolean; issueCount: number }) {
  if (isValid) {
    return (
      <span className="badge badge-sm badge-success gap-1">
        <CheckCircle className="w-3 h-3" />
        Valid
      </span>
    );
  }
  return (
    <span className="badge badge-sm badge-error gap-1">
      <AlertCircle className="w-3 h-3" />
      {issueCount} issues
    </span>
  );
}

function TranslationBadge({ isCurrent, sourceChanged }: { isCurrent: boolean; sourceChanged: boolean }) {
  if (isCurrent) {
    return (
      <span className="badge badge-sm badge-success gap-1">
        <CheckCircle className="w-3 h-3" />
        Current
      </span>
    );
  }
  if (sourceChanged) {
    return (
      <span className="badge badge-sm badge-warning gap-1">
        <Clock className="w-3 h-3" />
        Needs Update
      </span>
    );
  }
  return null;
}

function PublicationCard({ pub }: { pub: PublicationStatusItem }) {
  const TypeIcon = getPublicationTypeIcon(pub.pub_type);
  const ItemIcon = getItemTypeIcon(pub.item_label);

  return (
    <div className={CARD_STYLES.elevated}>
      <div className="card-body p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <TypeIcon className="w-5 h-5 text-primary" />
            <div>
              <h3 className="font-semibold text-sm">{pub.title}</h3>
              <p className="text-xs text-base-content/60">{pub.key}</p>
            </div>
          </div>
          <StatusBadge status={pub.status} />
        </div>

        <div className="flex flex-wrap gap-2 mt-3">
          <span className="badge badge-sm badge-ghost gap-1">
            <Globe className="w-3 h-3" />
            {pub.language.toUpperCase()}
          </span>
          <span className="badge badge-sm badge-ghost gap-1">
            <ItemIcon className="w-3 h-3" />
            {pub.item_count} {pub.item_label}
          </span>
          <ValidationBadge isValid={pub.is_valid} issueCount={pub.issues_count} />
          {pub.is_translation && (
            <TranslationBadge isCurrent={pub.translation_current} sourceChanged={pub.source_changed} />
          )}
        </div>

        {pub.missing_chapters > 0 && (
          <p className="text-xs text-error mt-2">
            {pub.missing_chapters} missing chapter(s)
          </p>
        )}
      </div>
    </div>
  );
}

function PublicationsList({ publications }: { publications: PublicationStatusItem[] }) {
  // Group by language
  const byLanguage = publications.reduce((acc, pub) => {
    if (!acc[pub.language]) acc[pub.language] = [];
    acc[pub.language].push(pub);
    return acc;
  }, {} as Record<string, PublicationStatusItem[]>);

  return (
    <div className="space-y-6">
      {Object.entries(byLanguage).map(([lang, pubs]) => (
        <div key={lang}>
          <h3 className="text-sm font-semibold text-base-content/70 mb-3 uppercase tracking-wide">
            {lang === 'en' ? 'English' : lang === 'no' ? 'Norwegian' : lang}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {pubs.map((pub) => (
              <PublicationCard key={pub.key} pub={pub} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function TranslationMatrix({ data }: { data: PublicationTranslationsResponse }) {
  if (data.pairs.length === 0) {
    return (
      <div className="text-center py-8 text-base-content/60">
        No translation pairs found
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {data.pairs.map((pair, i) => (
        <div
          key={i}
          className={`card bg-base-200 ${
            pair.sync_status.needs_update ? 'border border-warning' : ''
          }`}
        >
          <div className="card-body p-4">
            <div className="flex items-center gap-4">
              {/* Source */}
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="badge badge-sm">{pair.source.language.toUpperCase()}</span>
                  <span className="font-medium text-sm">{pair.source.title}</span>
                </div>
                <p className="text-xs text-base-content/50 mt-1 font-mono">
                  {pair.source.content_hash?.slice(0, 8)}...
                </p>
              </div>

              {/* Arrow */}
              <ChevronRight className="w-5 h-5 text-base-content/40" />

              {/* Translation */}
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="badge badge-sm">{pair.translation.language.toUpperCase()}</span>
                  <span className="font-medium text-sm">{pair.translation.title}</span>
                </div>
                <p className="text-xs text-base-content/50 mt-1 font-mono">
                  {pair.translation.source_hash?.slice(0, 8) || 'no hash'}...
                </p>
              </div>

              {/* Status */}
              <div>
                {pair.sync_status.is_current ? (
                  <span className="badge badge-success gap-1">
                    <CheckCircle className="w-3 h-3" />
                    Synced
                  </span>
                ) : (
                  <span className="badge badge-warning gap-1">
                    <Clock className="w-3 h-3" />
                    Needs Update
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function SummaryCard({ summary }: { summary: PublicationsStatusResponse['summary'] }) {
  return (
    <div className="stats stats-horizontal bg-base-200 shadow w-full">
      <div className="stat">
        <div className="stat-title">Total</div>
        <div className="stat-value text-2xl">{summary.total}</div>
        <div className="stat-desc">Publications</div>
      </div>
      <div className="stat">
        <div className="stat-title">Valid</div>
        <div className="stat-value text-2xl text-success">{summary.valid}</div>
        <div className="stat-desc">{summary.invalid > 0 ? `${summary.invalid} invalid` : 'All valid'}</div>
      </div>
      <div className="stat">
        <div className="stat-title">Translations</div>
        <div className="stat-value text-2xl text-info">{summary.translations_current}</div>
        <div className="stat-desc">
          {summary.translations_outdated > 0
            ? `${summary.translations_outdated} outdated`
            : 'All current'}
        </div>
      </div>
      <div className="stat">
        <div className="stat-title">Issues</div>
        <div className="stat-value text-2xl text-warning">{summary.total_issues}</div>
        <div className="stat-desc">Total issues</div>
      </div>
    </div>
  );
}

export default function Publications() {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview', 'publications']));

  const { data: statusData, isLoading: statusLoading, error: statusError } = usePublicationsStatus();
  const { data: translationsData, isLoading: translationsLoading } = usePublicationTranslations();

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

  if (statusLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" className="text-primary" />
      </div>
    );
  }

  if (statusError || !statusData) {
    return (
      <div className="alert alert-warning">
        <AlertCircle className="w-5 h-5" />
        <span>No publications found. Create publication YAML files in content/[lang]/publications/</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Book className="w-6 h-6 text-primary" />
          Publications
        </h1>
        <p className="text-base-content/60 mt-1">
          Composite documents combining chapters into books, guides, and presentations
        </p>
      </div>

      {/* Summary */}
      <ExpandableSection
        title="Overview"
        isExpanded={expandedSections.has('overview')}
        onToggle={() => toggleSection('overview')}
      >
        <SummaryCard summary={statusData.summary} />
      </ExpandableSection>

      {/* Publications List */}
      <ExpandableSection
        title={`Publications (${statusData.publications.length})`}
        isExpanded={expandedSections.has('publications')}
        onToggle={() => toggleSection('publications')}
      >
        <PublicationsList publications={statusData.publications} />
      </ExpandableSection>

      {/* Translation Matrix */}
      <ExpandableSection
        title={`Translation Pairs (${translationsData?.total || 0})`}
        isExpanded={expandedSections.has('translations')}
        onToggle={() => toggleSection('translations')}
        badge={
          translationsData && translationsData.outdated > 0 ? (
            <span className="badge badge-sm badge-warning">{translationsData.outdated} outdated</span>
          ) : undefined
        }
      >
        {translationsLoading ? (
          <div className="flex justify-center py-8">
            <Spinner size="md" />
          </div>
        ) : translationsData ? (
          <TranslationMatrix data={translationsData} />
        ) : (
          <p className="text-center py-8 text-base-content/60">No translation data available</p>
        )}
      </ExpandableSection>

      {/* Output Formats Guide */}
      <ExpandableSection
        title="Output Formats"
        isExpanded={expandedSections.has('formats')}
        onToggle={() => toggleSection('formats')}
      >
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {Object.entries(FORMAT_LABELS).map(([format, label]) => (
            <div key={format} className="card bg-base-200 p-4 text-center">
              <div className="text-2xl font-bold text-primary">{label}</div>
              <p className="text-xs text-base-content/60 mt-1 capitalize">{format}</p>
            </div>
          ))}
        </div>
      </ExpandableSection>
    </div>
  );
}
