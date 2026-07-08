import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type StatusType = "completed" | "processing" | "pending" | "failed";

export interface StatusBadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  status: StatusType | string;
}

export function StatusBadge({ status, className, ...props }: StatusBadgeProps) {
  const getStatusClass = (statusStr: string) => {
    switch (statusStr.toLowerCase()) {
      case "completed":
        return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/30 border-transparent";
      case "processing":
        return "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/30 border-transparent";
      case "pending":
        return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400 hover:bg-yellow-100 dark:hover:bg-yellow-900/30 border-transparent";
      case "failed":
        return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30 border-transparent";
      default:
        return "bg-muted text-muted-foreground hover:bg-muted border-transparent";
    }
  };

  return (
    <Badge
      className={cn("font-medium capitalize px-2.5 py-1 text-xs rounded-full", getStatusClass(status), className)}
      {...props}
    >
      {status}
    </Badge>
  );
}
