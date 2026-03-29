import { cn } from "@/lib/utils";

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-2xl bg-zinc-800/80 ring-1 ring-white/5",
        className
      )}
      {...props}
    />
  );
}

export { Skeleton };
