import Link from "next/link";
import type { ReactNode } from "react";

function BrandMark() {
  return (
    <div
      className="sidebar-logo"
      aria-label="TraceLedger"
    >
      TL
    </div>
  );
}

function Icon({
  children,
}: {
  children: ReactNode;
}) {
  return <span aria-hidden="true">{children}</span>;
}

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <BrandMark />

        <div className="sidebar-brand-name">
          TraceLedger
        </div>
      </div>

      <nav className="sidebar-nav">
        <Link
          href="/"
          className="sidebar-nav-item active"
        >
          <Icon>⌂</Icon>
          <span>Dashboard</span>
        </Link>

        <Link
          href="/"
          className="sidebar-nav-item"
        >
          <Icon>◈</Icon>
          <span>Investigations</span>
        </Link>

        <Link
          href="/"
          className="sidebar-nav-item"
        >
          <Icon>＋</Icon>
          <span>New Investigation</span>
        </Link>

        <Link
          href="/"
          className="sidebar-nav-item"
        >
          <Icon>◇</Icon>
          <span>Evidence</span>
        </Link>

        <Link
          href="/"
          className="sidebar-nav-item"
        >
          <Icon>⌁</Icon>
          <span>Evaluation</span>
        </Link>
      </nav>

      <nav className="sidebar-nav">
        <Link
          href="/"
          className="sidebar-nav-item"
        >
          <Icon>⚙</Icon>
          <span>Settings</span>
        </Link>
      </nav>

      <div className="sidebar-footer">
        <div>Personal Workspace</div>
        <div>Local development</div>
      </div>
    </aside>
  );
}