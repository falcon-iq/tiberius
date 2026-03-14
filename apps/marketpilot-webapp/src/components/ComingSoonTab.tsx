interface ComingSoonTabProps {
  title: string;
  subtitle: string;
  description: string;
  features: { icon: React.ReactNode; title: string; description: string }[];
  accentColor: string;
  accentColorRgb: string;
}

export function ComingSoonTab({ title, subtitle, description, features, accentColor, accentColorRgb }: ComingSoonTabProps) {
  return (
    <div style={{ animation: 'fadeSlideIn 0.3s ease-out' }}>
      {/* Coming Soon badge */}
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <span
          style={{
            display: 'inline-block',
            padding: '6px 16px',
            borderRadius: 20,
            background: `rgba(${accentColorRgb}, 0.1)`,
            border: `1px solid rgba(${accentColorRgb}, 0.25)`,
            color: accentColor,
            fontSize: 12,
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: 20,
          }}
        >
          Coming Soon
        </span>
        <h2
          style={{
            fontSize: 28,
            fontWeight: 800,
            color: '#f4f4f5',
            marginBottom: 8,
            letterSpacing: '-0.02em',
          }}
        >
          {title}
        </h2>
        <p style={{ fontSize: 15, color: '#71717a', maxWidth: 480, margin: '0 auto', lineHeight: 1.7 }}>
          {subtitle}
        </p>
      </div>

      {/* Description card */}
      <div
        style={{
          background: 'rgba(24, 24, 32, 0.8)',
          border: '1px solid rgba(63, 63, 70, 0.5)',
          borderRadius: 16,
          padding: 32,
          marginBottom: 24,
          backdropFilter: 'blur(12px)',
        }}
      >
        <p style={{ fontSize: 14, color: '#a1a1aa', lineHeight: 1.8 }}>
          {description}
        </p>
      </div>

      {/* Feature cards */}
      <div style={{ display: 'grid', gap: 16 }}>
        {features.map((feature, i) => (
          <div
            key={i}
            style={{
              background: 'rgba(24, 24, 32, 0.6)',
              border: '1px solid rgba(63, 63, 70, 0.4)',
              borderRadius: 14,
              padding: 24,
              display: 'flex',
              gap: 16,
              alignItems: 'flex-start',
              backdropFilter: 'blur(8px)',
              transition: 'border-color 0.3s, transform 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = `rgba(${accentColorRgb}, 0.3)`;
              e.currentTarget.style.transform = 'translateY(-1px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'rgba(63, 63, 70, 0.4)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 10,
                background: `rgba(${accentColorRgb}, 0.12)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
              }}
            >
              {feature.icon}
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#e4e4e7', marginBottom: 4 }}>
                {feature.title}
              </div>
              <div style={{ fontSize: 13, color: '#71717a', lineHeight: 1.6 }}>
                {feature.description}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
