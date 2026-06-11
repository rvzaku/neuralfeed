"use client";

import { Component, type ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

interface Props { children: ReactNode }
interface State { hasError: boolean }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center py-20 gap-3 text-center px-4">
          <AlertTriangle className="h-8 w-8 text-destructive" />
          <p className="text-sm font-medium">Something went wrong.</p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="text-sm text-primary hover:underline"
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
