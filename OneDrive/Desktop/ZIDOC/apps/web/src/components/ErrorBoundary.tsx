import { Component } from "react"
import type { ErrorInfo, ReactNode } from "react"
import { AlertTriangle, RotateCcw } from "lucide-react"

interface Props {
  children?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
    window.location.href = "/"
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background px-4 text-center">
          <div className="max-w-md w-full glass border border-red-500/20 p-8 rounded-2xl space-y-6">
            <div className="flex justify-center">
              <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-4">
                <AlertTriangle className="h-12 w-12 text-red-500" />
              </div>
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-bold text-white">Application Exception</h2>
              <p className="text-sm text-muted-foreground">
                An unexpected crash occurred in the frontend component tree. The error has been captured.
              </p>
              {this.state.error && (
                <div className="mt-2 rounded-lg bg-black/40 border border-white/5 p-3 text-left">
                  <p className="font-mono text-xs text-red-400 overflow-x-auto whitespace-pre-wrap">
                    {this.state.error.toString()}
                  </p>
                </div>
              )}
            </div>
            <div className="pt-2">
              <button
                onClick={this.handleReset}
                className="inline-flex h-10 items-center justify-center rounded-md bg-red-600 px-6 text-sm font-medium text-white shadow hover:bg-red-500 transition-all gap-2 w-full"
              >
                <RotateCcw className="h-4 w-4" /> Reload Workspace
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
