import { AppShell } from '../../design-system/components/AppShell';

export function Shell({ children, onLogout, showAdminTools = false }: { children: React.ReactNode; onLogout: () => void; showAdminTools?: boolean }) {
  return <AppShell onLogout={onLogout} showAdminTools={showAdminTools}>{children}</AppShell>;
}
