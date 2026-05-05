import { useState } from 'react';

interface Props {
  onAnalyze: (folderPath: string, includeContent: boolean) => void;
  loading: boolean;
}

export default function FolderInput({ onAnalyze, loading }: Props) {
  const [folderPath, setFolderPath] = useState('');
  const [includeContent, setIncludeContent] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = folderPath.trim();
    if (trimmed) onAnalyze(trimmed, includeContent);
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

      <label className="folder-input__content-toggle">
        <input
          type="checkbox"
          checked={includeContent}
          onChange={(e) => setIncludeContent(e.target.checked)}
          disabled={loading}
        />
        Read file contents for smarter suggestions (text files only)
      </label>

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
