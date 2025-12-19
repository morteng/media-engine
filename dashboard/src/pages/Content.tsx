import { useState } from 'react';
import { useProject, useDocuments, useFile } from '@/hooks/useApi';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingState } from '@/components/ui/Spinner';
import { Button } from '@/components/ui/Button';
import {
  FileText,
  FolderOpen,
  ChevronRight,
  Film,
  Image,
  BarChart3,
  Presentation,
  Database,
  Play
} from 'lucide-react';
import clsx from 'clsx';

const typeIcons: Record<string, typeof FileText> = {
  chapters: FileText,
  scripts: Film,
  slides: Presentation,
  diagrams: BarChart3,
  data: Database,
  demos: Play,
  media: Image,
};

export function Content() {
  const { data: project } = useProject();
  const [selectedLang, setSelectedLang] = useState('en');
  const [selectedDoc, setSelectedDoc] = useState<string | null>(null);

  const { data: documents, isLoading: docsLoading } = useDocuments(selectedLang);
  const { data: fileData, isLoading: fileLoading } = useFile(selectedDoc ?? '');

  const languages = project?.languages ?? ['en'];

  if (docsLoading) {
    return <LoadingState message="Loading documents..." />;
  }

  const categories = documents?.categories ?? {};

  return (
    <div className="page content-page">
      <div className="page-header">
        <div>
          <h1>Content</h1>
          <p className="text-muted">Browse and manage your documentation</p>
        </div>
        <div className="language-switcher">
          {languages.map(lang => (
            <Button
              key={lang}
              variant={selectedLang === lang ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => {
                setSelectedLang(lang);
                setSelectedDoc(null);
              }}
            >
              {lang.toUpperCase()}
            </Button>
          ))}
        </div>
      </div>

      <div className="content-layout">
        {/* Document Tree */}
        <Card className="document-tree">
          <CardHeader title="Documents" subtitle={`${selectedLang.toUpperCase()} content`} />
          <CardContent className="tree-content">
            {Object.entries(categories).map(([category, docs]) => {
              const Icon = typeIcons[category] ?? FolderOpen;
              return (
                <div key={category} className="category-group">
                  <div className="category-header">
                    <Icon size={16} />
                    <span>{category}</span>
                    <Badge variant="default" size="sm">{(docs as unknown[]).length}</Badge>
                  </div>
                  <div className="category-docs">
                    {(docs as Array<{ path: string; title: string; type: string }>).map(doc => (
                      <button
                        key={doc.path}
                        className={clsx('doc-item', { active: selectedDoc === doc.path })}
                        onClick={() => setSelectedDoc(doc.path)}
                      >
                        <ChevronRight size={14} />
                        <span className="doc-title">{doc.title}</span>
                      </button>
                    ))}
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Document Viewer */}
        <Card className="document-viewer">
          {selectedDoc ? (
            <>
              <CardHeader
                title={fileData?.filename ?? 'Loading...'}
                subtitle={selectedDoc}
              />
              <CardContent>
                {fileLoading ? (
                  <LoadingState message="Loading document..." />
                ) : (
                  <div className="document-content">
                    {fileData?.parsed && (
                      <div className="frontmatter">
                        <h4>Frontmatter</h4>
                        <pre>{JSON.stringify(fileData.parsed, null, 2)}</pre>
                      </div>
                    )}
                    <div className="markdown-content">
                      <pre>{fileData?.content}</pre>
                    </div>
                  </div>
                )}
              </CardContent>
            </>
          ) : (
            <CardContent className="empty-state">
              <FileText size={48} className="text-muted" />
              <p>Select a document to view its content</p>
            </CardContent>
          )}
        </Card>
      </div>
    </div>
  );
}
