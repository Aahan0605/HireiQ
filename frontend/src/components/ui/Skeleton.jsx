import React from 'react';

export default function Skeleton({ className, ...props }) {
  return (
    <div
      className={`animate-pulse rounded-xl bg-surface-3 border border-white/5 shadow-inner ${className}`}
      {...props}
    />
  );
}

export function CandidateCardSkeleton() {
  return (
    <div className="rounded-2xl border border-white/10 bg-surface-2 p-6 space-y-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Skeleton className="h-12 w-12 rounded-xl" />
          <div className="space-y-2">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-4 w-20" />
          </div>
        </div>
        <Skeleton className="h-8 w-14 rounded-lg" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
      </div>
      <div className="flex gap-2 pt-2">
        <Skeleton className="h-6 w-16" />
        <Skeleton className="h-6 w-20" />
        <Skeleton className="h-6 w-12" />
      </div>
    </div>
  );
}

export function TableRowSkeleton() {
  return (
    <tr className="border-b border-white/5">
      <td className="p-4"><Skeleton className="h-5 w-24" /></td>
      <td className="p-4"><Skeleton className="h-5 w-32" /></td>
      <td className="p-4"><Skeleton className="h-5 w-16" /></td>
      <td className="p-4"><Skeleton className="h-5 w-20" /></td>
      <td className="p-4"><Skeleton className="h-8 w-16 rounded-lg" /></td>
      <td className="p-4"><Skeleton className="h-8 w-24 rounded-lg" /></td>
    </tr>
  );
}
