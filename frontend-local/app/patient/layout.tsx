/**
 * Dashboard-v3 Layout
 *
 * This layout overrides the parent /patient/layout.tsx to remove the
 * duplicate header. Dashboard-v3 has its own complete Header component
 * with theme toggle, so we bypass the parent's header entirely.
 */

export default function DashboardV3Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Render children directly without the parent's header wrapper
  // The dashboard-v3/page.tsx already includes its own Header component
  return <>{children}</>;
}
