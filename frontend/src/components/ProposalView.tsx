import { useMemo, useState } from 'react';
import type { ProposedMove } from '../services/sortApi';

interface Props {
  moves: ProposedMove[];
  onExecute: (moves: ProposedMove[]) => void;
  onReset: () => void;
  loading: boolean;
}

function getFolderLabel(destination: string, source: string): string {
  const srcDir = source.substring(0, source.lastIndexOf('/') + 1);
  const destDir = destination.substring(0, destination.lastIndexOf('/') + 1);
  return destDir.startsWith(srcDir) ? destDir.slice(srcDir.length).replace(/\/$/, '') : destDir;
}

export default function ProposalView({ moves, onExecute, onReset, loading }: Props) {
  const [localMoves, setLocalMoves] = useState<ProposedMove[]>(moves);
  const [collapsedFolders, setCollapsedFolders] = useState<Set<string>>(new Set());

  function toggleApproval(index: number) {
    setLocalMoves((prev) =>
      prev.map((m, i) => (i === index ? { ...m, approved: !m.approved } : m))
    );
  }

  function toggleAll(approved: boolean) {
    setLocalMoves((prev) => prev.map((m) => ({ ...m, approved })));
  }

  function toggleFolder(folder: string, approved: boolean) {
    setLocalMoves((prev) =>
      prev.map((m) =>
        getFolderLabel(m.destination, m.source) === folder ? { ...m, approved } : m
      )
    );
  }

  function toggleCollapse(folder: string) {
    setCollapsedFolders((prev) => {
      const next = new Set(prev);
      next.has(folder) ? next.delete(folder) : next.add(folder);
      return next;
    });
  }

  // Group moves by destination folder
  const grouped = useMemo(() => {
    const map = new Map<string, { move: ProposedMove; index: number }[]>();
    localMoves.forEach((move, index) => {
      const folder = getFolderLabel(move.destination, move.source);
      if (!map.has(folder)) map.set(folder, []);
      map.get(folder)!.push({ move, index });
    });
    return map;
  }, [localMoves]);

  const approvedCount = localMoves.filter((m) => m.approved).length;

  return (
    <div className="proposal-view">
      <div className="proposal-view__header">
        <div>
          <h2 className="proposal-view__title">Proposed Changes</h2>
          <p className="proposal-view__meta">
            {approvedCount} of {localMoves.length} moves approved
          </p>
        </div>
        <div className="proposal-view__bulk">
          <button className="btn btn--ghost" onClick={() => toggleAll(true)} disabled={loading}>
            Select all
          </button>
          <button className="btn btn--ghost" onClick={() => toggleAll(false)} disabled={loading}>
            Deselect all
          </button>
        </div>
      </div>

      {localMoves.length === 0 ? (
        <p className="proposal-view__empty">No files found in this folder.</p>
      ) : (
        <div className="proposal-tree">
          {Array.from(grouped.entries()).map(([folder, items]) => {
            const allApproved = items.every((i) => i.move.approved);
            const someApproved = items.some((i) => i.move.approved);
            const collapsed = collapsedFolders.has(folder);

            return (
              <div key={folder} className="proposal-tree__group">
                <div className="proposal-tree__folder">
                  <button
                    className="proposal-tree__collapse-btn"
                    onClick={() => toggleCollapse(folder)}
                    title={collapsed ? 'Expand' : 'Collapse'}
                    type="button"
                  >
                    {collapsed ? '▶' : '▼'}
                  </button>
                  <input
                    type="checkbox"
                    className="proposal-tree__folder-check"
                    checked={allApproved}
                    ref={(el) => { if (el) el.indeterminate = !allApproved && someApproved; }}
                    onChange={(e) => toggleFolder(folder, e.target.checked)}
                    disabled={loading}
                  />
                  <span className="proposal-tree__folder-name">📁 {folder}/</span>
                  <span className="proposal-tree__folder-count">{items.length} file{items.length !== 1 ? 's' : ''}</span>
                </div>

                {!collapsed && (
                  <ul className="proposal-tree__files">
                    {items.map(({ move, index }) => (
                      <li
                        key={move.source}
                        className={`proposal-item ${move.approved ? 'proposal-item--approved' : 'proposal-item--skipped'}`}
                      >
                        <label className="proposal-item__check">
                          <input
                            type="checkbox"
                            checked={move.approved}
                            onChange={() => toggleApproval(index)}
                            disabled={loading}
                          />
                        </label>
                        <div className="proposal-item__details">
                          <span className="proposal-item__filename">
                            {move.source.split('/').pop()}
                          </span>
                          <span className="proposal-item__reason">{move.reason}</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="proposal-view__actions">
        <button className="btn btn--secondary" onClick={onReset} disabled={loading}>
          ← Back
        </button>
        <button
          className="btn btn--primary"
          onClick={() => onExecute(localMoves)}
          disabled={loading || approvedCount === 0}
        >
          {loading ? 'Moving files…' : `Execute ${approvedCount} move${approvedCount !== 1 ? 's' : ''}`}
        </button>
      </div>
    </div>
  );
}


interface Props {
  moves: ProposedMove[];
  onExecute: (moves: ProposedMove[]) => void;
  onReset: () => void;
  loading: boolean;
}

export default function ProposalView({ moves, onExecute, onReset, loading }: Props) {
  const [localMoves, setLocalMoves] = useState<ProposedMove[]>(moves);

  function toggleApproval(index: number) {
    setLocalMoves((prev) =>
      prev.map((m, i) => (i === index ? { ...m, approved: !m.approved } : m))
    );
  }

  function toggleAll(approved: boolean) {
    setLocalMoves((prev) => prev.map((m) => ({ ...m, approved })));
  }

  const approvedCount = localMoves.filter((m) => m.approved).length;

  function relativeDest(source: string, destination: string): string {
    const srcDir = source.substring(0, source.lastIndexOf('/') + 1);
    return destination.startsWith(srcDir)
      ? destination.slice(srcDir.length)
      : destination;
  }

  return (
    <div className="proposal-view">
      <div className="proposal-view__header">
        <div>
          <h2 className="proposal-view__title">Proposed Changes</h2>
          <p className="proposal-view__meta">
            {approvedCount} of {localMoves.length} moves approved
          </p>
        </div>
        <div className="proposal-view__bulk">
          <button className="btn btn--ghost" onClick={() => toggleAll(true)} disabled={loading}>
            Select all
          </button>
          <button className="btn btn--ghost" onClick={() => toggleAll(false)} disabled={loading}>
            Deselect all
          </button>
        </div>
      </div>

      {localMoves.length === 0 ? (
        <p className="proposal-view__empty">No files found in this folder.</p>
      ) : (
        <ul className="proposal-view__list">
          {localMoves.map((move, i) => (
            <li
              key={move.source}
              className={`proposal-item ${move.approved ? 'proposal-item--approved' : 'proposal-item--skipped'}`}
            >
              <label className="proposal-item__check">
                <input
                  type="checkbox"
                  checked={move.approved}
                  onChange={() => toggleApproval(i)}
                  disabled={loading}
                />
              </label>
              <div className="proposal-item__details">
                <span className="proposal-item__filename">
                  {move.source.split('/').pop()}
                </span>
                <span className="proposal-item__arrow">→</span>
                <span className="proposal-item__destination">
                  {relativeDest(move.source, move.destination)}
                </span>
                <span className="proposal-item__reason">{move.reason}</span>
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="proposal-view__actions">
        <button className="btn btn--secondary" onClick={onReset} disabled={loading}>
          ← Back
        </button>
        <button
          className="btn btn--primary"
          onClick={() => onExecute(localMoves)}
          disabled={loading || approvedCount === 0}
        >
          {loading ? 'Moving files…' : `Execute ${approvedCount} move${approvedCount !== 1 ? 's' : ''}`}
        </button>
      </div>
    </div>
  );
}
