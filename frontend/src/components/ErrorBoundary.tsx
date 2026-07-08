import { Component, type ErrorInfo, type ReactNode } from "react";

// Isolates render crashes to a fallback so one bad payload (e.g. an unexpected
// now-playing field) can't blank the whole app. Wrap dynamic, data-driven
// subtrees. The fallback shows the error and a Retry that clears the state so
// the next poll re-renders.
interface Props {
  children: ReactNode;
  label?: string;
}
interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("UI error boundary caught:", error, info);
  }

  render(): ReactNode {
    if (this.state.error) {
      return (
        <div className="err-boundary">
          <div className="err-title">{this.props.label ?? "Something went wrong"}</div>
          <div className="err-msg">{this.state.error.message}</div>
          <button className="btn" onClick={() => this.setState({ error: null })}>
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
