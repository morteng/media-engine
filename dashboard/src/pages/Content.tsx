import { useState, useEffect, useRef } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useProject, useDocuments, useDocument, useInsights, useSaveDocument } from '@/hooks/useApi';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { LoadingState } from '@/components/ui/Spinner';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { SubTabs } from '@/components/ui/SubTabs';
import { MarkdownPreview } from '@/components/ui/MarkdownPreview';
import { SelectionAnnotation } from '@/components/ui/SelectionAnnotation';
import {
  FileText,
  FolderOpen,
  Languages,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Eye,
  Edit3,
  Save,
  X,
  Code,
} from 'lucide-react';
import clsx from 'clsx';
import './Content.css';

const tabs = [
  { path: '', label: 'Documents' },
  { path: 'translations', label: 'Translations' },
];

// Documents Sub-page
function DocumentsView() {
  const { data: project } = useProject();
  const [selectedLang, setSelectedLang] = useState('en');
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'preview' | 'source' | 'edit'>('preview');
  const [editContent, setEditContent] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  const { data: documents, isLoading: docsLoading } = useDocuments(selectedLang);
  const { data: docData, isLoading: docLoading, refetch } = useDocument(selectedDoc ?? '');
  const saveDocument = useSaveDocument();
  const contentRef = useRef<HTMLDivElement>(null);

  const languages = project?.languages ? Object.keys(project.languages) : ['en'];

  // Update edit content when document changes
  useEffect(() => {
    if (docData?.content) {
      setEditContent(docData.content);
      setHasChanges(false);
    }
  }, [docData?.content]);

  const handleContentChange = (value: string) => {
    setEditContent(value);
    setHasChanges(value !== docData?.content);
  };

  const handleSave = async () => {
    if (!selectedDoc || !hasChanges) return;

    try {
      await saveDocument.mutateAsync({
        path: selectedDoc,
        content: editContent,
      });
      setHasChanges(false);
      setViewMode('preview');
      refetch();
    } catch (error) {
      console.error('Failed to save document:', error);
    }
  };

  const handleCancelEdit = () => {
    setEditContent(docData?.content ?? '');
    setHasChanges(false);
    setViewMode('preview');
  };

  if (docsLoading) {
    return <LoadingState message="Loading documents..." />;
  }

  const categories = documents?.categories ?? {};
  const isMarkdown = selectedDoc?.endsWith('.md');

  return (
    <div className="content-layout">
      {/* Document Tree */}
      <Card className="document-tree">
        <CardHeader
          title="Documents"
          subtitle={
            <div className="lang-pills">
              {languages.map(lang => (
                <button
                  key={lang}
                  className={clsx('lang-pill', { active: selectedLang === lang })}
                  onClick={() => { setSelectedLang(lang); setSelectedDoc(null); }}
                >
                  {lang.toUpperCase()}
                </button>
              ))}
            </div>
          }
        />
        <CardContent className="tree-content">
          {Object.entries(categories).map(([category, docs]) => (
            <div key={category} className="category-group">
              <div className="category-header">
                <FolderOpen size={14} />
                <span>{category}</span>
                <Badge variant="default" size="sm">{(docs as unknown[]).length}</Badge>
              </div>
              <div className="category-docs">
                {(docs as Array<{ path: string; title: string }>).map(doc => (
                  <button
                    key={doc.path}
                    className={clsx('doc-item', { active: selectedDoc === doc.path })}
                    onClick={() => {
                      setSelectedDoc(doc.path);
                      setViewMode('preview');
                    }}
                  >
                    <FileText size={12} />
                    <span className="doc-title">{doc.title}</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Document Viewer */}
      <Card className="document-viewer">
        {selectedDoc ? (
          <>
            <CardHeader
              title={docData?.title ?? 'Loading...'}
              subtitle={selectedDoc}
              action={
                isMarkdown && (
                  <div className="view-mode-toggle">
                    <Button
                      variant={viewMode === 'preview' ? 'primary' : 'ghost'}
                      size="sm"
                      onClick={() => setViewMode('preview')}
                      title="Preview"
                    >
                      <Eye size={14} />
                    </Button>
                    <Button
                      variant={viewMode === 'source' ? 'primary' : 'ghost'}
                      size="sm"
                      onClick={() => setViewMode('source')}
                      title="Source"
                    >
                      <Code size={14} />
                    </Button>
                    <Button
                      variant={viewMode === 'edit' ? 'primary' : 'ghost'}
                      size="sm"
                      onClick={() => setViewMode('edit')}
                      title="Edit"
                    >
                      <Edit3 size={14} />
                    </Button>
                    {viewMode === 'edit' && hasChanges && (
                      <>
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={handleSave}
                          disabled={saveDocument.isPending}
                        >
                          <Save size={14} />
                          Save
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleCancelEdit}
                        >
                          <X size={14} />
                        </Button>
                      </>
                    )}
                  </div>
                )
              }
            />
            <CardContent>
              {docLoading ? (
                <LoadingState message="Loading..." />
              ) : (
                <div className="document-content">
                  {/* Frontmatter */}
                  {docData?.metadata && Object.keys(docData.metadata).length > 0 && (
                    <details className="frontmatter-details">
                      <summary>
                        <Badge variant="info" size="sm">Frontmatter</Badge>
                      </summary>
                      <pre className="frontmatter-content">
                        {JSON.stringify(docData.metadata, null, 2)}
                      </pre>
                    </details>
                  )}

                  {/* Content based on view mode */}
                  <div ref={contentRef} className="document-content-inner">
                    {viewMode === 'preview' && docData?.html ? (
                      <MarkdownPreview html={docData.html} className="markdown-rendered" />
                    ) : viewMode === 'edit' ? (
                      <textarea
                        className="document-editor"
                        value={editContent}
                        onChange={(e) => handleContentChange(e.target.value)}
                        spellCheck={false}
                      />
                    ) : (
                      <pre className="document-source">{docData?.content ?? ''}</pre>
                    )}
                  </div>

                  {/* Selection Annotation for AI Queue */}
                  {viewMode !== 'edit' && selectedDoc && (
                    <SelectionAnnotation
                      documentPath={selectedDoc}
                      documentTitle={docData?.title ?? 'Document'}
                      contentRef={contentRef}
                      onAnnotationSubmitted={() => {
                        // Could show a toast notification here
                        console.log('Annotation queued for AI');
                      }}
                    />
                  )}
                </div>
              )}
            </CardContent>
          </>
        ) : (
          <CardContent className="empty-state">
            <FileText size={48} className="text-muted" />
            <p>Select a document</p>
          </CardContent>
        )}
      </Card>
    </div>
  );
}

// Translations Sub-page
function TranslationsView() {
  const { data: insights, isLoading: insightsLoading } = useInsights();

  if (insightsLoading) {
    return <LoadingState message="Loading translations..." />;
  }

  const parity = insights?.parity;
  const languages = parity?.languages ?? [];
  const coverage = parity?.coverage ?? {};
  const missing = parity?.missing ?? {};

  return (
    <div className="translations-content">
      {/* Coverage Cards */}
      <div className="coverage-cards">
        {languages.map(lang => (
          <Card key={lang} className={coverage[lang] === 100 ? 'card-success' : ''}>
            <CardContent>
              <div className="coverage-header">
                <Languages size={20} />
                <span className="lang-code">{lang.toUpperCase()}</span>
                {coverage[lang] === 100 ? (
                  <CheckCircle size={16} className="text-success" />
                ) : (
                  <AlertTriangle size={16} className="text-warning" />
                )}
              </div>
              <div className="coverage-value">{Math.round(coverage[lang] ?? 0)}%</div>
              <ProgressBar
                value={coverage[lang] ?? 0}
                variant={coverage[lang] === 100 ? 'success' : 'warning'}
              />
              {missing[lang]?.length > 0 && (
                <div className="missing-count">
                  <XCircle size={12} />
                  <span>{missing[lang].length} missing</span>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Missing Files */}
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
                    <XCircle size={12} className="text-error" />
                    <span>{file}</span>
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

      {/* Content Matrix */}
      {parity?.matrix && (
        <Card>
          <CardHeader title="Content Matrix" />
          <CardContent>
            <table className="matrix-table">
              <thead>
                <tr>
                  <th>Category</th>
                  {languages.map(lang => <th key={lang}>{lang.toUpperCase()}</th>)}
                </tr>
              </thead>
              <tbody>
                {Object.entries(parity.matrix).map(([category, langCounts]) => (
                  <tr key={category}>
                    <td>{category}</td>
                    {languages.map(lang => {
                      const count = (langCounts as Record<string, number>)[lang] ?? 0;
                      const maxCount = Math.max(...Object.values(langCounts as Record<string, number>));
                      return (
                        <td key={lang} className="count-cell">
                          <Badge variant={count === maxCount ? 'success' : count === 0 ? 'error' : 'warning'}>
                            {count}
                          </Badge>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Main Content Page
export function Content() {
  return (
    <div className="page content-page">
      <div className="page-header">
        <h1>Content</h1>
        <SubTabs tabs={tabs} basePath="/content" />
      </div>

      <Routes>
        <Route index element={<DocumentsView />} />
        <Route path="translations" element={<TranslationsView />} />
      </Routes>
    </div>
  );
}
