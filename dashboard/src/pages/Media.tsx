import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getMedia } from '@/api/client';
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
import { formatSize, formatDate } from '@/utils/format';
import { Spinner, NoMediaState, EmptyState } from '@/components/ui';

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

export function Media() {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<MediaFile | null>(null);

  const { data, isLoading, error } = useQuery<MediaResponse>({
    queryKey: ['media'],
    queryFn: () => getMedia() as Promise<MediaResponse>,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Spinner size="lg" className="text-primary" />
          <p className="mt-4 text-base-content/60">Loading media files...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Media</h1>
        <div className="card bg-base-200">
          <EmptyState
            icon={<Image size={48} strokeWidth={1.5} className="text-error" />}
            title="Failed to load media files"
            description="An error occurred while loading media files"
          />
        </div>
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Media</h1>
          <p className="text-sm text-base-content/60">{data?.total ?? 0} files in {data?.output_dir ?? 'output'}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-220px)]">
        {/* Type Filter Sidebar */}
        <div className="lg:col-span-2">
          <div className="card bg-base-200 h-full">
            <div className="card-body p-3">
              <h3 className="font-semibold text-sm mb-2 px-2">Types</h3>
              <div className="space-y-1">
                <button
                  className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                    selectedType === null ? 'bg-primary/20 text-primary' : 'hover:bg-base-300'
                  }`}
                  onClick={() => setSelectedType(null)}
                >
                  <FolderOpen size={16} />
                  <span className="flex-1 text-left">All Files</span>
                  <div className="badge badge-ghost badge-sm">{data?.total ?? 0}</div>
                </button>
                {sortedTypes.map(type => {
                  const Icon = typeIcons[type] || FileText;
                  return (
                    <button
                      key={type}
                      className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                        selectedType === type ? 'bg-primary/20 text-primary' : 'hover:bg-base-300'
                      }`}
                      onClick={() => setSelectedType(type)}
                    >
                      <Icon size={16} />
                      <span className="flex-1 text-left">{typeLabels[type] || type}</span>
                      <div className="badge badge-ghost badge-sm">{byType[type]}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* File List */}
        <div className="lg:col-span-4">
          <div className="card bg-base-200 h-full flex flex-col">
            <div className="p-4 border-b border-base-300">
              <h3 className="font-semibold">{selectedType ? typeLabels[selectedType] || selectedType : 'All Files'}</h3>
              <p className="text-sm text-base-content/60">{filteredFiles.length} files</p>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              {filteredFiles.length === 0 ? (
                <NoMediaState />
              ) : (
                <div className="space-y-1">
                  {filteredFiles.map(file => {
                    const Icon = typeIcons[file.type] || FileText;
                    return (
                      <button
                        key={file.path}
                        className={`w-full flex items-center gap-3 p-3 rounded-lg text-left transition-colors ${
                          selectedFile?.path === file.path ? 'bg-primary/20' : 'hover:bg-base-300'
                        }`}
                        onClick={() => setSelectedFile(file)}
                      >
                        <Icon size={20} className="text-base-content/60 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <span className="block truncate text-sm font-medium">{file.filename}</span>
                          <span className="flex items-center gap-2 text-xs text-base-content/50">
                            <HardDrive size={10} />
                            {formatSize(file.size)}
                            <Clock size={10} />
                            {formatDate(file.modified)}
                          </span>
                        </div>
                        {(file.type === 'video' || file.type === 'audio') && (
                          <Play size={16} className="text-primary flex-shrink-0" />
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Preview Panel */}
        <div className="lg:col-span-6">
          <div className="card bg-base-200 h-full flex flex-col">
            <div className="p-4 border-b border-base-300">
              <h3 className="font-semibold">Preview</h3>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {selectedFile ? (
                <div className="space-y-4">
                  {(selectedFile.type === 'video' || selectedFile.type === 'audio') && (
                    <MediaPlayer
                      src={selectedFile.url}
                      type={selectedFile.type}
                      title={selectedFile.filename}
                    />
                  )}

                  {selectedFile.type === 'demo' && (
                    <div className="aspect-video rounded-lg overflow-hidden bg-base-300">
                      <iframe
                        src={selectedFile.url}
                        title={selectedFile.filename}
                        className="w-full h-full"
                        sandbox="allow-scripts allow-same-origin"
                      />
                    </div>
                  )}

                  {selectedFile.type === 'document' && selectedFile.format === 'html' && (
                    <div className="aspect-video rounded-lg overflow-hidden bg-base-300">
                      <iframe
                        src={selectedFile.url}
                        title={selectedFile.filename}
                        className="w-full h-full"
                      />
                    </div>
                  )}

                  {selectedFile.type === 'captions' && (
                    <div className="flex flex-col items-center gap-3 p-6 rounded-lg bg-base-300">
                      <div className="badge badge-info">VTT Captions</div>
                      <a
                        href={selectedFile.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-ghost btn-sm"
                      >
                        Download {selectedFile.filename}
                      </a>
                    </div>
                  )}

                  {selectedFile.type === 'video_props' && (
                    <div className="flex flex-col items-center gap-3 p-6 rounded-lg bg-base-300">
                      <div className="badge badge-info">Video Properties</div>
                      <a
                        href={selectedFile.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-ghost btn-sm"
                      >
                        View {selectedFile.filename}
                      </a>
                    </div>
                  )}

                  <div className="p-4 rounded-lg bg-base-300">
                    <dl className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <dt className="text-base-content/60">Path</dt>
                        <dd className="truncate max-w-[60%] text-right">{selectedFile.relative_path}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-base-content/60">Format</dt>
                        <dd>{selectedFile.format.toUpperCase()}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-base-content/60">Size</dt>
                        <dd>{formatSize(selectedFile.size)}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-base-content/60">Modified</dt>
                        <dd>{formatDate(selectedFile.modified)}</dd>
                      </div>
                      {selectedFile.source && (
                        <div className="flex justify-between">
                          <dt className="text-base-content/60">Source</dt>
                          <dd>{selectedFile.source.name} ({selectedFile.source.language})</dd>
                        </div>
                      )}
                    </dl>
                  </div>
                </div>
              ) : (
                <EmptyState
                  icon={<Play size={48} strokeWidth={1.5} />}
                  title="No file selected"
                  description="Select a file to preview"
                  variant="compact"
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
