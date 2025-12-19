import { useInsights, useTranslationMatrix } from '@/hooks/useApi';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { LoadingState } from '@/components/ui/Spinner';
import {
  Languages,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle
} from 'lucide-react';

export function Translations() {
  const { data: insights, isLoading: insightsLoading } = useInsights();
  const { data: matrix, isLoading: matrixLoading } = useTranslationMatrix();

  if (insightsLoading || matrixLoading) {
    return <LoadingState message="Loading translations..." />;
  }

  const parity = insights?.parity;
  const languages = parity?.languages ?? [];
  const coverage = parity?.coverage ?? {};
  const missing = parity?.missing ?? {};

  return (
    <div className="page translations-page">
      <div className="page-header">
        <h1>Translations</h1>
        <p className="text-muted">Multi-language content coverage and parity</p>
      </div>

      {/* Coverage Overview */}
      <div className="coverage-cards">
        {languages.map(lang => (
          <Card key={lang} className={coverage[lang] === 100 ? 'card-success' : ''}>
            <CardContent>
              <div className="coverage-header">
                <Languages size={24} />
                <span className="lang-code">{lang.toUpperCase()}</span>
                {coverage[lang] === 100 ? (
                  <CheckCircle size={20} className="text-success" />
                ) : (
                  <AlertTriangle size={20} className="text-warning" />
                )}
              </div>
              <div className="coverage-value">{Math.round(coverage[lang] ?? 0)}%</div>
              <ProgressBar
                value={coverage[lang] ?? 0}
                variant={coverage[lang] === 100 ? 'success' : 'warning'}
              />
              {missing[lang]?.length > 0 && (
                <div className="missing-count">
                  <XCircle size={14} className="text-error" />
                  <span>{missing[lang].length} missing</span>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Missing Translations */}
      {languages.map(lang => (
        missing[lang]?.length > 0 && (
          <Card key={`missing-${lang}`} className="missing-card">
            <CardHeader
              title={`Missing in ${lang.toUpperCase()}`}
              subtitle={`${missing[lang].length} files need translation`}
            />
            <CardContent>
              <div className="missing-list">
                {missing[lang].slice(0, 10).map(file => (
                  <div key={file} className="missing-item">
                    <XCircle size={14} className="text-error" />
                    <span className="file-path">{file}</span>
                  </div>
                ))}
                {missing[lang].length > 10 && (
                  <p className="text-muted">...and {missing[lang].length - 10} more</p>
                )}
              </div>
            </CardContent>
          </Card>
        )
      ))}

      {/* Translation Matrix */}
      {parity?.matrix && (
        <Card className="matrix-card">
          <CardHeader title="Content Matrix" subtitle="Documents by category and language" />
          <CardContent>
            <div className="matrix-table-wrapper">
              <table className="matrix-table">
                <thead>
                  <tr>
                    <th>Category</th>
                    {languages.map(lang => (
                      <th key={lang}>{lang.toUpperCase()}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(parity.matrix).map(([category, langCounts]) => (
                    <tr key={category}>
                      <td className="category-cell">{category}</td>
                      {languages.map(lang => {
                        const count = (langCounts as Record<string, number>)[lang] ?? 0;
                        const maxCount = Math.max(...Object.values(langCounts as Record<string, number>));
                        return (
                          <td key={lang} className="count-cell">
                            <Badge
                              variant={count === maxCount ? 'success' : count === 0 ? 'error' : 'warning'}
                            >
                              {count}
                            </Badge>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
