import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

type AppShellProps = {
  children: React.ReactNode;
};

export default function AppShell({
  children,
}: AppShellProps) {
  return (
    <div className="app-shell">
      <Sidebar />

      <main className="main-content">
        <Topbar />

        {children}
      </main>
    </div>
  );
}