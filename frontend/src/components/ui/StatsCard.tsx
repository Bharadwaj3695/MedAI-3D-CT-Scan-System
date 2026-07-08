import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface StatsCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  value: string | number;
  icon: React.ComponentType<any> | React.ReactNode;
  description?: string;
  iconClassName?: string;
  iconBgClassName?: string;
}

export function StatsCard({
  title,
  value,
  icon,
  description,
  className,
  iconClassName,
  iconBgClassName,
  ...props
}: StatsCardProps) {
  const renderIcon = () => {
    if (!icon) return null;
    if (React.isValidElement(icon)) {
      return icon;
    }
    const IconComponent = icon as any;
    return <IconComponent className={cn("w-6 h-6", iconClassName)} />;
  };

  return (
    <Card className={cn("glass-card overflow-hidden relative", className)} {...props}>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground font-medium">{title}</p>
            <p className="text-3xl font-display font-bold tracking-tight mt-1">{value}</p>
            {description && (
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            )}
          </div>
          <div
            className={cn(
              "w-12 h-12 rounded-xl flex items-center justify-center bg-primary/5 text-primary shrink-0 ml-4",
              iconBgClassName
            )}
          >
            {renderIcon()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
