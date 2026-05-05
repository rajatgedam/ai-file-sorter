import type { ExecuteResult } from '../services/sortApi';

interface Props {
  result: ExecuteResult;
  onReset: () => void;
  onUndo: (sessionId: string) => void;
  undoing: boolean;
}

export default function ResultView({ result, onReset, onUndo, undoing }: Props) {
  const { moved, skipped, errors, session_id } = result;

  return (
    <div className="result-view">
      <h2 className="result-view__title">Done</h2>

      <div className="result-view__stats">
        <div className="result-stat result-stat--moved">
          <span className="result-stat__count">{moved.length}</span>
          <span className="result-stat__label">Moved</span>
        </div>
        <div className="result-stat result-stat--skipped">
          <span className="result-stat__count">{skipped.length}</span>
          <span className="result-stat__label">Skipped</span>
        </div>
        <div className="result-stat result-stat--errors">
          <span className="result-stat__count">{errors.length}</span>
          <span className="result-stat__label">Errors</span>
        </div>
      </div>

      {moved.length > 0 && (
        <details className="result-view__detail">
          <summary>Moved files ({moved.length})</summary>
          <ul className="result-view__file-list">
            {moved.map((f) => (
              <li key={f}>{f.split('/').pop()}</li>
            ))}
          </ul>
        </details>
      )}

      {skipped.length > 0 && (
        <details className="result-view__detail">
          <summary>Skipped files ({skipped.length})</summary>
          <ul className="result-view__file-list">
            {skipped.map((f) => (
              <li key={f}>{f.split('/').pop()}</li>
            ))}
          </ul>
        </details>
      )}

      {errors.length > 0 && (
        <details className="result-view__detail result-view__detail--error" open>
          <summary>Errors ({errors.length})</summary>
          <ul className="result-view__file-list result-view__file-list--error">
            {errors.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </details>
      )}

      <div className="result-view__actions">
        {session_id && moved.length > 0 && (
          <button
            className="btn btn--secondary"
            onClick={() => onUndo(session_id)}
            disabled={undoing}
          >
            {undoing ? 'Undoing…' : '↩ Undo moves'}
          </button>
        )}
        <button className="btn btn--primary" onClick={onReset} disabled={undoing}>
          Sort another folder
        </button>
      </div>
    </div>
  );
}


  return (
    <div className="result-view">
      <h2 className="result-view__title">Done</h2>

      <div className="result-view__stats">
        <div className="result-stat result-stat--moved">
          <span className="result-stat__count">{moved.length}</span>
          <span className="result-stat__label">Moved</span>
        </div>
        <div className="result-stat result-stat--skipped">
          <span className="result-stat__count">{skipped.length}</span>
          <span className="result-stat__label">Skipped</span>
        </div>
        <div className="result-stat result-stat--errors">
          <span className="result-stat__count">{errors.length}</span>
          <span className="result-stat__label">Errors</span>
        </div>
      </div>

      {moved.length > 0 && (
        <details className="result-view__detail">
          <summary>Moved files ({moved.length})</summary>
          <ul className="result-view__file-list">
            {moved.map((f) => (
              <li key={f}>{f.split('/').pop()}</li>
            ))}
          </ul>
        </details>
      )}

      {skipped.length > 0 && (
        <details className="result-view__detail">
          <summary>Skipped files ({skipped.length})</summary>
          <ul className="result-view__file-list">
            {skipped.map((f) => (
              <li key={f}>{f.split('/').pop()}</li>
            ))}
          </ul>
        </details>
      )}

      {errors.length > 0 && (
        <details className="result-view__detail result-view__detail--error" open>
          <summary>Errors ({errors.length})</summary>
          <ul className="result-view__file-list result-view__file-list--error">
            {errors.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </details>
      )}

      <button className="btn btn--primary" onClick={onReset}>
        Sort another folder
      </button>
    </div>
  );
}
