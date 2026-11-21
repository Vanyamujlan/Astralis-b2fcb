import {Component, type ErrorInfo, type ReactNode} from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  message: string;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = {hasError: false, message: ''};

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      message: error.message || 'Unexpected application error.',
    };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Astralio ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-slate-950 p-6 text-slate-100">
          <div className="max-w-lg rounded-2xl border border-rose-500/30 bg-slate-900 p-6">
            <h1 className="text-lg font-semibold text-white">Произошла ошибка приложения</h1>
            <p className="mt-2 text-sm text-slate-300">
              Проверьте подключение к Firebase или обновите страницу.
            </p>
            <pre className="mt-4 max-h-48 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-rose-300">
              {this.state.message}
            </pre>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-4 rounded-lg bg-indigo-500 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-400"
            >
              Обновить страницу
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
