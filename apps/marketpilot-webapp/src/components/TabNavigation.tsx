import { useState, type ReactNode } from 'react';

export interface Tab {
  id: string;
  label: string;
  icon: ReactNode;
  content: ReactNode;
}

interface TabNavigationProps {
  tabs: Tab[];
  defaultTab?: string;
}

export function TabNavigation({ tabs, defaultTab }: TabNavigationProps) {
  const [activeTab, setActiveTab] = useState(defaultTab ?? tabs[0]?.id ?? '');

  const activeContent = tabs.find((t) => t.id === activeTab)?.content;

  return (
    <div>
      <style>{`
        .tab-bar {
          display: flex;
          gap: 6px;
          padding: 6px;
          background: rgba(24, 24, 32, 0.6);
          border: 1px solid rgba(63, 63, 70, 0.4);
          border-radius: 14px;
          margin-bottom: 32px;
          backdrop-filter: blur(12px);
          overflow-x: auto;
          -webkit-overflow-scrolling: touch;
          scrollbar-width: none;
        }
        .tab-bar::-webkit-scrollbar { display: none; }
        .tab-btn {
          flex: 1;
          min-width: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          padding: 12px 12px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          border: none;
          border-radius: 10px;
          font-size: 13px;
          cursor: pointer;
          font-family: inherit;
          transition: all 0.25s ease;
          position: relative;
          letter-spacing: 0.01em;
        }
        .tab-label {
          display: inline;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        /* Desktop wide: more padding */
        @media (min-width: 1100px) {
          .tab-btn { padding: 12px 20px; font-size: 14px; }
        }
        /* Below 640px: icon-only tabs */
        @media (max-width: 640px) {
          .tab-bar { gap: 4px; padding: 4px; }
          .tab-btn { padding: 12px 16px; gap: 0; flex: 0 0 auto; }
          .tab-label { display: none; }
        }
      `}</style>

      {/* Tab bar */}
      <div className="tab-bar">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              className="tab-btn"
              onClick={() => setActiveTab(tab.id)}
              title={tab.label}
              style={{
                background: isActive
                  ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(168, 85, 247, 0.2))'
                  : 'transparent',
                color: isActive ? '#e0e7ff' : '#71717a',
                fontWeight: isActive ? 700 : 500,
                boxShadow: isActive
                  ? '0 0 20px rgba(99, 102, 241, 0.15), inset 0 1px 0 rgba(255,255,255,0.05)'
                  : 'none',
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.color = '#a1a1aa';
                  e.currentTarget.style.background = 'rgba(63, 63, 70, 0.2)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.color = '#71717a';
                  e.currentTarget.style.background = 'transparent';
                }
              }}
            >
              <span style={{ display: 'flex', alignItems: 'center', width: 16, height: 16, flexShrink: 0 }}>
                {tab.icon}
              </span>
              <span className="tab-label">{tab.label}</span>
              {isActive && (
                <div
                  style={{
                    position: 'absolute',
                    bottom: 0,
                    left: '20%',
                    right: '20%',
                    height: 2,
                    background: 'linear-gradient(90deg, transparent, #6366f1, #a855f7, transparent)',
                    borderRadius: 1,
                  }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div style={{ animation: 'fadeSlideIn 0.3s ease-out' }} key={activeTab}>
        {activeContent}
      </div>
    </div>
  );
}
