import { Sparkles } from "lucide-react"

const AgentSidebar = () => {
  return (
    <aside className="flex w-80 flex-col border-l border-border bg-card">
      {/* Header */}
      <div className="flex h-16 items-center gap-2 border-b border-border px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
          <Sparkles className="h-4 w-4 text-primary" />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-foreground">AI Buddy</h2>
          <p className="text-xs text-muted-foreground">Your helpful assistant</p>
        </div>
      </div>

      {/* Feed Content */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {/* Sample Feed Item */}
          <div className="rounded-lg border border-border bg-background p-4">
            <div className="mb-2 flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-primary" />
              <span className="text-xs font-medium text-muted-foreground">Insight</span>
            </div>
            <p className="text-sm text-foreground">AI-powered insights and suggestions will appear here.</p>
          </div>

          <div className="rounded-lg border border-border bg-background p-4">
            <div className="mb-2 flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-accent" />
              <span className="text-xs font-medium text-muted-foreground">Action</span>
            </div>
            <p className="text-sm text-foreground">Suggested actions and quick notes will be displayed here.</p>
          </div>
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-border p-4">
        <div className="flex items-center gap-2 rounded-lg border border-input bg-background px-3 py-2">
          <input
            type="text"
            placeholder="Ask your buddy..."
            className="flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
          />
          <Sparkles className="h-4 w-4 text-muted-foreground" />
        </div>
      </div>
    </aside>
  )
}

export default AgentSidebar;