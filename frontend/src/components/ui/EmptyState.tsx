import * as React from "react";
import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  icon?: React.ComponentType<any> | React.ReactNode;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  actionHref,
  icon,
  className,
  ...props
}: EmptyStateProps) {
  const renderIcon = () => {
    if (!icon) return null;
    if (React.isValidElement(icon)) {
      return <div className="mx-auto mb-4">{icon}</div>;
    }
    const IconComponent = icon as any;
    return <IconComponent className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />;
  };

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center p-8 border border-dashed rounded-xl bg-card/50 backdrop-blur-sm py-12",
        className
      )}
      {...props}
    >
      {renderIcon()}
      <h3 className="text-lg font-semibold tracking-tight mb-1">{title}</h3>
      <p className="text-sm text-muted-foreground max-w-sm mb-6">{description}</p>
      {actionLabel && actionHref && (
        <Button asChild size="sm">
          <Link to={actionHref}>{actionLabel}</Link>
        </Button>
      )}
    </div>
  );
}
