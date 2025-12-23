import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getMedia } from '@/api/client';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingState } from '@/components/ui/Spinner';
import { MediaPlayer } from '@/components/ui/MediaPlayer';
import {
  Video,
  Music,
  FileText,
  Image,
  Captions,
  FileCode,
  Film,
  FolderOpen,
  Play,
  Clock,
  HardDrive,
} from 'lucide-react';
import clsx from 'clsx';
import './Media.css';

interface MediaSource {
  path: string;
  name: string;
  language: string;
  type: string;
}

interface MediaFile {
  path: string;
  relative_path: string;
  filename: string;
  type: 'video' | 'audio' | 'captions' | 'video_props' | 'demo' | 'document';
  format: string;
  size: number;
  modified: string;
  source: MediaSource | null;
  url: string;
}

interface MediaResponse {
  total: number;
  by_type: Record<string, number>;
  files: MediaFile[];
  output_dir: string;
}

const typeIcons: Record<string, typeof Video> = {
  video: Video,
  audio: Music,
  captions: Captions,
  video_props: FileCode,
  demo: Film,
  document: FileText,
};

const typeLabels: Record<string, string> = {
  video: 'Videos',
  audio: 'Audio',
  captions: 'Captions',
  video_props: 'Props',
  demo: 'Demos',
  document: 'Documents',
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function Media() {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<MediaFile | null>(null);

  const { data, isLoading, error } = useQuery<MediaResponse>({
    queryKey: ['media'],
    queryFn: () => getMedia() as Promise<MediaResponse>,
  });

  if (isLoading) {
    return <LoadingState message="Loading media files..." />;
  }

  if (error) {
    return (
      <div className="page media-page">
        <div className="page-header">
          <h1>Media</h1>
        </div>
        <Card>
          <CardContent className="empty-state">
            <p className="text-error">Failed to load media files</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const files = data?.files ?? [];
  const byType = data?.by_type ?? {};

  const filteredFiles = selectedType
    ? files.filter(f => f.type === selectedType)
    : files;

  const typeOrder = ['video', 'audio', 'captions', 'demo', 'document', 'video_props'];
  const sortedTypes = Object.keys(byType).sort(
    (a, b) => typeOrder.indexOf(a) - typeOrder.indexOf(b)
  );

  return (
    <div className="page media-page">
      <div className="page-header">
        <h1>Media</h1>
        <p className="text-muted">{data?.total ?? 0} files in {data?.output_dir ?? 'output'}</p>
      </div>

      <div className="media-layout">
        {/* Type Filter Sidebar */}
        <Card className="media-types">
          <CardHeader title="Types" />
          <CardContent>
            <button
              className={clsx('type-item', { active: selectedType === null })}
              onClick={() => setSelectedType(null)}
            >
              <FolderOpen size={16} />
              <span>All Files</span>
              <Badge variant="default" size="sm">{data?.total ?? 0}</Badge>
            </button>
            {sortedTypes.map(type => {
              const Icon = typeIcons[type] || FileText;
              return (
                <button
                  key={type}
                  className={clsx('type-item', { active: selectedType === type })}
                  onClick={() => setSelectedType(type)}
                >
                  <Icon size={16} />
                  <span>{typeLabels[type] || type}</span>
                  <Badge variant="default" size="sm">{byType[type]}</Badge>
                </button>
              );
            })}
          </CardContent>
        </Card>

        {/* File List */}
        <Card className="media-files">
          <CardHeader
            title={selectedType ? typeLabels[selectedType] || selectedType : 'All Files'}
            subtitle={`${filteredFiles.length} files`}
          />
          <CardContent>
            {filteredFiles.length === 0 ? (
              <div className="empty-state">
                <Image size={48} className="text-muted" />
                <p>No media files found</p>
              </div>
            ) : (
              <div className="file-list">
                {filteredFiles.map(file => {
                  const Icon = typeIcons[file.type] || FileText;
                  return (
                    <button
                      key={file.path}
                      className={clsx('file-item', { active: selectedFile?.path === file.path })}
                      onClick={() => setSelectedFile(file)}
                    >
                      <Icon size={20} className="file-icon" />
                      <div className="file-info">
                        <span className="file-name">{file.filename}</span>
                        <span className="file-meta">
                          <HardDrive size={10} />
                          {formatSize(file.size)}
                          <Clock size={10} />
                          {formatDate(file.modified)}
                        </span>
                      </div>
                      {(file.type === 'video' || file.type === 'audio') && (
                        <Play size={16} className="play-icon" />
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Preview Panel */}
        <Card className="media-preview">
          <CardHeader title="Preview" />
          <CardContent>
            {selectedFile ? (
              <div className="preview-content">
                {(selectedFile.type === 'video' || selectedFile.type === 'audio') && (
                  <MediaPlayer
                    src={selectedFile.url}
                    type={selectedFile.type}
                    title={selectedFile.filename}
                  />
                )}

                {selectedFile.type === 'demo' && (
                  <div className="demo-preview">
                    <iframe
                      src={selectedFile.url}
                      title={selectedFile.filename}
                      sandbox="allow-scripts allow-same-origin"
                    />
                  </div>
                )}

                {selectedFile.type === 'document' && selectedFile.format === 'html' && (
                  <div className="document-preview">
                    <iframe
                      src={selectedFile.url}
                      title={selectedFile.filename}
                    />
                  </div>
                )}

                {selectedFile.type === 'captions' && (
                  <div className="captions-preview">
                    <Badge variant="info">VTT Captions</Badge>
                    <a href={selectedFile.url} target="_blank" rel="noopener noreferrer">
                      Download {selectedFile.filename}
                    </a>
                  </div>
                )}

                {selectedFile.type === 'video_props' && (
                  <div className="props-preview">
                    <Badge variant="info">Video Properties</Badge>
                    <a href={selectedFile.url} target="_blank" rel="noopener noreferrer">
                      View {selectedFile.filename}
                    </a>
                  </div>
                )}

                <div className="file-details">
                  <dl>
                    <dt>Path</dt>
                    <dd>{selectedFile.relative_path}</dd>
                    <dt>Format</dt>
                    <dd>{selectedFile.format.toUpperCase()}</dd>
                    <dt>Size</dt>
                    <dd>{formatSize(selectedFile.size)}</dd>
                    <dt>Modified</dt>
                    <dd>{formatDate(selectedFile.modified)}</dd>
                    {selectedFile.source && (
                      <>
                        <dt>Source</dt>
                        <dd>{selectedFile.source.name} ({selectedFile.source.language})</dd>
                      </>
                    )}
                  </dl>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <Play size={48} className="text-muted" />
                <p>Select a file to preview</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
