import type { ReactNode } from "react";

interface HeaderProps {
  title: ReactNode;
  description?: string;
}

export function Header({ title, description }: HeaderProps) {
  return (
    <div className="border-b bg-card px-6 py-4">
      <h2 className="text-xl font-semibold">{title}</h2>
      {description && (
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      )}
    </div>
  );
}
