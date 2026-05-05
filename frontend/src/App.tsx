import { useState } from 'react';
import './App.css';
import FolderInput from './components/FolderInput';
import ProposalView from './components/ProposalView';
import ResultView from './components/ResultView';
import {
  analyzeFolder,
  executeSort,
  type ExecuteResult,
  type ProposedMove,
  type SortProposal,
} from './services/sortApi';

type Step = 'input' | 'proposal' | 'result';

function App() {
  const [step, setStep] = useState<Step>('input');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [folderPath, setFolderPath] = useState('');
  const [proposal, setProposal] = useState<SortProposal | null>(null);
  const [result, setResult] = useState<ExecuteResult | null>(null);

  async function handleAnalyze(path: string, includeContent: boolean) {
    setError(null);
    setLoading(true);
    setFolderPath(path);
    try {
      const data = await analyzeFolder(path, includeContent);
      setProposal(data);
      setStep('proposal');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze folder');
    } finally {
      setLoading(false);
    }
  }

  async function handleExecute(moves: ProposedMove[]) {
    setError(null);
    setLoading(true);
    try {
      const data = await executeSort(folderPath, moves);
      setResult(data);
      setStep('result');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute moves');
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setStep('input');
    setProposal(null);
    setResult(null);
    setError(null);
    setFolderPath('');
  }

  return (
    <div className="app">
      <main className="app__main">
        {error && (
          <div className="app__error" role="alert">
            {error}
            <button className="app__error-dismiss" onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {step === 'input' && (
          <FolderInput onAnalyze={handleAnalyze} loading={loading} />
        )}

        {step === 'proposal' && proposal && (
          <ProposalView
            moves={proposal.moves}
            onExecute={handleExecute}
            onReset={handleReset}
            loading={loading}
          />
        )}

        {step === 'result' && result && (
          <ResultView result={result} onReset={handleReset} />
        )}
      </main>
    </div>
  );
}

export default App;
