import { Routes, Route } from 'react-router-dom';
import { useBrandVoice, useVoiceCheck, useTerminologyCheck } from '@/hooks/useApi';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { LoadingState } from '@/components/ui/Spinner';
import { SubTabs } from '@/components/ui/SubTabs';
import {
  MessageCircle,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  BookOpen,
  Users,
  FileText,
  Type,
  XCircle,
} from 'lucide-react';

const tabs = [
  { path: '', label: 'Voice Profile' },
  { path: 'check', label: 'Voice Check' },
  { path: 'terminology', label: 'Terminology' },
];

// Voice Profile View
function VoiceProfileView() {
  const { data: voice, isLoading } = useBrandVoice();

  if (isLoading) {
    return <LoadingState message="Loading voice profile..." />;
  }

  if (!voice?.has_voice) {
    return (
      <Card>
        <CardContent className="empty-state">
          <MessageCircle size={48} className="text-muted" />
          <h3>No Voice Profile</h3>
          <p className="text-muted">
            {voice?.warning || 'Add a voice section to your brand.yaml to define voice guidelines.'}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="brand-content">
      {/* Hero Card */}
      <Card variant="gradient" className="brand-hero">
        <CardContent>
          <div className="brand-hero-display">
            <MessageCircle size={40} className="text-accent" />
            <div className="hero-info">
              <span className="tone-value">{voice.tone}</span>
              <span className="tone-label">Default Tone</span>
            </div>
            <Badge
              variant={voice.formality_level >= 0.7 ? 'default' : voice.formality_level >= 0.4 ? 'accent' : 'success'}
              size="lg"
            >
              {voice.formality_level >= 0.7 ? 'Formal' : voice.formality_level >= 0.4 ? 'Moderate' : 'Casual'}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Personality */}
      <Card>
        <CardHeader title="Personality" subtitle="Brand voice characteristics" />
        <CardContent>
          <div className="personality-tags">
            {voice.personality?.map((trait, idx) => (
              <Badge key={idx} variant="accent" size="md">
                {trait}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Style Targets */}
      <Card>
        <CardHeader title="Style Targets" subtitle="Writing style guidelines" />
        <CardContent>
          <div className="style-metrics">
            <div className="style-row">
              <span className="style-label">Active Voice Target</span>
              <ProgressBar
                value={voice.style.active_voice_target * 100}
                variant="success"
                showLabel
              />
            </div>
            <div className="style-row">
              <span className="style-label">Sentence Length</span>
              <span className="style-value">{voice.style.sentence_length_target} words avg</span>
            </div>
            <div className="style-row">
              <span className="style-label">Max Paragraph</span>
              <span className="style-value">{voice.style.paragraph_length_max} sentences</span>
            </div>
            <div className="style-row">
              <span className="style-label">Contractions</span>
              <Badge variant={voice.style.use_contractions ? 'success' : 'default'} size="sm">
                {voice.style.use_contractions ? 'Allowed' : 'Avoid'}
              </Badge>
            </div>
            <div className="style-row">
              <span className="style-label">Person Usage</span>
              <div className="person-badges">
                {voice.style.use_first_person && <Badge variant="accent" size="sm">First Person</Badge>}
                {voice.style.use_second_person && <Badge variant="accent" size="sm">Second Person</Badge>}
                {!voice.style.use_first_person && !voice.style.use_second_person && (
                  <Badge variant="default" size="sm">Third Person Only</Badge>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Available Overrides */}
      <div className="overrides-grid">
        {voice.available_doc_types && voice.available_doc_types.length > 0 && (
          <Card>
            <CardHeader title="Document Type Overrides" subtitle="Context-specific voice" />
            <CardContent>
              <div className="override-tags">
                {voice.available_doc_types.map((type, idx) => (
                  <Badge key={idx} variant="default" size="sm">
                    <FileText size={12} />
                    {type}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {voice.available_audiences && voice.available_audiences.length > 0 && (
          <Card>
            <CardHeader title="Audience Overrides" subtitle="Audience-specific voice" />
            <CardContent>
              <div className="override-tags">
                {voice.available_audiences.map((aud, idx) => (
                  <Badge key={idx} variant="default" size="sm">
                    <Users size={12} />
                    {aud}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Terminology Preferences */}
      {voice.preferred_terms && voice.preferred_terms.length > 0 && (
        <Card>
          <CardHeader
            title="Terminology Preferences"
            subtitle={`${voice.preferred_terms.length} term preferences`}
          />
          <CardContent>
            <div className="term-list">
              {voice.preferred_terms.slice(0, 10).map((term, idx) => (
                <div key={idx} className="term-item">
                  <span className="prefer">
                    <CheckCircle size={14} className="text-success" />
                    {term.prefer}
                  </span>
                  <span className="arrow">instead of</span>
                  <span className="avoid">{term.avoid.join(', ')}</span>
                </div>
              ))}
              {voice.preferred_terms.length > 10 && (
                <p className="text-muted">...and {voice.preferred_terms.length - 10} more</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Avoided Phrases */}
      {voice.avoid_phrases && voice.avoid_phrases.length > 0 && (
        <Card>
          <CardHeader
            title="Phrases to Avoid"
            subtitle={`${voice.avoid_phrases.length} phrases`}
          />
          <CardContent>
            <div className="avoid-list">
              {voice.avoid_phrases.slice(0, 10).map((phrase, idx) => (
                <Badge key={idx} variant="warning" size="sm">
                  <XCircle size={12} />
                  {phrase}
                </Badge>
              ))}
              {voice.avoid_phrases.length > 10 && (
                <p className="text-muted">...and {voice.avoid_phrases.length - 10} more</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Voice Check View
function VoiceCheckView() {
  const { data: voiceCheck, isLoading } = useVoiceCheck();

  if (isLoading) {
    return <LoadingState message="Checking documents..." />;
  }

  const summary = voiceCheck?.summary;
  const results = voiceCheck?.results || [];

  return (
    <div className="voice-check-content">
      {/* Summary Cards */}
      <div className="check-summary">
        <Card className="card-success">
          <CardContent>
            <CheckCircle size={24} className="text-success" />
            <span className="count">{summary?.documents_passed || 0}</span>
            <span className="label">Passed</span>
          </CardContent>
        </Card>
        <Card className={summary && summary.documents_checked - summary.documents_passed > 0 ? 'card-warning' : ''}>
          <CardContent>
            <AlertTriangle size={24} className="text-warning" />
            <span className="count">{(summary?.documents_checked || 0) - (summary?.documents_passed || 0)}</span>
            <span className="label">Need Work</span>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <AlertCircle size={24} className="text-muted" />
            <span className="count">{summary?.total_issues || 0}</span>
            <span className="label">Total Issues</span>
          </CardContent>
        </Card>
      </div>

      {/* Pass Rate */}
      <Card>
        <CardHeader title="Voice Compliance" subtitle={`${summary?.documents_checked || 0} documents checked`} />
        <CardContent>
          <div className="pass-rate">
            <div className="pass-header">
              <span className="percent">{summary?.pass_rate?.toFixed(0) || 0}%</span>
              <Badge
                variant={
                  (summary?.pass_rate || 0) >= 90 ? 'success' :
                  (summary?.pass_rate || 0) >= 70 ? 'warning' : 'error'
                }
              >
                {(summary?.pass_rate || 0) >= 90 ? 'Excellent' :
                 (summary?.pass_rate || 0) >= 70 ? 'Good' : 'Needs Improvement'}
              </Badge>
            </div>
            <ProgressBar
              value={summary?.pass_rate || 0}
              variant={(summary?.pass_rate || 0) >= 90 ? 'success' : (summary?.pass_rate || 0) >= 70 ? 'warning' : 'error'}
              size="lg"
            />
          </div>
        </CardContent>
      </Card>

      {/* Document Results */}
      <Card>
        <CardHeader title="Document Results" subtitle="Individual voice checks" />
        <CardContent>
          <div className="results-list">
            {results.map((result, idx) => (
              <div key={idx} className={`result-item ${result.passed ? 'passed' : 'failed'}`}>
                <div className="result-header">
                  {result.passed ? (
                    <CheckCircle size={16} className="text-success" />
                  ) : (
                    <AlertTriangle size={16} className="text-warning" />
                  )}
                  <span className="doc-name">{result.document_name}</span>
                  {result.metrics && (
                    <div className="metrics-inline">
                      <Badge variant="default" size="sm">
                        Active: {result.metrics.active_voice_percentage?.toFixed(0) || 0}%
                      </Badge>
                      {result.metrics.avg_sentence_length && (
                        <Badge variant="default" size="sm">
                          Sent: {result.metrics.avg_sentence_length.toFixed(0)} words
                        </Badge>
                      )}
                    </div>
                  )}
                </div>
                {result.issues.length > 0 && (
                  <div className="issues-inline">
                    {result.issues.slice(0, 3).map((issue, i) => (
                      <div key={i} className={`issue-badge severity-${issue.severity}`}>
                        <span className="issue-type">{issue.type}</span>
                        <span className="issue-msg">{issue.message}</span>
                      </div>
                    ))}
                    {result.issues.length > 3 && (
                      <span className="more-issues">+{result.issues.length - 3} more</span>
                    )}
                  </div>
                )}
              </div>
            ))}
            {results.length === 0 && (
              <div className="empty-state small">
                <BookOpen size={24} className="text-muted" />
                <p>No documents to check</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Terminology View
function TerminologyView() {
  const { data: terminology, isLoading } = useTerminologyCheck();

  if (isLoading) {
    return <LoadingState message="Checking terminology..." />;
  }

  if (terminology?.warning) {
    return (
      <Card>
        <CardContent className="empty-state">
          <Type size={48} className="text-muted" />
          <h3>No Terminology Preferences</h3>
          <p className="text-muted">{terminology.warning}</p>
        </CardContent>
      </Card>
    );
  }

  const issues = terminology?.issues || {};
  const issueCount = Object.values(issues).reduce((sum, docs) => sum + docs.length, 0);
  const uniqueIssues = Object.keys(issues).length;

  return (
    <div className="terminology-content">
      {/* Summary */}
      <div className="term-summary">
        <Card className={issueCount > 0 ? 'card-warning' : 'card-success'}>
          <CardContent>
            {issueCount > 0 ? (
              <AlertTriangle size={24} className="text-warning" />
            ) : (
              <CheckCircle size={24} className="text-success" />
            )}
            <span className="count">{issueCount}</span>
            <span className="label">Term Issues</span>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Type size={24} className="text-accent" />
            <span className="count">{terminology?.preferred_terms?.length || 0}</span>
            <span className="label">Preferred Terms</span>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <XCircle size={24} className="text-error" />
            <span className="count">{terminology?.avoid_phrases?.length || 0}</span>
            <span className="label">Avoided Phrases</span>
          </CardContent>
        </Card>
      </div>

      {/* Preferred Terms */}
      <Card>
        <CardHeader title="Preferred Terms" subtitle="Use these instead of alternatives" />
        <CardContent>
          <div className="term-grid">
            {terminology?.preferred_terms?.map((term, idx) => {
              const hasIssues = Object.keys(issues).some(msg =>
                term.avoid.some(a => msg.includes(a))
              );
              return (
                <div key={idx} className={`term-card ${hasIssues ? 'has-issues' : 'compliant'}`}>
                  <div className="term-preferred">
                    <CheckCircle size={14} className="text-success" />
                    <strong>{term.prefer}</strong>
                  </div>
                  <div className="term-avoid">
                    <span className="avoid-label">instead of:</span>
                    {term.avoid.map((a, i) => (
                      <Badge key={i} variant="warning" size="sm">{a}</Badge>
                    ))}
                  </div>
                  {hasIssues && (
                    <div className="term-status">
                      <AlertTriangle size={12} className="text-warning" />
                      <span>Issues found</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Issues by Term */}
      {uniqueIssues > 0 && (
        <Card>
          <CardHeader title="Issues Found" subtitle={`${uniqueIssues} unique terminology issues`} />
          <CardContent>
            <div className="issues-by-term">
              {Object.entries(issues).slice(0, 10).map(([msg, docs], idx) => (
                <div key={idx} className="issue-row">
                  <div className="issue-message">
                    <AlertTriangle size={14} className="text-warning" />
                    <span>{msg}</span>
                  </div>
                  <div className="issue-docs">
                    {docs.slice(0, 3).map((doc, i) => (
                      <Badge key={i} variant="default" size="sm">
                        {doc.split('/').pop()}
                      </Badge>
                    ))}
                    {docs.length > 3 && (
                      <span className="more-docs">+{docs.length - 3} more</span>
                    )}
                  </div>
                </div>
              ))}
              {uniqueIssues > 10 && (
                <p className="text-muted">...and {uniqueIssues - 10} more issues</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Avoided Phrases */}
      {terminology?.avoid_phrases && terminology.avoid_phrases.length > 0 && (
        <Card>
          <CardHeader title="Phrases to Avoid" subtitle="These should not appear in content" />
          <CardContent>
            <div className="avoid-phrases-grid">
              {terminology.avoid_phrases.map((phrase, idx) => (
                <Badge key={idx} variant="error" size="sm">
                  <XCircle size={12} />
                  {phrase}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {issueCount === 0 && (
        <Card>
          <CardContent className="empty-state">
            <CheckCircle size={48} className="text-success" />
            <h3>All Clear!</h3>
            <p className="text-muted">All documents follow terminology guidelines.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Main Brand Page
export function Brand() {
  return (
    <div className="page brand-page">
      <div className="page-header">
        <h1>Brand Voice</h1>
        <SubTabs tabs={tabs} basePath="/brand" />
      </div>

      <Routes>
        <Route index element={<VoiceProfileView />} />
        <Route path="check" element={<VoiceCheckView />} />
        <Route path="terminology" element={<TerminologyView />} />
      </Routes>
    </div>
  );
}
