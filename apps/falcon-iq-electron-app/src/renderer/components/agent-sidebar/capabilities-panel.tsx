import { ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import type { Capability } from '../../types/electron';

interface CapabilitiesPanelProps {
  capabilities: Capability[];
  onSelectExample: (example: string) => void;
  collapsed?: boolean;
}

export function CapabilitiesPanel({
  capabilities,
  onSelectExample,
  collapsed = false,
}: CapabilitiesPanelProps) {
  const [isExpanded, setIsExpanded] = useState(!collapsed);

  if (capabilities.length === 0) {
    return null;
  }

  return (
    <div className="border-t border-border">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-muted/50 transition-colors"
      >
        <span className="text-sm font-medium">Quick Actions</span>
        {isExpanded ? (
          <ChevronUp className="w-4 h-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        )}
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-4 max-h-[300px] overflow-y-auto">
          {capabilities.map((capability, idx) => (
            <div key={idx} className="space-y-2">
              <div className="space-y-1">
                <h4 className="text-sm font-semibold">{capability.name}</h4>
                <p className="text-xs text-muted-foreground">
                  {capability.description}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {capability.examples.map((example: string, exampleIdx: number) => (
                  <button
                    key={exampleIdx}
                    onClick={() => onSelectExample(example)}
                    className="bg-muted hover:bg-muted/80 text-sm px-3 py-1.5 rounded-lg transition-colors text-left"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
