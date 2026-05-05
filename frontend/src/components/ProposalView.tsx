import { useState } from 'react';
import type { ProposedMove } from '../services/sortApi';

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
