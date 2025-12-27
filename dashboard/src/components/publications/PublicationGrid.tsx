import { PublicationCard } from './PublicationCard';
import type { PublicationStatusItem } from '@/api/types';

interface PublicationGridProps {
  publications: PublicationStatusItem[];
  groupByLanguage?: boolean;
  compact?: boolean;
  showActions?: boolean;
  onBuild?: (pubId: string) => void;
}

export function PublicationGrid({
  publications,
  groupByLanguage = true,
  compact = false,
  showActions = false,
  onBuild,
}: PublicationGridProps) {
  if (!publications || publications.length === 0) {
    return (
      <div className="text-center py-12 text-base-content/60">
        <p>No publications found</p>
        <p className="text-sm mt-2">Create publications in your project.yaml</p>
      </div>
    );
  }

  if (groupByLanguage) {
    // Group publications by language
    const byLanguage = publications.reduce((acc, pub) => {
      const lang = pub.language;
      if (!acc[lang]) acc[lang] = [];
      acc[lang].push(pub);
      return acc;
    }, {} as Record<string, PublicationStatusItem[]>);

    const languageNames: Record<string, string> = {
      en: 'English',
      no: 'Norwegian',
      nb: 'Norwegian (Bokmal)',
      nn: 'Norwegian (Nynorsk)',
      sv: 'Swedish',
      da: 'Danish',
      de: 'German',
      fr: 'French',
      es: 'Spanish',
    };

    return (
      <div className="space-y-8">
        {Object.entries(byLanguage).map(([lang, pubs]) => (
          <div key={lang}>
            <h3 className="text-sm font-semibold text-base-content/70 mb-4 uppercase tracking-wide flex items-center gap-2">
              <span className="badge badge-sm">{lang.toUpperCase()}</span>
              {languageNames[lang] || lang}
              <span className="text-xs font-normal">({pubs.length})</span>
            </h3>
            {compact ? (
              <div className="space-y-2">
                {pubs.map((pub) => (
                  <PublicationCard
                    key={pub.key}
                    publication={pub}
                    compact
                    showActions={showActions}
                    onBuild={onBuild}
                  />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {pubs.map((pub) => (
                  <PublicationCard
                    key={pub.key}
                    publication={pub}
                    showActions={showActions}
                    onBuild={onBuild}
                  />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  }

  // No grouping
  if (compact) {
    return (
      <div className="space-y-2">
        {publications.map((pub) => (
          <PublicationCard
            key={pub.key}
            publication={pub}
            compact
            showActions={showActions}
            onBuild={onBuild}
          />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {publications.map((pub) => (
        <PublicationCard
          key={pub.key}
          publication={pub}
          showActions={showActions}
          onBuild={onBuild}
        />
      ))}
    </div>
  );
}
