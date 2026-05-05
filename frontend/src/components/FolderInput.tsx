import { useEffect, useState } from 'react';
import type { OllamaModel } from '../services/sortApi';
import { listModels } from '../services/sortApi';

interface Props {
  onAnalyze: (folderPath: string, includeContent: boolean, recursive: boolean, model: string) => void;
  loading: boolean;
}

// File System Access API — available in Chromium-based browsers
declare global {
  interface Window {
    showDirectoryPicker?: () => Promise<{ name: string }>;
  }
}

export default function FolderInput({ onAnalyze, loading }: Props) {
  const [folderPath, setFolderPath] = useState('');
  const [includeContent, setIncludeContent] = useState(false);
  const [recursive, setRecursive] = useState(false);
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [pickerSupported] = useState(() => typeof window.showDirectoryPicker === 'function');

  useEffect(() => {
    listModels()
      .then((m) => {
        setModels(m);
        if (m.length > 0) setSelectedModel(m[0].name);
      })
      .catch(() => {/* backend may not be up yet */});
  }, []);

  async function handlePickFolder() {
    if (!window.showDirectoryPicker) return;
    try {
      const handle = await window.showDirectoryPicker();
      // The API returns the folder name, not the full path.
      // We set the name as a hint and let the user confirm/edit.
      setFolderPath(handle.name);
    } catch {
      // User cancelled — do nothing
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = folderPath.trim();
    if (trimmed) onAnalyze(trimmed, includeContent, recursive, selectedModel);
  }

  return (
    <form className="folder-input" onSubmit={handleSubmit}>
      <h2 className="folder-input__title">AI File Sorter</h2>
      <p className="folder-input__subtitle">
        Enter a folder path and the AI will propose how to organize its files.
      </p>

      <label className="folder-input__label" htmlFor="folder-path">
        Folder path
      </label>
      <div className="folder-input__path-row">
        <input
          id="folder-path"
          className="folder-input__field"
          type="text"
          placeholder="/Users/you/Downloads"
          value={folderPath}
          onChange={(e) => setFolderPath(e.target.value)}
          disabled={loading}
          autoComplete="off"
          spellCheck={false}
        />
        {pickerSupported && (
          <button
            type="button"
            className="btn btn--secondary folder-input__pick-btn"
            onClick={handlePickFolder}
            disabled={loading}
            title="Browse for folder"
          >
            Browse
          </button>
        )}
      </div>

      {models.length > 0 && (
        <>
          <label className="folder-input__label" htmlFor="model-select">
            Model
          </label>
          <select
            id="model-select"
            className="folder-input__select"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            disabled={loading}
          >
            {models.map((m) => (
              <option key={m.name} value={m.name}>
                {m.name}
                {m.size ? ` — ${(m.size / 1e9).toFixed(1)} GB` : ''}
              </option>
            ))}
          </select>
        </>
      )}

      <div className="folder-input__toggles">
        <label className="folder-input__content-toggle">
          <input
            type="checkbox"
            checked={includeContent}
            onChange={(e) => setIncludeContent(e.target.checked)}
            disabled={loading}
          />
          Read file contents (text files only, smarter suggestions)
        </label>
        <label className="folder-input__content-toggle">
          <input
            type="checkbox"
            checked={recursive}
            onChange={(e) => setRecursive(e.target.checked)}
            disabled={loading}
          />
          Scan sub-folders recursively
        </label>
      </div>

      <button
        className="btn btn--primary"
        type="submit"
        disabled={loading || !folderPath.trim()}
      >
        {loading ? 'Analyzing…' : 'Analyze Folder'}
      </button>
    </form>
  );
}

