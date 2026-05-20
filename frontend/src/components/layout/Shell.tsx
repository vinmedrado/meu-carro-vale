import { AppShell } from '../../design-system/components/AppShell';

export function Shell({ children, onLogout }: { children: React.ReactNode; onLogout: () => void }) {
  return <AppShell onLogout={onLogout}>{children}</AppShell>;
}
