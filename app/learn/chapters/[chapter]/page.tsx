'use client';

import dynamic from 'next/dynamic';
import { useParams, useRouter } from 'next/navigation';
import React from 'react';

const ChapterMap: Record<string, React.ComponentType<any>> = {
  chap1: dynamic(() => import('@/addons/chap1'), { ssr: false }),
  chap2: dynamic(() => import('@/addons/chap2'), { ssr: false }),
  chap3: dynamic(() => import('@/addons/chap3'), { ssr: false }),
  chap4: dynamic(() => import('@/addons/chap4'), { ssr: false }),
};

export default function ChapterPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params as any)?.chapter as string;
  const Chapter = ChapterMap[slug];

  if (!Chapter) {
    return (
      <div className="p-6">
        <p className="text-slate-400">Chapter not found.</p>
        <button onClick={() => router.push('/learn')} className="mt-3 px-4 py-2 bg-blue-600 rounded text-white">
          Back to Learn
        </button>
      </div>
    );
  }

  return <Chapter />;
}

