import { Link } from '@tanstack/react-router';

const BASE =
  'px-6 py-2.5 rounded-full text-[14px] font-semibold cursor-pointer transition-all border-2 bg-white text-[#555] border-[#e0e0e0]';
const ACTIVE =
  'px-6 py-2.5 rounded-full text-[14px] font-semibold cursor-pointer transition-all border-2 bg-[#4a6cf7] text-white border-[#4a6cf7]';

const tabs = [
  { to: '/' as const, label: 'Websites', exact: true },
  { to: '/benchmark' as const, label: 'Benchmark', exact: false },
  { to: '/reports' as const, label: 'Reports', exact: false },
];

export function TopNav() {
  return (
    <nav className="flex gap-2 justify-center mb-6 flex-wrap">
      {tabs.map((tab) => (
        <Link
          key={tab.to}
          to={tab.to}
          activeOptions={tab.exact ? { exact: true } : {}}
          className={BASE}
          activeProps={{ className: ACTIVE }}
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  );
}
