import dynamic from 'next/dynamic';

const Reader = dynamic(() => import('../components/Reader'), { ssr: false });

export default function Page() {
  return <Reader />;
}
