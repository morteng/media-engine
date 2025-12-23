import { useState, useEffect, useRef } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useProject, useDocuments, useDocument, useInsights, useSaveDocument, useHierarchyTree, useBreadcrumbs, useHierarchyNode, useFlowGraph } from '@/hooks/useApi';
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
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <span className="loading loading-spinner loading-lg text-primary"></span>
          <p className="mt-4 text-base-content/60">Loading documents...</p>
        </div>
      </div>
    );
  }

  const categories = documents?.categories ?? {};
  const isMarkdown = selectedDoc?.endsWith('.md');

  return (
    <div className="flex gap-6 h-[calc(100vh-200px)]">
      {/* Sidebar - Document Tree */}
      <aside className="w-72 flex-shrink-0 flex flex-col bg-base-200 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-base-300">
          <h3 className="font-semibold mb-3">Documents</h3>
          <div className="flex gap-1">
            {languages.map(lang => (
              <button
                key={lang}
                className={`btn btn-xs ${selectedLang === lang ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => { setSelectedLang(lang); setSelectedDoc(null); }}
              >
                {lang.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto p-2">
          {Object.entries(categories).map(([category, docs]) => {
            const isExpanded = expandedCategories.has(category);
            const docsList = docs as Array<{ path: string; title: string }>;
            const hasActiveDoc = docsList.some(d => d.path === selectedDoc);

            return (
              <div key={category} className="mb-1">
                <button
                  className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left text-sm hover:bg-base-300 transition-colors ${hasActiveDoc ? 'bg-base-300' : ''}`}
                  onClick={() => toggleCategory(category)}
                >
                  {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  <FolderOpen size={14} className="text-primary" />
                  <span className="flex-1 truncate">{category}</span>
                  <div className="badge badge-ghost badge-sm">{docsList.length}</div>
                </button>

                {isExpanded && (
                  <div className="ml-4 mt-1 space-y-0.5">
                    {docsList.map(doc => (
                      <button
                        key={doc.path}
                        className={`w-full flex items-center gap-2 px-3 py-1.5 rounded text-left text-sm transition-colors ${selectedDoc === doc.path ? 'bg-primary/20 text-primary' : 'hover:bg-base-300 text-base-content/80'}`}
                        onClick={() => handleDocSelect(doc.path, category)}
                      >
                        <FileText size={12} />
                        <span className="truncate">{doc.title}</span>
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
      <main className="flex-1 min-w-0">
        {selectedDoc ? (
          <div className="card bg-base-200 h-full flex flex-col">
            <div className="p-4 border-b border-base-300 flex items-start justify-between gap-4">
              <div className="min-w-0">
                <h3 className="font-semibold truncate">{docData?.title ?? 'Loading...'}</h3>
                <p className="text-sm text-base-content/60 truncate">{selectedDoc}</p>
              </div>
              {isMarkdown && (
                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    className={`btn btn-sm ${viewMode === 'preview' ? 'btn-primary' : 'btn-ghost'}`}
                    onClick={() => setViewMode('preview')}
                    title="Preview"
                  >
                    <Eye size={14} />
                  </button>
                  <button
                    className={`btn btn-sm ${viewMode === 'source' ? 'btn-primary' : 'btn-ghost'}`}
                    onClick={() => setViewMode('source')}
                    title="Source"
                  >
                    <Code size={14} />
                  </button>
                  <button
                    className={`btn btn-sm ${viewMode === 'edit' ? 'btn-primary' : 'btn-ghost'}`}
                    onClick={() => setViewMode('edit')}
                    title="Edit"
                  >
                    <Edit3 size={14} />
                  </button>
                  {viewMode === 'edit' && hasChanges && (
                    <>
                      <button
                        className="btn btn-primary btn-sm gap-1"
                        onClick={handleSave}
                        disabled={saveDocument.isPending}
                      >
                        <Save size={14} />
                        Save
                      </button>
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={handleCancelEdit}
                      >
                        <X size={14} />
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {docLoading ? (
                <div className="flex items-center justify-center h-full">
                  <span className="loading loading-spinner loading-md text-primary"></span>
                </div>
              ) : (
                <div className="document-content">
                  {/* Frontmatter */}
                  {docData?.metadata && Object.keys(docData.metadata).length > 0 && (
                    <details className="collapse collapse-arrow bg-base-300 mb-4">
                      <summary className="collapse-title text-sm font-medium py-2 min-h-0">
                        <div className="badge badge-info badge-sm">Frontmatter</div>
                      </summary>
                      <div className="collapse-content">
                        <pre className="text-xs bg-base-100 p-3 rounded overflow-x-auto">
                          {JSON.stringify(docData.metadata, null, 2)}
                        </pre>
                      </div>
                    </details>
                  )}

                  {/* Content based on view mode */}
                  <div ref={contentRef}>
                    {viewMode === 'preview' && docData?.html ? (
                      <MarkdownPreview html={docData.html} className="prose prose-invert max-w-none" />
                    ) : viewMode === 'edit' ? (
                      <textarea
                        className="textarea textarea-bordered w-full h-[500px] font-mono text-sm"
                        value={editContent}
                        onChange={(e) => handleContentChange(e.target.value)}
                        spellCheck={false}
                      />
                    ) : (
                      <pre className="bg-base-300 p-4 rounded-lg overflow-x-auto text-sm">{docData?.content ?? ''}</pre>
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
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <FileText size={48} className="text-base-content/30 mb-4" />
            <p className="text-lg">Select a document to view</p>
            <span className="text-sm text-base-content/60">Choose a category and document from the sidebar</span>
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
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <span className="loading loading-spinner loading-lg text-primary"></span>
          <p className="mt-4 text-base-content/60">Loading hierarchy...</p>
        </div>
      </div>
    );
  }

  if (viewMode === 'flow' && flowLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <span className="loading loading-spinner loading-lg text-primary"></span>
          <p className="mt-4 text-base-content/60">Loading flow graph...</p>
        </div>
      </div>
    );
  }

  // Flow view
  if (viewMode === 'flow') {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex gap-1">
            {languages.map(lang => (
              <button
                key={lang}
                className={`btn btn-xs ${selectedLang === lang ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => { setSelectedLang(lang); setSelectedPath(null); }}
              >
                {lang.toUpperCase()}
              </button>
            ))}
          </div>
          <div className="flex gap-1">
            <button
              className="btn btn-xs btn-ghost gap-1"
              onClick={() => setViewMode('tree')}
            >
              <List size={14} /> Tree
            </button>
            <button
              className="btn btn-xs btn-primary gap-1"
              onClick={() => setViewMode('flow')}
            >
              <Network size={14} /> Flow
            </button>
          </div>
        </div>
        <div className="h-[calc(100vh-280px)] bg-base-200 rounded-lg overflow-hidden">
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
    <div className="flex gap-6 h-[calc(100vh-200px)]">
      {/* Sidebar - Hierarchy Tree */}
      <aside className="w-80 flex-shrink-0 flex flex-col bg-base-200 rounded-lg overflow-hidden">
        <div className="p-4 border-b border-base-300 space-y-3">
          <h3 className="font-semibold">Document Hierarchy</h3>
          <div className="flex gap-1">
            {languages.map(lang => (
              <button
                key={lang}
                className={`btn btn-xs ${selectedLang === lang ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => { setSelectedLang(lang); setSelectedPath(null); }}
              >
                {lang.toUpperCase()}
              </button>
            ))}
          </div>
          <div className="flex gap-1">
            <button
              className="btn btn-xs btn-primary gap-1"
              onClick={() => setViewMode('tree')}
            >
              <List size={14} /> Tree
            </button>
            <button
              className="btn btn-xs btn-ghost gap-1"
              onClick={() => setViewMode('flow')}
            >
              <Network size={14} /> Flow
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          <HierarchyTree
            nodes={hierarchyTree?.nodes ?? []}
            selectedPath={selectedPath ?? undefined}
            onSelect={setSelectedPath}
            showLegend={true}
          />
        </div>

        {hierarchyTree && (
          <div className="p-3 border-t border-base-300 flex gap-4 text-xs text-base-content/60">
            <span>{hierarchyTree.total_count} documents</span>
            <span>{hierarchyTree.root_count} root nodes</span>
          </div>
        )}
      </aside>

      {/* Main Content - Node Detail */}
      <main className="flex-1 min-w-0">
        {selectedPath ? (
          <div className="card bg-base-200 h-full flex flex-col">
            {/* Breadcrumbs */}
            {breadcrumbs?.breadcrumbs && breadcrumbs.breadcrumbs.length > 0 && (
              <div className="px-4 pt-4">
                <Breadcrumbs
                  items={breadcrumbs.breadcrumbs}
                  onNavigate={setSelectedPath}
                  showHome={true}
                />
              </div>
            )}

            <div className="p-4 border-b border-base-300 flex items-start justify-between gap-4">
              <div className="min-w-0">
                <h3 className="font-semibold truncate">{nodeDetail?.title ?? 'Loading...'}</h3>
                <p className="text-sm text-base-content/60 truncate">{selectedPath}</p>
              </div>
              {nodeDetail && (
                <div className="flex gap-2 flex-shrink-0">
                  <div className="badge badge-info">{nodeDetail.doc_type}</div>
                  <div className={`badge ${nodeDetail.lifecycle === 'living' ? 'badge-success' : 'badge-warning'}`}>
                    {nodeDetail.lifecycle}
                  </div>
                  {nodeDetail.is_stale && (
                    <div className="badge badge-warning gap-1">
                      <AlertTriangle size={12} /> Stale
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {nodeLoading ? (
                <div className="flex items-center justify-center h-full">
                  <span className="loading loading-spinner loading-md text-primary"></span>
                </div>
              ) : nodeDetail ? (
                <div className="space-y-6">
                  {/* Relationships */}
                  <div>
                    <h4 className="font-medium mb-3">Relationships</h4>
                    <div className="space-y-3">
                      {nodeDetail.parent && (
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-base-content/60 w-20">Parent:</span>
                          <button
                            className="btn btn-ghost btn-xs"
                            onClick={() => setSelectedPath(nodeDetail.parent!)}
                          >
                            {nodeDetail.parent.split('/').pop()}
                          </button>
                        </div>
                      )}

                      {nodeDetail.children.length > 0 && (
                        <div>
                          <span className="text-sm text-base-content/60">Children ({nodeDetail.children.length}):</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {nodeDetail.children.map(child => (
                              <button
                                key={child}
                                className="btn btn-ghost btn-xs"
                                onClick={() => setSelectedPath(child)}
                              >
                                {child.split('/').pop()}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {nodeDetail.siblings.length > 0 && (
                        <div>
                          <span className="text-sm text-base-content/60">Siblings ({nodeDetail.siblings.length}):</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {nodeDetail.siblings.slice(0, 5).map(sibling => (
                              <button
                                key={sibling}
                                className="btn btn-ghost btn-xs"
                                onClick={() => setSelectedPath(sibling)}
                              >
                                {sibling.split('/').pop()}
                              </button>
                            ))}
                            {nodeDetail.siblings.length > 5 && (
                              <span className="text-xs text-base-content/50">+{nodeDetail.siblings.length - 5} more</span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Derivations */}
                  {(nodeDetail.derived_from.length > 0 || nodeDetail.derivatives.length > 0) && (
                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2">
                        <GitBranch size={14} /> Derivations
                      </h4>
                      <div className="space-y-3">
                        {nodeDetail.derived_from.length > 0 && (
                          <div>
                            <span className="text-sm text-base-content/60">Derived from:</span>
                            <div className="space-y-1 mt-1">
                              {nodeDetail.derived_from.map(source => (
                                <div key={source.path} className="flex items-center gap-2">
                                  <button
                                    className="btn btn-ghost btn-xs"
                                    onClick={() => setSelectedPath(source.path)}
                                  >
                                    {source.path.split('/').pop()}
                                  </button>
                                  <div className="badge badge-ghost badge-sm">{source.relationship}</div>
                                  {source.version && (
                                    <span className="text-xs text-base-content/50">v{source.version}</span>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {nodeDetail.derivatives.length > 0 && (
                          <div>
                            <span className="text-sm text-base-content/60">Derivatives:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {nodeDetail.derivatives.map(derivative => (
                                <button
                                  key={derivative}
                                  className="btn btn-ghost btn-xs"
                                  onClick={() => setSelectedPath(derivative)}
                                >
                                  {derivative.split('/').pop()}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Anchors */}
                  {(nodeDetail.defined_anchors.length > 0 || nodeDetail.anchor_refs.length > 0) && (
                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2">
                        <Anchor size={14} /> Consistency Anchors
                      </h4>
                      <div className="space-y-3">
                        {nodeDetail.defined_anchors.length > 0 && (
                          <div>
                            <span className="text-sm text-base-content/60">Defined anchors:</span>
                            <div className="space-y-1 mt-1">
                              {nodeDetail.defined_anchors.map(anchor => (
                                <div key={anchor.id} className="flex items-center gap-2 text-sm">
                                  <code className="bg-base-300 px-2 py-0.5 rounded text-xs">{anchor.id}</code>
                                  <span className="text-base-content/70 truncate">
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
                          <div>
                            <span className="text-sm text-base-content/60">References:</span>
                            <div className="space-y-1 mt-1">
                              {nodeDetail.anchor_refs.map((ref, idx) => (
                                <div key={idx} className="flex items-center gap-2 text-sm">
                                  <button
                                    className="btn btn-ghost btn-xs"
                                    onClick={() => setSelectedPath(ref.source)}
                                  >
                                    {ref.source.split('/').pop()}
                                  </button>
                                  <span className="text-base-content/50">#</span>
                                  <code className="bg-base-300 px-2 py-0.5 rounded text-xs">{ref.anchor}</code>
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
                    <div>
                      <h4 className="font-medium mb-3 flex items-center gap-2">
                        <Users size={14} /> Ownership
                      </h4>
                      <div className="space-y-2 text-sm">
                        {nodeDetail.owner && (
                          <div className="flex items-center gap-2">
                            <span className="text-base-content/60">Owner:</span>
                            <span>{nodeDetail.owner}</span>
                          </div>
                        )}
                        {nodeDetail.approvers.length > 0 && (
                          <div className="flex items-center gap-2">
                            <span className="text-base-content/60">Approvers:</span>
                            <span>{nodeDetail.approvers.join(', ')}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <AlertTriangle size={32} className="text-warning mb-4" />
                  <p>Could not load document details</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <GitBranch size={48} className="text-base-content/30 mb-4" />
            <p className="text-lg">Select a document to view its hierarchy</p>
            <span className="text-sm text-base-content/60">Click on any node in the tree to see relationships, derivations, and anchors</span>
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
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <span className="loading loading-spinner loading-lg text-primary"></span>
          <p className="mt-4 text-base-content/60">Loading translations...</p>
        </div>
      </div>
    );
  }

  const parity = insights?.parity;
  const languages = parity?.languages ?? [];
  const coverage = parity?.coverage ?? {};
  const missing = parity?.missing ?? {};

  return (
    <div className="space-y-6">
      {/* Coverage Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {languages.map(lang => (
          <div key={lang} className={`card bg-base-200 ${coverage[lang] === 100 ? 'border border-success/30' : ''}`}>
            <div className="card-body p-4">
              <div className="flex items-center gap-2 mb-2">
                <Languages size={20} className="text-primary" />
                <span className="font-semibold">{lang.toUpperCase()}</span>
                {coverage[lang] === 100 ? (
                  <CheckCircle size={16} className="text-success ml-auto" />
                ) : (
                  <AlertTriangle size={16} className="text-warning ml-auto" />
                )}
              </div>
              <div className="text-3xl font-bold mb-2">{Math.round(coverage[lang] ?? 0)}%</div>
              <progress
                className={`progress ${coverage[lang] === 100 ? 'progress-success' : 'progress-warning'} w-full`}
                value={coverage[lang] ?? 0}
                max="100"
              ></progress>
              {missing[lang]?.length > 0 && (
                <div className="flex items-center gap-1 mt-2 text-sm text-error">
                  <XCircle size={12} />
                  <span>{missing[lang].length} missing</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Missing Files */}
      {languages.map(lang => (
        missing[lang]?.length > 0 && (
          <div key={`missing-${lang}`} className="card bg-base-200">
            <div className="card-body">
              <h3 className="card-title text-lg">Missing in {lang.toUpperCase()}</h3>
              <p className="text-sm text-base-content/60 mb-4">{missing[lang].length} files need translation</p>
              <div className="space-y-2">
                {missing[lang].slice(0, 10).map(file => (
                  <div key={file} className="flex items-center gap-2 text-sm">
                    <XCircle size={12} className="text-error flex-shrink-0" />
                    <span className="truncate">{file}</span>
                  </div>
                ))}
                {missing[lang].length > 10 && (
                  <p className="text-sm text-base-content/60">...and {missing[lang].length - 10} more</p>
                )}
              </div>
            </div>
          </div>
        )
      ))}

      {/* Content Matrix */}
      {parity?.matrix && (
        <div className="card bg-base-200">
          <div className="card-body">
            <h3 className="card-title text-lg mb-4">Content Matrix</h3>
            <div className="overflow-x-auto">
              <table className="table table-sm">
                <thead>
                  <tr>
                    <th>Category</th>
                    {languages.map(lang => <th key={lang} className="text-center">{lang.toUpperCase()}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(parity.matrix).map(([category, langCounts]) => (
                    <tr key={category}>
                      <td className="font-medium">{category}</td>
                      {languages.map(lang => {
                        const count = (langCounts as Record<string, number>)[lang] ?? 0;
                        const maxCount = Math.max(...Object.values(langCounts as Record<string, number>));
                        return (
                          <td key={lang} className="text-center">
                            <div className={`badge ${count === maxCount ? 'badge-success' : count === 0 ? 'badge-error' : 'badge-warning'}`}>
                              {count}
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Main Content Page
export function Content() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Content</h1>
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
