import { useState, useEffect, useRef } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useProject, useDocuments, useDocument, useInsights, useSaveDocument, useHierarchyTree, useBreadcrumbs, useHierarchyNode, useFlowGraph } from '@/hooks/useApi';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { LoadingState } from '@/components/ui/Spinner';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { SubTabs } from '@/components/ui/SubTabs';
import { MarkdownPreview } from '@/components/ui/MarkdownPreview';
import { SelectionAnnotation } from '@/components/ui/SelectionAnnotation';
import { HierarchyTree, Breadcrumbs, FlowDiagram } from '@/components/hierarchy';
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
  ChevronRight,
  ChevronDown,
  GitBranch,
  Anchor,
  Users,
  List,
  Network,
} from 'lucide-react';
import clsx from 'clsx';
import './Content.css';
import { Video as VideoView } from './Video';
import { Media as MediaView } from './Media';

const tabs = [
  { path: '', label: 'Documents' },
  { path: 'hierarchy', label: 'Hierarchy' },
  { path: 'translations', label: 'Translations' },
  { path: 'video', label: 'Video' },
  { path: 'media', label: 'Media' },
];

// Documents Sub-page
function DocumentsView() {
  const { data: project } = useProject();
  const [selectedLang, setSelectedLang] = useState('en');
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'preview' | 'source' | 'edit'>('preview');
  const [editContent, setEditContent] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  const { data: documents, isLoading: docsLoading } = useDocuments(selectedLang);
  const { data: docData, isLoading: docLoading, refetch } = useDocument(selectedDoc ?? '');
  const saveDocument = useSaveDocument();
  const contentRef = useRef<HTMLDivElement>(null);

  const languages = project?.languages ? Object.keys(project.languages) : ['en'];

  // Auto-expand all categories when documents load
  useEffect(() => {
    if (documents?.categories) {
      const categoryKeys = Object.keys(documents.categories);
      setExpandedCategories(new Set(categoryKeys));
    }
  }, [documents?.categories]);

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

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };

  const handleDocSelect = (docPath: string, category: string) => {
    setSelectedDoc(docPath);
    setViewMode('preview');
    // Auto-expand the category when selecting a document
    if (!expandedCategories.has(category)) {
      setExpandedCategories(prev => new Set(prev).add(category));
    }
  };

  if (docsLoading) {
    return <LoadingState message="Loading documents..." />;
  }

  const categories = documents?.categories ?? {};
  const isMarkdown = selectedDoc?.endsWith('.md');

  return (
    <div className="documents-layout">
      {/* Sidebar - Document Tree */}
      <aside className="documents-sidebar">
        <div className="documents-sidebar-header">
          <h3>Documents</h3>
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
        </div>

        <nav className="documents-tree">
          {Object.entries(categories).map(([category, docs]) => {
            const isExpanded = expandedCategories.has(category);
            const docsList = docs as Array<{ path: string; title: string }>;
            const hasActiveDoc = docsList.some(d => d.path === selectedDoc);

            return (
              <div key={category} className="category-group">
                <button
                  className={clsx('category-header', { expanded: isExpanded, 'has-active': hasActiveDoc })}
                  onClick={() => toggleCategory(category)}
                >
                  {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  <FolderOpen size={14} />
                  <span className="category-name">{category}</span>
                  <Badge variant="default" size="sm">{docsList.length}</Badge>
                </button>

                {isExpanded && (
                  <div className="category-docs">
                    {docsList.map(doc => (
                      <button
                        key={doc.path}
                        className={clsx('doc-item', { active: selectedDoc === doc.path })}
                        onClick={() => handleDocSelect(doc.path, category)}
                      >
                        <FileText size={12} />
                        <span className="doc-title">{doc.title}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </aside>

      {/* Main Content - Document Viewer */}
      <main className="documents-main">
        {selectedDoc ? (
          <Card className="document-viewer-card">
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
                        console.log('Annotation queued for AI');
                      }}
                    />
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="empty-state-panel">
            <FileText size={48} />
            <p>Select a document to view</p>
            <span className="text-muted">Choose a category and document from the sidebar</span>
          </div>
        )}
      </main>
    </div>
  );
}

// Hierarchy Sub-page
function HierarchyView() {
  const { data: project } = useProject();
  const [selectedLang, setSelectedLang] = useState('en');
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'tree' | 'flow'>('tree');

  const { data: hierarchyTree, isLoading: treeLoading } = useHierarchyTree(selectedLang);
  const { data: nodeDetail, isLoading: nodeLoading } = useHierarchyNode(selectedPath ?? '');
  const { data: breadcrumbs } = useBreadcrumbs(selectedPath ?? '');
  const { data: flowGraph, isLoading: flowLoading } = useFlowGraph({ language: selectedLang });

  const languages = project?.languages ? Object.keys(project.languages) : ['en'];

  if (viewMode === 'tree' && treeLoading) {
    return <LoadingState message="Loading hierarchy..." />;
  }

  if (viewMode === 'flow' && flowLoading) {
    return <LoadingState message="Loading flow graph..." />;
  }

  // Flow view
  if (viewMode === 'flow') {
    return (
      <div className="hierarchy-flow-layout">
        <div className="hierarchy-flow-header">
          <div className="hierarchy-flow-controls">
            <div className="lang-pills">
              {languages.map(lang => (
                <button
                  key={lang}
                  className={clsx('lang-pill', { active: selectedLang === lang })}
                  onClick={() => { setSelectedLang(lang); setSelectedPath(null); }}
                >
                  {lang.toUpperCase()}
                </button>
              ))}
            </div>
            <div className="view-mode-pills">
              <button
                className="view-pill"
                onClick={() => setViewMode('tree')}
                title="Tree view"
              >
                <List size={14} /> Tree
              </button>
              <button
                className="view-pill active"
                onClick={() => setViewMode('flow')}
                title="Flow view"
              >
                <Network size={14} /> Flow
              </button>
            </div>
          </div>
        </div>
        <div className="hierarchy-flow-content">
          <FlowDiagram
            nodes={flowGraph?.nodes ?? []}
            edges={flowGraph?.edges ?? []}
            stalenessSummary={flowGraph?.staleness_summary}
            selectedNode={selectedPath ?? undefined}
            onNodeClick={setSelectedPath}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="hierarchy-layout">
      {/* Sidebar - Hierarchy Tree */}
      <aside className="hierarchy-sidebar">
        <div className="hierarchy-sidebar-header">
          <h3>Document Hierarchy</h3>
          <div className="lang-pills">
            {languages.map(lang => (
              <button
                key={lang}
                className={clsx('lang-pill', { active: selectedLang === lang })}
                onClick={() => { setSelectedLang(lang); setSelectedPath(null); }}
              >
                {lang.toUpperCase()}
              </button>
            ))}
          </div>
          <div className="view-mode-pills">
            <button
              className="view-pill active"
              onClick={() => setViewMode('tree')}
              title="Tree view"
            >
              <List size={14} /> Tree
            </button>
            <button
              className="view-pill"
              onClick={() => setViewMode('flow')}
              title="Flow view"
            >
              <Network size={14} /> Flow
            </button>
          </div>
        </div>

        <HierarchyTree
          nodes={hierarchyTree?.nodes ?? []}
          selectedPath={selectedPath ?? undefined}
          onSelect={setSelectedPath}
          showLegend={true}
        />

        {hierarchyTree && (
          <div className="hierarchy-stats">
            <span>{hierarchyTree.total_count} documents</span>
            <span>{hierarchyTree.root_count} root nodes</span>
          </div>
        )}
      </aside>

      {/* Main Content - Node Detail */}
      <main className="hierarchy-main">
        {selectedPath ? (
          <Card className="hierarchy-detail-card">
            {/* Breadcrumbs */}
            {breadcrumbs?.breadcrumbs && breadcrumbs.breadcrumbs.length > 0 && (
              <div className="hierarchy-breadcrumbs">
                <Breadcrumbs
                  items={breadcrumbs.breadcrumbs}
                  onNavigate={setSelectedPath}
                  showHome={true}
                />
              </div>
            )}

            <CardHeader
              title={nodeDetail?.title ?? 'Loading...'}
              subtitle={selectedPath}
              action={
                nodeDetail && (
                  <div className="node-badges">
                    <Badge variant="info">{nodeDetail.doc_type}</Badge>
                    <Badge variant={nodeDetail.lifecycle === 'living' ? 'success' : 'warning'}>
                      {nodeDetail.lifecycle}
                    </Badge>
                    {nodeDetail.is_stale && (
                      <Badge variant="warning">
                        <AlertTriangle size={12} /> Stale
                      </Badge>
                    )}
                  </div>
                )
              }
            />
            <CardContent>
              {nodeLoading ? (
                <LoadingState message="Loading details..." />
              ) : nodeDetail ? (
                <div className="node-detail-content">
                  {/* Relationships */}
                  <div className="node-detail-section">
                    <h4>Relationships</h4>
                    <div className="node-relationships">
                      {nodeDetail.parent && (
                        <div className="relationship-item">
                          <span className="relationship-label">Parent:</span>
                          <button
                            className="relationship-link"
                            onClick={() => setSelectedPath(nodeDetail.parent!)}
                          >
                            {nodeDetail.parent.split('/').pop()}
                          </button>
                        </div>
                      )}

                      {nodeDetail.children.length > 0 && (
                        <div className="relationship-item">
                          <span className="relationship-label">Children ({nodeDetail.children.length}):</span>
                          <div className="relationship-list">
                            {nodeDetail.children.map(child => (
                              <button
                                key={child}
                                className="relationship-link"
                                onClick={() => setSelectedPath(child)}
                              >
                                {child.split('/').pop()}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {nodeDetail.siblings.length > 0 && (
                        <div className="relationship-item">
                          <span className="relationship-label">Siblings ({nodeDetail.siblings.length}):</span>
                          <div className="relationship-list">
                            {nodeDetail.siblings.slice(0, 5).map(sibling => (
                              <button
                                key={sibling}
                                className="relationship-link"
                                onClick={() => setSelectedPath(sibling)}
                              >
                                {sibling.split('/').pop()}
                              </button>
                            ))}
                            {nodeDetail.siblings.length > 5 && (
                              <span className="text-muted">+{nodeDetail.siblings.length - 5} more</span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Derivations */}
                  {(nodeDetail.derived_from.length > 0 || nodeDetail.derivatives.length > 0) && (
                    <div className="node-detail-section">
                      <h4><GitBranch size={14} /> Derivations</h4>
                      <div className="node-derivations">
                        {nodeDetail.derived_from.length > 0 && (
                          <div className="derivation-group">
                            <span className="derivation-label">Derived from:</span>
                            {nodeDetail.derived_from.map(source => (
                              <div key={source.path} className="derivation-item">
                                <button
                                  className="relationship-link"
                                  onClick={() => setSelectedPath(source.path)}
                                >
                                  {source.path.split('/').pop()}
                                </button>
                                <Badge variant="default" size="sm">{source.relationship}</Badge>
                                {source.version && (
                                  <span className="text-muted">v{source.version}</span>
                                )}
                              </div>
                            ))}
                          </div>
                        )}

                        {nodeDetail.derivatives.length > 0 && (
                          <div className="derivation-group">
                            <span className="derivation-label">Derivatives:</span>
                            {nodeDetail.derivatives.map(derivative => (
                              <button
                                key={derivative}
                                className="relationship-link"
                                onClick={() => setSelectedPath(derivative)}
                              >
                                {derivative.split('/').pop()}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Anchors */}
                  {(nodeDetail.defined_anchors.length > 0 || nodeDetail.anchor_refs.length > 0) && (
                    <div className="node-detail-section">
                      <h4><Anchor size={14} /> Consistency Anchors</h4>
                      <div className="node-anchors">
                        {nodeDetail.defined_anchors.length > 0 && (
                          <div className="anchor-group">
                            <span className="anchor-label">Defined anchors:</span>
                            <div className="anchor-list">
                              {nodeDetail.defined_anchors.map(anchor => (
                                <div key={anchor.id} className="anchor-item">
                                  <code className="anchor-id">{anchor.id}</code>
                                  <span className="anchor-value">
                                    {typeof anchor.value === 'object'
                                      ? JSON.stringify(anchor.value)
                                      : String(anchor.value)}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {nodeDetail.anchor_refs.length > 0 && (
                          <div className="anchor-group">
                            <span className="anchor-label">References:</span>
                            <div className="anchor-list">
                              {nodeDetail.anchor_refs.map((ref, idx) => (
                                <div key={idx} className="anchor-ref-item">
                                  <button
                                    className="relationship-link"
                                    onClick={() => setSelectedPath(ref.source)}
                                  >
                                    {ref.source.split('/').pop()}
                                  </button>
                                  <span className="text-muted">#</span>
                                  <code className="anchor-id">{ref.anchor}</code>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Ownership */}
                  {(nodeDetail.owner || nodeDetail.approvers.length > 0) && (
                    <div className="node-detail-section">
                      <h4><Users size={14} /> Ownership</h4>
                      <div className="node-ownership">
                        {nodeDetail.owner && (
                          <div className="ownership-item">
                            <span className="ownership-label">Owner:</span>
                            <span>{nodeDetail.owner}</span>
                          </div>
                        )}
                        {nodeDetail.approvers.length > 0 && (
                          <div className="ownership-item">
                            <span className="ownership-label">Approvers:</span>
                            <span>{nodeDetail.approvers.join(', ')}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="empty-state-panel">
                  <AlertTriangle size={32} />
                  <p>Could not load document details</p>
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="empty-state-panel">
            <GitBranch size={48} />
            <p>Select a document to view its hierarchy</p>
            <span className="text-muted">Click on any node in the tree to see relationships, derivations, and anchors</span>
          </div>
        )}
      </main>
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
        <Route path="hierarchy" element={<HierarchyView />} />
        <Route path="translations" element={<TranslationsView />} />
        <Route path="video/*" element={<VideoView />} />
        <Route path="media" element={<MediaView />} />
      </Routes>
    </div>
  );
}
